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
Track the maximum depth of a stream.
'''

from lepl.stream.stream import LocationStream, SimpleStream
from lepl.matchers.support import trampoline_matcher_factory
from lepl.support.lib import open_stop, format


class Memory(object):
    
    def __init__(self, deepest):
        self.deepest = deepest


def facade_factory(stream):
    '''
    Generate a facade class (we need a class so that we can register as
    a subclass of the correct stream interface).
    '''
    
    class Facade(object):
        
        __slots__ = ['_Facade__stream', '_Facade__memory', '__weakref__']
        
        def __init__(self, stream, memory):
            self.__stream = stream
            self.__memory = memory
            memory.deepest = stream
                
        def __getitem__(self, spec):
            if isinstance(spec, slice) and open_stop(spec):
                return Facade(self.__stream.__getitem__(spec), self.__memory)
            else:
                return self.__stream.__getitem__(spec)

        def __bool__(self):
            return bool(self.__stream)
    
        def __nonzero__(self):
            return self.__bool__() 
    
        def __len__(self):
            return len(self.__stream)

        def __repr__(self):
            return repr(self.__stream)
    
        def __str__(self):
            return str(self.__stream)
    
        def __hash__(self):
            return hash(self.__stream)
        
        def __eq__(self, other):
            return isinstance(other, Facade) and self.__stream == other.__stream
        
        @property
        def location(self):
            return self.__stream.location

        @property
        def line_number(self):
            return self.__stream.line_number
        
        @property
        def line_offset(self):
            return self.__stream.line_offset
        
        @property
        def character_offset(self):
            return self.__stream.character_offset
   
        @property
        def text(self):
            # this is a hack needed for inter-op with python regexps, which
            # only accept strings.  it's identical to the hack in Regexp().
            try:
                return self.__stream.text
            except AttributeError:
                return self.__stream
    
        @property
        def source(self):
            return self.__stream.source
        
        @property
        def stream(self):
            return self.__stream

    if isinstance(stream, LocationStream):
        LocationStream.register(Facade)
    else:
        SimpleStream.register(Facade)
    memory = Memory(stream)
    facade = Facade(stream, memory)
    return (facade, memory)


@trampoline_matcher_factory()
def FullFirstMatch(matcher, eos=True):
    '''
    Raise an exception if the first match fails (if eos=False) or does not
    consume the entire input stream (eos=True).  The exception includes 
    information about the location of the deepest match.
    
    This only works for the first match because we cannot reset the stream
    facade for subsequent matches (also, if you want multiple matches you
    probably want more sophisticated error handling than this).
    '''
    
    def _matcher(support, stream1):
        # add facade to stream
        (stream2, memory) = facade_factory(stream1)
        
        # first match
        generator = matcher._match(stream2)
        try:
            (result2, stream3) = yield generator
            if eos and stream3.stream:
                raise FullFirstMatchException(memory.deepest)
            else:
                yield (result2, stream3.stream)
        except StopIteration:
            raise FullFirstMatchException(memory.deepest)
        
        # subsequent matches:
        while True:
            (result2, stream3) = yield generator
            # drop stream wrapper
            yield (result2, stream3.stream)

    return _matcher


class FullFirstMatchException(Exception):
    '''
    The exception raised by `FullFirstMatch`.  This includes information
    about the deepest point read in the stream. 
    '''
    
    def __init__(self, stream):
        try:
            if stream.line_number is None:
                msg = format("The match failed at '{0}',"
                             "\nIndex {1} of {2}.",
                             stream, stream.line_offset, stream.source)
            else:
                msg = format("The match failed at '{0}',"
                             "\nLine {1}, character {2} of {3}.",
                             stream, stream.line_number, stream.line_offset,
                             stream.source)
        except AttributeError:
            msg = format("The match failed at '{0}'.", stream)
        super(FullFirstMatchException, self).__init__(msg)
        self.stream = stream

