
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
Memoisation (both as described by Norvig 1991, giving Packrat 
parsers for non-left recursive grammars, and the equivalent described by
Frost and Hafiz 2006 which allows left-recursive grammars to be used).
 
Note that neither paper describes the extension to backtracking with
generators implemented here. 
'''

# for some reason (parsing of yields?) pyulint cannot process this file
# (but running from the command line gives partial data)

from abc import ABCMeta
from itertools import count

from lepl.matchers.core import OperatorMatcher
from lepl.matchers.matcher import is_child
from lepl.core.parser import tagged, GeneratorWrapper
from lepl.support.state import State
from lepl.support.lib import LogMixin, empty, format


# pylint: disable-msg=W0105, C0103, R0903, W0212
# Python 2.6
#class NoMemo(metaclass=NoMemo):
NoMemo = ABCMeta('NoMemo', (object, ), {})
'''
ABC used to indicate that memoisation should not be applied.  
'''

# pylint: disable-msg=R0901, R0904
# lepl conventions


class MemoException(Exception):
    '''
    Exception raised for problems with memoisation.
    '''
    
def RMemo(matcher):
    '''
    Wrap in the _RMemo cache if required.
    '''
    if is_child(matcher, NoMemo, fail=False):
        return matcher
    else:
        return _RMemo(matcher)


class _RMemo(OperatorMatcher):
    '''
    A simple memoizer for grammars that do not have left recursion.  Since this
    fails with left recursion it's safer to always use LMemo.
    
    Making this class Transformable did not improve performance (it's better
    to place the transformation on critical classes like Or and And). 
    '''
    
    # pylint: disable-msg=E1101
    # (using _args to define attributes)
    
    def __init__(self, matcher):
        super(_RMemo, self).__init__()
        self._arg(matcher=matcher)
        self.__table = {}
        self.__state = State.singleton()
        
    def _match(self, stream):
        '''
        Attempt to match the stream.
        '''
        # pylint: disable-msg=W0212
        # (_match is an internal interface)
        try:
            key = (stream, self.__state.hash)
            if key not in self.__table:
                # we have no cache for this stream, so we need to generate the
                # entry.  we do not care about nested calls with the same stream
                # because this memoization is not for left recursion.  that 
                # means that we can return a table around this generator 
                # immediately.
                self.__table[key] = RTable(self.matcher._match(stream))
            return GeneratorWrapper(self.__table[key].generator(self.matcher, stream),
                                    self, stream)
        except TypeError as e: # unhashable type; cannot cache
            self._warn(format('Cannot memoize (cannot hash {0!r}: {1})', 
                              stream, e))
            return self.matcher._match(stream)


class RTable(LogMixin):
    '''
    Wrap a generator so that separate uses all call the same core generator,
    which is itself tabulated as it unrolls.
    '''
    
    def __init__(self, generator):
        super(RTable, self).__init__()
        self.__generator = generator
        self.__table = []
        self.__stopped = False
        self.__active = False
        self.__cached_stream = None
        
    def __read(self, i, matcher, stream):
        '''
        Either return a value from previous cached values or call the
        embedded generator to get the next value (and then store it).
        '''
        if self.__active:
            raise MemoException(format('''Left recursion with RMemo?
i: {0}
table: {1!r}
stream: {2}/{3} (initially {4})
matcher: {5!s}''', 
i, self.__table, stream, type(stream), self.__cached_stream, matcher))
        try:
            while i >= len(self.__table) and not self.__stopped:
                try:
                    self.__active = True
                    self.__cached_stream = stream
                    result = yield self.__generator
                finally:
                    self.__active = False
                self.__table.append(result)
        except StopIteration:
            self.__stopped = True
        if i < len(self.__table):
            yield self.__table[i]
        else:
            raise StopIteration()
    
    def generator(self, matcher, stream):
        '''
        A proxy to the "real" generator embedded inside the cache.
        '''
        for i in count():
            yield (yield GeneratorWrapper(self.__read(i, matcher, stream), 
                            _DummyMatcher(self.__class__.__name__, 
                                          matcher), 
                            stream))


class _DummyMatcher(object):
    '''
    Fake matcher used to provide the appropriate interface to the generator 
    wrapper from within `RTable`.
    '''
    
    def __init__(self, outer, inner):
        '''
        Making this lazy has no effect on efficiency for nested.right.
        '''
        self.__cached_repr = format('{0}({1})', outer, inner)
        
    def __repr__(self):
        return self.__cached_repr
    
    def __str__(self):
        return self.__cached_repr
        
        
def LMemo(matcher):
    '''
    Wrap in the _LMemo cache if required.
    '''
    if is_child(matcher, NoMemo, fail=False):
        return matcher
    else:
        return _LMemo(matcher)


class _LMemo(OperatorMatcher):
    '''
    A memoizer for grammars that do have left recursion.
    '''
    
    # pylint: disable-msg=E1101
    # (using _args to define attributes)
    
    def __init__(self, matcher):
        super(_LMemo, self).__init__()
        self._arg(matcher=matcher)
        self.__caches = {}
        self.__state = State.singleton()
        
    def _match(self, stream):
        '''
        Attempt to match the stream.
        '''
        key = (stream, self.__state.hash)
        if key not in self.__caches:
            self.__caches[key] = PerStreamCache(self.matcher)
        return self.__caches[key]._match(stream)
        

class PerStreamCache(LogMixin):
    '''
    Manage the counter (one for each different stream) that limits the 
    number of (left-)recursive calls.  Each permitted call receives a separate
    `PerCallCache`. 
    '''
    
    def __init__(self, matcher):
        super(PerStreamCache, self).__init__()
        self.__matcher = matcher
        self.__counter = 0
        self.__first = None
        
    @staticmethod
    def __curtail(count_, stream):
        '''
        Do we stop at this point?
        '''
        if count_ == 1:
            return False
        else:
            return count_ > len(stream) 
        
    @tagged
    def _match(self, stream):
        '''
        Attempt to match the stream.
        '''
        if not self.__first:
            self.__counter += 1
            if self.__curtail(self.__counter, stream):
                return empty()
            else:
                cache = PerCallCache(self.__matcher._match(stream))
                if self.__first is None:
                    self.__first = cache
                return cache.generator()
        else:
            return self.__first.view()
        

class PerCallCache(LogMixin):
    '''
    The "final" cache for a matcher at a certain recursive depth and with a
    certain input stream.
    '''
    
    def __init__(self, generator):
        super(PerCallCache, self).__init__()
        self.__generator = generator
        self.__cache = []
        self.__returned = False # has an initial match completed?
        self.__complete = False # have all matches completed?
        self.__unstable = False # has a view completed before the matcher?
        
    def view(self):
        '''
        Provide available (cached) values.
        
        This does not generate further values itself - the assumption is that
        generator() has already done this.  I believe that is reasonable
        (the argument is basically that generator was created first, so is
        'above' whatever is using view()), but I do not have a proof.
        
        Note that changing this assumption is non-trivial.  It would be easy
        to have shared access to the generator, but we would need to guarantee
        that the generator is not "in the middle" of generating a new value
        (ie has not been yielded by some earlier, pending call).
        '''
        for value in self.__cache:
            yield value
        self.__unstable = not self.__complete
    
    def generator(self):
        '''
        Expand the underlying generator, storing results.
        '''
        try:
            while True:
                result = yield self.__generator
                if self.__unstable:
                    self._warn(
                        format('A view completed before the cache was '
                               'complete: {0!r}. This typically means that '
                               'the grammar contains a matcher that does not '
                               'consume input within a loop and is usually '
                               'an error.', self.__generator))
                self.__cache.append(result)
                self.__returned = True
                yield result
        finally:
            self.__complete = True
            
    def __bool__(self):
        '''
        Has the underlying call returned?  If so, then we can use the cache.
        If not, then the call tree is still being constructed via left-
        recursive calls.
        '''
        return self.__returned
    
    def __nonzero__(self):
        '''
        For Python 2.6: may it burn in hell, hell I say!
        '''
        return self.__bool__()
