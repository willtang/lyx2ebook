
# The contents of this file are subject to the Mozilla Public License
# (MPL) Version 1.1 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License
# at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and
# limitations under the License.
#
# The Original Code is LEPL (http://www.acooke.org/lepl)
# The Initial Developer of the Original Code is Andrew Cooke.
# Portions created by the Initial Developer are Copyright (C) 2009-2010
# Andrew Cooke (andrew@acooke.org). All Rights Reserved.
#
# Alternatively, the contents of this file may be used under the terms
# of the LGPL license (the GNU Lesser General Public License,
# http://www.gnu.org/licenses/lgpl.html), in which case the provisions
# of the LGPL License are applicable instead of those above.
#
# If you wish to allow use of your version of this file only under the
# terms of the LGPL License and not to allow others to use your version
# of this file under the MPL, indicate your decision by deleting the
# provisions above and replace them with the notice and other provisions
# required by the LGPL License.  If you do not delete the provisions
# above, a recipient may use your version of this file under either the
# MPL or the LGPL License.

'''
Filter and transform streams.
'''


from lepl.matchers.core import OperatorMatcher
from lepl.core.parser import tagged
from lepl.stream.stream import Source, LocationStream, DEFAULT_STREAM_FACTORY
from lepl.support.lib import str


class FilterException(Exception):
    '''
    Raised when there are problems with filtering.
    '''
    

class BaseDelegateSource(Source):
    '''
    Support for sources that delegate location to other sources.  The location
    state is a StreamView into the underlying source at the start of the
    current line.
    '''
    
    def location(self, offset, line, location_state):
        '''
        A tuple containing line number, line offset, character offset,
        the line currently being processed, and a description of the source.
        
        location_state is the original stream.
        '''
        if location_state:
            try:
                shifted = location_state[offset:]
                return shifted.location
            except IndexError:
                return (-1, -1, -1, None, None)
        else:
            return (-1, -1, -1, None, None)
        
    def hash_line(self, line):
        '''
        Extract line number from original data.
        '''
        return self.location(0, line, line.location_state)[0]
    
    def eq_line(self, line, other):
        return line.location_state == other.location_state \
            and self == other.source


def list_join(old_join):
    '''
    We're taking a stream and splitting it into single "characters", 
    each of which is then placed in a "line", so we have introduce an
    extra level of lists.
    '''
    def join(list_of_lists):
        '''
        Rewrite join to remove the extra lists.
        '''
        return old_join(x[0] for x in list_of_lists)
    return join
    

# pylint: disable-msg=E1002
# pylint confused by abcs
class BaseTransformedSource(BaseDelegateSource):
    '''
    Support for transformations of `LocationStream` instances.  The location is
    delegated to the underlying stream.
    
    Each item is transformed into a list of new tokens (all associated with 
    the same location).  To completely filter an item, return the empty list.
    
    Note that a transform should take a stream and return an iterator over
    (new_item, old_stream) pairs, where new_item is a transformed item and
    old_stream is the stream whose head corresponds to the new item.  The
    old_stream may "jump" or "repeat" as necessary. 
    '''

    def __init__(self, transform, stream):
        if not isinstance(stream, LocationStream):
            raise FilterException('Can only filter LocationStream instances.')
        # join is unused here, but used by `StreamView`
        super(BaseTransformedSource, self).__init__(str(stream.source),
                                            list_join(stream.source.join))
        self.__length = 0
        self.__iterator = transform(stream)
        
    def __next__(self):
        try:
            (new_item, old_stream) = next(self.__iterator)
            self.__length += 1
            # The extra list is needed because sources return lines
            return ([new_item], old_stream)
        except StopIteration:
            self.total_length = self.__length
            return (None, None)
        

class FilteredSource(BaseTransformedSource):
    '''
    Filter a `LocationStream`.
    
    Predicate should return True/False for each item in turn.
    '''

    def __init__(self, predicate, stream):
        def transform(stream):
            '''
            Create a transform as required by `BaseTransformedSource`.
            '''
            while stream:
                item = stream[0]
                if predicate(item):
                    yield (item, stream)
                stream = stream[1:]
        # join is unused here, but used by `StreamView`
        super(FilteredSource, self).__init__(transform, stream)

    @staticmethod
    def filtered_stream(predicate, stream, factory=DEFAULT_STREAM_FACTORY):
        '''
        Generated a filtered stream.
        '''
        return factory(FilteredSource(predicate, stream))
        

class CachingTransformedSource(BaseDelegateSource):
    '''
    An alternative to `TransformedSource` that allows efficient retrieval of
    the underlying stream at a location corresponding to a position in the
    transformed stream.  Typically used via `Filter`.
    
    This is necessary to avoid O(n^2) time when parsing chunks of data
    with a transformed stream (without the cache, retrieving an offset in 
    our linked-list style streams is O(n)).  However it is expensive in
    terms of memory consumed.
    
    As before a transform should take a stream and return an iterator over
    (new_item, old_stream) pairs, where new_item is a transformed item and
    old_stream is the stream whose head corresponds to the new item.  The
    old_stream may "jump" or "repeat" as necessary. 
    '''

    def __init__(self, transform, stream):
        if not isinstance(stream, LocationStream):
            raise FilterException('Can only filter LocationStream instances.')
        # join is unused here, but used by `StreamView`
        super(CachingTransformedSource, self).__init__(str(stream.source),
                                                list_join(stream.source.join))
        self.__length = 0
        self.__iterator = transform(stream)
        # map from character offset to underlying stream 
        self.__lookup = {}
        self.__previous_stream = stream
    
    def __next__(self):
        '''
        This is the same algorithm as `BaseTranformedSource`, unrolling a
        possibly expanded list of transformed items.  However, it is 
        complicated by the need to cache the result for `locate`.
        
        Ideally, we would like the old_stream to be conservative, in that if 
        an item is generated from the stream at a certain point, but earlier 
        parts of the stream generated no items, then we use the earlier part 
        of the stream.  This approach makes sense with filters because 
        typically a filter is only valid in the region when it is used, and 
        we are checking the stream after the region has finished, so any final 
        discarded items were likely discarded incorrectly.
        
        To make a conservative old_stream, we preserve the *previous* 
        old_stream and move "one on" from that.
        '''
        try:
            (item, old_stream) = next(self.__iterator)
            self.__length += 1
            index = old_stream.character_offset
            if index not in self.__lookup:
                self.__lookup[index] = self.__previous_stream
            self.__previous_stream = old_stream[1:]
            # The extra list is needed because sources return lines
            return ([item], old_stream)
        except StopIteration:
            self.total_length = self.__length
            return (None, None)

    def locate(self, stream):
        '''
        Find the first location in the original stream which, when filtered,
        would match the given stream.
        '''
        if stream.character_offset == -1:
            return self.__previous_stream
        else:
            return self.__lookup[stream.character_offset]


class CachingFilteredSource(CachingTransformedSource):
    '''
    An alternative to `FilteredSource` that allows efficient retrieval of
    the underlying stream at a location corresponding to a position in the
    filtered stream.  Typically used via `Filter`.
    
    This is necessary to avoid O(n^2) time when parsing chunks of data
    with a filtered stream (without the cache, retrieving an offset in 
    our linked-list style streams is O(n)).
    
    Predicate takes a stream and should return a boolean indicating whether
    the first item is to be used.
    '''

    def __init__(self, predicate, stream):
        def transform(stream):
            '''
            Create a transform as required by `BaseTransformedSource`.
            '''
            while stream:
                item = stream[0]
                if predicate(item):
                    yield (item, stream)
                stream = stream[1:]
        super(CachingFilteredSource, self).__init__(transform, stream)
        

# pylint: disable-msg=R0903
# also have public attribute
class Transform(object):
    '''
    Transform a `LocationStream` using a `CachingTransformedSource`.  This 
    consumes memory proportional to the amount of data read from the filtered 
    stream, but allows efficient retrieval of the underlying stream at a 
    location equivalent to the filtered stream.
    '''
    
    def __init__(self, transform, stream, factory=DEFAULT_STREAM_FACTORY):
        self.__source = CachingTransformedSource(transform, stream)
        self.stream = factory(self.__source)

    def locate(self, stream):
        '''
        Find the first location in the original stream which, when filtered,
        would match the given stream.
        '''
        return self.__source.locate(stream)
    
    
class Filter(object):
    '''
    Filter a `LocationStream` using a `CachingFilteredSource`.  This consumes
    memory proportional to the amount of data read from the filtered stream,
    but allows efficient retrieval of the underlying stream at a location
    equivalent to the filtered stream.
    '''
    
    def __init__(self, predicate, stream, factory=DEFAULT_STREAM_FACTORY):
        self.__source = CachingFilteredSource(predicate, stream)
        self.stream = factory(self.__source)

    def locate(self, stream):
        '''
        Find the first location in the original stream which, when filtered,
        would match the given stream.
        '''
        return self.__source.locate(stream)


# pylint: disable-msg=R0901, R0904, E1101, W0212
# lepl convention
class _Exclude(OperatorMatcher):
    '''
    Match the content against a stream filtered by a predicate.
    '''
    
    def __init__(self, exclude, matcher):
        '''
        filter is used to exclude values from the stream; matcher matches
        against the remaining stream.
        '''
        super(_Exclude, self).__init__()
        self._arg(exclude=exclude)
        self._arg(matcher=matcher)
        
    @tagged
    def _match(self, stream_in):
        '''
        Matcher the contents against the filtered stream.
        '''
        filter_ = Filter(lambda strm: not self.exclude(strm), stream_in)
        generator = self.matcher._match(filter_.stream)
        try:
            while True:
                (result, stream) = yield generator
                yield (result, filter_.locate(stream))
        except StopIteration:
            return


# pylint: disable-msg=C0103
# lepl convention
def Exclude(exclude):
    '''
    A matcher factory - matchers apply their arguments to filtered streams.
    
    So, for example,
    
      factory = Exclude(lambda x: x == 'a')
      matcher = factory(Literal('b')[:, ...]) + Literal('c')[:, ...]
      matcher.parse_string('abababccc')
      ['bbbccc']  
    
    Warning - consumes space proportional to the size of the filtered data.
    '''
    return lambda matcher: _Exclude(exclude, matcher)


class _ExcludeSequence(OperatorMatcher):
    '''
    Match the content against a stream filtered to remove a sequence.
    '''
    
    def __init__(self, exclude, matcher, *sequence):
        '''
        exclude takes two arguments - a value from sequence and an item
        from the stream.
        
        The argument arder is a bit unusual here, but sequence is *args so that
        each value appears as a child and so is automatically detected when
        generating the lexer.
        '''
        super(_ExcludeSequence, self).__init__()
        self._arg(exclude=exclude)
        self._arg(matcher=matcher)
        self._args(sequence=sequence)
        
    @staticmethod
    def __zip(seq1, seq2):
        '''
        Avoid calling len() on seq2
        '''
        for item in seq1:
            if seq2:
                yield (item, seq2[0])
                seq2 = seq2[1:]
    
    @tagged
    def _match(self, stream_in):
        '''
        Matcher the contents against the filtered stream.
        '''
        def filter_(stream):
            '''
            Only drop the entire sequence.
            '''
            residual = 0
            while stream:
                if residual:
                    stream = stream[1:]
                    residual -= 1
                else:
                    for (seq, item) in self.__zip(self.sequence, stream):
                        if not self.exclude(seq, item):
                            break
                        else:
                            residual += 1
                    if residual != len(self.sequence):
                        residual = 1
                        yield (stream[0], stream)
        transform = Transform(filter_, stream_in)
        generator = self.matcher._match(transform.stream)
        try:
            while True:
                (result, stream) = yield generator
                yield (result, transform.locate(stream))
        except StopIteration:
            return


def ExcludeSequence(exclude, sequence):
    '''
    A matcher factory - matchers apply their arguments to filtered streams.

    exclude takes two arguments - a value from sequence and an item
    from the stream.  If it returns true for all items in the sequence then
    the corresponding items in the stream are dropped.
    
    Warning - consumes space proportional to the size of the filtered data.
    '''
    # pylint: disable-msg=W0142
    # see comment in `_ExcludedSequence`
    return lambda matcher: _ExcludeSequence(exclude, matcher, *sequence)

