
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
Matchers that embody fundamental, common actions.
'''

# pylint: disable-msg=C0103,W0212
# (consistent interfaces)
# pylint: disable-msg=E1101
# (_args create attributes)
# pylint: disable-msg=R0901, R0904, W0142
# lepl conventions

from re import compile as compile_

from lepl.core.parser import tagged
from lepl.regexp.matchers import DfaRegexp
from lepl.matchers.support import OperatorMatcher, coerce_, \
    function_matcher, function_matcher_factory, trampoline_matcher_factory, to
from lepl.support.lib import format


@function_matcher_factory()
def Any(restrict=None):
    '''
    Create a matcher for a single character.
    
    :Parameters:
    
      restrict (optional)
        A list of tokens (or a string of suitable characters).  
        If omitted any single token is accepted.  
        
        **Note:** This argument is *not* a sub-matcher.
    '''
    warned = [False]

    def match(support, stream):
        '''
        Do the matching.  The result will be a single matchingcharacter.
        '''
        ok = bool(stream)
        if ok and restrict:
            try:
                ok = stream[0] in restrict
            except TypeError:
                # it would be nice to make this an error, but for line aware
                # parsing (and any other heterogenous input) it's legal
                if not warned[0]:
                    support._warn(format('Cannot restrict {0} with {1!r}',
                                          stream[0], restrict))
                    warned[0] = True
                    ok = False
        if ok:
            return ([stream[0]], stream[1:])
            
    return match
            
            
@function_matcher_factory()
def Literal(text):
    '''
    Match a series of tokens in the stream (**''**).

    Typically the argument is a string but a list might be appropriate 
    with some streams.
    '''
    def match(support, stream):
        '''
        Do the matching (return a generator that provides successive 
        (result, stream) tuples).

        Need to be careful here to use only the restricted functionality
        provided by the stream interface.
        '''
        try:
            data = stream[0:len(text)]
            if text == data:
                return ([text], stream[len(text):])
        except IndexError:
            pass
    return match

       
@function_matcher
def Empty(support, stream):
    '''
    Match any stream, consumes no input, and returns nothing.
    '''
    return ([], stream)
 

class Lookahead(OperatorMatcher):
    '''
    Tests to see if the embedded matcher *could* match, but does not do the
    matching.  On success an empty list (ie no result) and the original
    stream are returned.
    
    When negated (preceded by ~) the behaviour is reversed - success occurs
    only if the embedded matcher would fail to match.
    
    This is a consumer because it's correct functioning depends directly on
    the stream's contents.
    '''
    
    def __init__(self, matcher, negated=False):
        '''
        On success, no input is consumed.
        If negated, this will succeed if the matcher fails.  If the matcher is
        a string it is coerced to a literal match.
        '''
        super(Lookahead, self).__init__()
        self._arg(matcher=coerce_(matcher))
        self._karg(negated=negated)
    
    @tagged
    def _match(self, stream):
        '''
        Do the matching (return a generator that provides successive 
        (result, stream) tuples).
        '''
        try:
            yield self.matcher._match(stream) # an evaluation, not a return
            success = True
        except StopIteration:
            success = False
        if success is self.negated:
            return
        else:
            yield ([], stream)
            
    def __invert__(self):
        '''
        Invert the semantics (this overrides the usual meaning for ~).
        '''
        return Lookahead(self.matcher, negated=not self.negated)
            

@function_matcher_factory()
def Regexp(pattern):
    '''
    Match a regular expression.  If groups are defined, they are returned
    as results.  Otherwise, the entire expression is returned.

    If the pattern contains groups, they are returned as separate results,
    otherwise the whole match is returned.
    
    :Parameters:
    
      pattern
        The regular expression to match. 
    '''
    pattern = compile_(pattern)
    
    def match(support, stream):
        try:
            match = pattern.match(stream.text)
        except AttributeError: # no text method
            match = pattern.match(stream)
        if match:
            eaten = len(match.group())
            if match.groups():
                return (list(match.groups()), stream[eaten:])
            else:
                return ([match.group()], stream[eaten:])
    return match
        

class Delayed(OperatorMatcher):
    '''
    A placeholder that allows forward references (**+=**).  Before use a 
    matcher must be assigned via '+='.
    '''
    
    def __init__(self, matcher=None):
        '''
        Introduce the matcher.  It can be defined later with '+='
        '''
        super(Delayed, self).__init__()
        self._karg(matcher=matcher)
    
    def _match(self, stream):
        '''
        Do the matching (return a generator that provides successive 
        (result, stream) tuples).
        '''
        if self.matcher:
            return self.matcher._match(stream)
        else:
            raise ValueError('Delayed matcher still unbound.')
        
    # pylint: disable-msg=E0203, W0201
    # _karg defined this in constructor
    def __iadd__(self, matcher):
        if self.matcher:
            raise ValueError('Delayed matcher already bound.')
        else:
            self.matcher = coerce_(matcher)
            return self
        

@function_matcher
def Eof(support, stream):
    '''
    Match the end of a stream.  Returns nothing.  

    This is also aliased to Eos in lepl.derived.
    '''
    if not stream:
        return ([], stream)


@trampoline_matcher_factory(matcher=to(Literal))
def Consumer(matcher, consume=True):
    '''
    Only accept the match if it consumes data from the input
    '''
    def match(support, stream_in):
        '''
        Do the match and test whether the stream has progressed.
        '''
        try:
            generator = matcher._match(stream_in)
            while True:
                (result, stream_out) = yield generator
                if consume == (stream_in != stream_out):
                    yield (result, stream_out)
        except StopIteration:
            pass
    return match


@trampoline_matcher_factory(matcher=to(Literal), condition=to(DfaRegexp))
def PostMatch(matcher, condition, not_=False, equals=True):
    '''
    Apply the condition to each result from the matcher.  It should return
    either an exact match (equals=True) or simply not fail (equals=False).
    If `not_` is set, the test is inverted.
    
    `matcher` is coerced to `Literal()`, condition to `DfaRegexp()`
    '''
    from lepl.regexp.matchers import DfaRegexp
#    matcher = coerce_(matcher)
#    condition = coerce_(condition, DfaRegexp)
    
    def match(support, stream_in):
        '''
        Do the match and test the result.
        '''
        generator = matcher._match(stream_in)
        while True:
            (results, stream_out) = yield generator
            success = True
            for result in results:
                if not success: break
                generator2 = condition._match(result)
                try:
                    (results2, _ignored) = yield generator2
                    if not_:
                        # if equals is false, we need to fail just because
                        # we matched.  otherwise, we need to fail only if
                        # we match.
                        if not equals or (len(results2) == 1 or 
                                          results2[0] == result):
                            success = False
                    else:
                        # if equals is false, not generating an error is
                        # sufficient, otherwise we must fail if the result
                        # does not match
                        if equals and (len(results2) != 1 or 
                                       results2[0] != result):
                            success = False
                except:
                    # fail unless if we were expecting any kind of match
                    if not not_:
                        success = False
            if success:
                yield (results, stream_out)
    
    return match

                    
