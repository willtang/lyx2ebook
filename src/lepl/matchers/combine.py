
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
Matchers that combine sub-matchers (And, Or etc).
'''

# pylint: disable-msg=C0103,W0212
# (consistent interfaces)
# pylint: disable-msg=E1101
# (_args create attributes)
# pylint: disable-msg=R0901, R0904, W0142
# lepl conventions

from abc import ABCMeta
from collections import deque

from lepl.matchers.core import Literal
from lepl.matchers.matcher import add_children
from lepl.matchers.support import coerce_, sequence_matcher_factory, \
    trampoline_matcher_factory, to
from lepl.matchers.transform import Transformable
from lepl.support.lib import lmap, format, document


# pylint: disable-msg=C0103, W0105
# Python 2.6
#class BaseSearch(metaclass=ABCMeta):
_BaseSearch = ABCMeta('_BaseSearch', (object, ), {})
'''
ABC used to identify matchers.  

Note that graph traversal assumes subclasses are hashable and iterable.
'''

class BaseSearch(_BaseSearch):
    pass


def _cleanup(queue):
    '''
    Utility to discard queued/stacked values.
    '''
    for (_count, _acc, _stream, generator) in queue:
        generator.generator.close()
        

def search_factory(factory):
    '''
    Add the arg processing common to all searching.
    '''
    def new_factory(first, start, stop, rest=None):
        rest = first if rest is None else rest
        return factory(first, start, stop, rest)
    return document(new_factory, factory)


@trampoline_matcher_factory(False)
@search_factory
def DepthFirst(first, start, stop, rest):
    '''
    (Post order) Depth first repetition (typically used via `Repeat`).
    '''
    def match(support, stream):
        stack = deque()
        try:
            stack.append((0, [], stream, first._match(stream)))
            while stack:
                (count1, acc1, stream1, generator) = stack[-1]
                extended = False
                if stop is None or count1 < stop:
                    count2 = count1 + 1
                    try:
                        (value, stream2) = yield generator
                        acc2 = acc1 + value
                        stack.append((count2, acc2, stream2, 
                                      rest._match(stream2)))
                        extended = True
                    except StopIteration:
                        pass
                if not extended:
                    if count1 >= start and (stop is None or count1 <= stop):
                        yield (acc1, stream1)
                    stack.pop()
        finally:
            _cleanup(stack)
            
    return match


@trampoline_matcher_factory(False)
@search_factory
def BreadthFirst(first, start, stop, rest):
    '''
    (Level order) Breadth first repetition (typically used via `Repeat`).
    '''
    def match(support, stream):
        queue = deque()
        try:
            queue.append((0, [], stream, first._match(stream)))
            while queue:
                (count1, acc1, stream1, generator) = queue.popleft()
                if count1 >= start and (stop is None or count1 <= stop):
                    yield (acc1, stream1)
                count2 = count1 + 1
                try:
                    while True:
                        (value, stream2) = yield generator
                        acc2 = acc1 + value
                        if stop is None or count2 <= stop:
                            queue.append((count2, acc2, stream2, 
                                          rest._match(stream2)))
                except StopIteration:
                    pass
        finally:
            _cleanup(queue)
            
    return match


@trampoline_matcher_factory(False, matcher=to(Literal))
def OrderByResultCount(matcher, ascending=True):
    '''
    Modify a matcher to return results in length order.
    '''

    def match(support, stream):
        '''
        Attempt to match the stream.
        '''
        generator = matcher._match(stream)
        results = []
        try:
            while True:
                # syntax error if this on one line?!
                result = yield generator
                results.append(result)
        except StopIteration:
            pass
        for result in sorted(results,
                             key=lambda x: len(x[0]), reverse=ascending):
            yield result
            
    return match
            

@sequence_matcher_factory()
@search_factory
def DepthNoTrampoline(first, start, stop, rest):
    '''
    A more efficient search when all matchers are functions (so no need to
    trampoline).  Depth first (greedy).
    '''
    def matcher(support, stream):
        stack = deque()
        try:
            stack.append((0, [], stream, first._untagged_match(stream)))
            while stack:
                (count1, acc1, stream1, generator) = stack[-1]
                extended = False
                if stop is None or count1 < stop:
                    count2 = count1 + 1
                    try:
                        (value, stream2) = next(generator)
                        acc2 = acc1 + value
                        stack.append((count2, acc2, stream2, 
                                      rest._untagged_match(stream2)))
                        extended = True
                    except StopIteration:
                        pass
                if not extended:
                    if count1 >= start and (stop is None or count1 <= stop):
                        yield (acc1, stream1)
                    stack.pop()
        finally:
            for (_count, _acc, _stream, generator) in stack:
                generator.close()
            
    return matcher
            
            
@sequence_matcher_factory()
@search_factory
def BreadthNoTrampoline(first, start, stop, rest):
    '''
    A more efficient search when all matchers are functions (so no need to
    trampoline).  Breadth first (non-greedy).
    '''
    def matcher(support, stream):
        queue = deque()
        try:
            queue.append((0, [], stream, first._untagged_match(stream)))
            while queue:
                (count1, acc1, stream1, generator) = queue.popleft()
                if count1 >= start and (stop is None or count1 <= stop):
                    yield (acc1, stream1)
                count2 = count1 + 1
                for (value, stream2) in generator:
                    acc2 = acc1 + value
                    if stop is None or count2 <= stop:
                        queue.append((count2, acc2, stream2, 
                                      rest._untagged_match(stream2)))
        finally:
            for (_count, _acc, _stream, generator) in queue:
                generator.close()
            
    return matcher


add_children(BaseSearch, DepthFirst, BreadthFirst, \
             DepthNoTrampoline, BreadthNoTrampoline)

                
class _BaseCombiner(Transformable):
    '''
    Support for `And` and `Or`.
    '''
    
    def __init__(self, *matchers):
        super(_BaseCombiner, self).__init__()
        self._args(matchers=lmap(coerce_, matchers))
        
    def compose(self, wrapper):
        '''
        Generate a new instance with the composed function from the Transform.
        '''
        copy = type(self)(*self.matchers)
        copy.wrapper = self.wrapper.compose(wrapper)
        return copy
    

@trampoline_matcher_factory(True, args_=to(Literal))
def And(*matchers):
    '''
    Match one or more matchers in sequence (**&**).
    It can be used indirectly by placing ``&`` between matchers.
    '''
#    matchers = lmap(coerce_, matchers)
    
    def match(support, stream_in):
        if matchers:
            stack = deque([([], 
                            matchers[0]._match(stream_in), 
                            matchers[1:])])
            append = stack.append
            pop = stack.pop
            try:
                while stack:
                    (result, generator, queued) = pop()
                    try:
                        (value, stream_out) = yield generator
                        append((result, generator, queued))
                        if queued:
                            append((result+value, 
                                    queued[0]._match(stream_out), 
                                    queued[1:]))
                        else:
                            yield (result+value, stream_out)
                    except StopIteration:
                        pass
            finally:
                for (result, generator, queued) in stack:
                    generator.generator.close()
                    
    return match


@sequence_matcher_factory(args_=to(Literal))
def AndNoTrampoline(*matchers):
    '''
    Used as an optimisation when sub-matchers do not require the trampoline.
    '''
    def matcher(support, stream_in):
        if matchers:
            stack = deque([([], matchers[0]._untagged_match(stream_in), matchers[1:])])
            append = stack.append
            pop = stack.pop
            try:
                while stack:
                    (result, generator, queued) = pop()
                    try:
                        (value, stream_out) = next(generator)
                        append((result, generator, queued))
                        if queued:
                            append((result+value, 
                                    queued[0]._untagged_match(stream_out), 
                                    queued[1:]))
                        else:
                            yield (result+value, stream_out)
                    except StopIteration:
                        pass
            finally:
                for (result, generator, queued) in stack:
                    generator.close()
                    
    return matcher
        
        
@trampoline_matcher_factory(True, args_=to(Literal))
def Or(*matchers):
    '''
    Match one of the given matchers (**|**).
    It can be used indirectly by placing ``|`` between matchers.
    
    Matchers are tried from left to right until one succeeds; backtracking
    will try more from the same matcher and, once that is exhausted,
    continue to the right.  String arguments will be coerced to 
    literal matches.
    '''
#    matchers = lmap(coerce_, matchers)
   
    def match(support, stream_in):
        '''
        Do the matching (return a generator that provides successive 
        (result, stream) tuples).  The result will correspond to one of the
        sub-matchers (starting from the left).
        '''
        for matcher in matchers:
            generator = matcher._match(stream_in)
            try:
                while True:
                    yield (yield generator)
            except StopIteration:
                pass
            
    return match


@sequence_matcher_factory(args_=to(Literal))
def OrNoTrampoline(*matchers):
    '''
    Used as an optimisation when sub-matchers do not require the trampoline.
    '''
    def match(support, stream_in):
        '''
        Do the matching (return a generator that provides successive 
        (result, stream) tuples).  The result will correspond to one of the
        sub-matchers (starting from the left).
        '''
        for matcher in matchers:
            for result in matcher._untagged_match(stream_in):
                yield result
    return match

       
@trampoline_matcher_factory(True)
def First(*matchers):
    '''
    Match the first successful matcher only (**%**).
    It can be used indirectly by placing ``%`` between matchers.
    Note that backtracking for the first-selected matcher will still occur.

    Matchers are tried from left to right until one succeeds; backtracking
    will try more from the same matcher (only).  String arguments will be 
    coerced to literal matches.
    '''
    def match(self, stream):
        matched = False
        for matcher in self.matchers:
            generator = matcher._match(stream)
            try:
                while True:
                    yield (yield generator)
                    matched = True
            except StopIteration:
                pass
            if matched:
                break

    return match


