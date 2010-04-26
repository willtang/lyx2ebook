
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
Base class for matchers.
'''


from abc import ABCMeta, abstractmethod
from types import FunctionType

from lepl.support.lib import format, singleton, identity

# pylint: disable-msg=C0103, W0105
# Python 2.6
#class Matcher(metaclass=ABCMeta):
_Matcher = ABCMeta('_Matcher', (object, ), {})
'''
ABC used to identify matchers.  

Note that graph traversal assumes subclasses are hashable and iterable.
'''

class Matcher(_Matcher):
    
    def __init__(self):
        self._small_str = self.__class__.__name__
    
#    @abstractmethod 
    def _match(self, stream):
        '''
        This is the core method called during recursive decent.  It must
        yield (stream, results) pairs until the matcher has exhausted all
        possible matches.
        
        To evaluate a sub-matcher it should yield the result of calling
        this method on the sub-matcher:
        
            generator = sub_matcher._match(stream_in)
            try:
                while True:
                    # evaluate the sub-matcher
                    (stream_out, result) = yield generator
                    ....
                    # return the result from this matcher
                    yield (stream_out, result)
            except StopIteration:
                ...
                
        The implementation should be decorated with @tagged in almost all
        cases.
        '''

#    @abstractmethod
    def indented_repr(self, indent, key=None):
        '''
        Called by repr; should recursively call contents.
        '''
        

# Python 2.6
#class FactoryMatcher(metaclass=ABCMeta):
_FactoryMatcher = ABCMeta('_FactoryMatcher', (object, ), {})
'''
ABC used to identify factory matchers (have a property factory that 
identifies the matcher they generate).
'''


class FactoryMatcher(_FactoryMatcher):
    '''
    Imagine an abstract property called 'factory' below.
    '''


class MatcherTypeException(Exception):
    '''
    Used to flag problems related to matcher types.
    '''
    
def raiseException(msg):
    raise MatcherTypeException(msg)


def case_type(matcher, if_factory, if_matcher):
    if isinstance(matcher, FunctionType) and hasattr(matcher, 'factory'):
        return if_factory(matcher.factory)
    elif issubclass(matcher, Matcher):
        return if_matcher(matcher)
    else:
        raise MatcherTypeException(
            format('{0!s} ({1}) does not appear to be a matcher type', 
                   matcher, type(matcher)))


def case_instance(matcher, if_wrapper, if_matcher):
    from lepl.matchers.support import FactoryMatcher
    try:
        if isinstance(matcher, FactoryMatcher):
            return if_wrapper(matcher.factory)
    except TypeError:
        pass # bug in python impl
    # may already be unpacked
    if isinstance(matcher, FunctionType):
        return if_wrapper(matcher)
    if isinstance(matcher, Matcher):
        return if_matcher(matcher)
    else:
        raise MatcherTypeException(
            format('{0!s} ({1}) does not appear to be a matcher', 
                   matcher, type(matcher)))


def canonical_matcher_type(matcher):
    '''
    Given a "constructor" (either a real constructor, or an annotated 
    function), generate something that uniquely identifies that (the class
    for real constructors, and the embedded function for the output from 
    the factories).
    '''
    return case_type(matcher, identity, identity)

def matcher_type(matcher, fail=True):
    '''
    '''
    try:
        return case_instance(matcher, identity, type)
    except MatcherTypeException as e:
        if fail:
            raise e
        else:
            return False

def matcher_map(map_):
    '''
    Rewrite a map whose keys are matchers to use canonical_matcher_type.
    '''
    return dict((canonical_matcher_type(key), map_[key]) for key in map_)

def matcher_instance(matcher):
    return case_instance(matcher, identity, identity)


class Relations(object):
    
    def __init__(self, base):
        self.base = base
        self.factories = set()
        
    def add_child(self, child):
        return case_type(child,
                         lambda m: self.factories.add(m),
                         lambda m: self.base.register(m))
        
    def child_of(self, child):
        return case_instance(child, 
                             lambda m: m is self.base or m in self.factories,
                             lambda m: isinstance(self.base, type) 
                             and isinstance(m, self.base))
        

def relations(base):
    # if base is a factory then we want the related type
    try:
        base = canonical_matcher_type(base)
    except MatcherTypeException:
        pass
    table = singleton(Relations, dict)
    if base not in table:
        table[base] = Relations(base)
    return table[base]
    

def is_child(child, base, fail=True):
    try:
        return relations(base).child_of(child)
    except MatcherTypeException as e:
        if fail:
            raise e
        else:
            return False

def add_child(base, child):
    relations(base).add_child(child)

def add_children(base, *children):
    for child in children:
        add_child(base, child)
        