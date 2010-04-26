from lepl.regexp.unicode import UnicodeAlphabet

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
Rewrite the tree of matchers from the bottom up (as far as possible)
using regular expressions.  This is complicated by a number of things.

First, intermediate parts of regular expressions are not matchers, so we need 
to keep them inside a special container type that we can detect and convert to
a regular expression when needed (since at some point we cannot continue with
regular expressions).

Second, we sometimes do not know if our regular expression can be used until we 
have moved higher up the matcher tree.  For example, And() might convert all
sub-expressions to a sequence if it's parent is an Apply(add).  So we may
need to store several alternatives, along with a way of selecting the correct
alternative.

So cloning a node may give either a matcher or a container.  The container
will provide both a matcher and an intermediate regular expression.  The logic
for handling odd dependencies is more difficult to implement in a general
way, because it is not clear what all cases may be.  For now, therefore,
we use a simple state machine approach using a tag (which is almost always
None).  
'''

from logging import getLogger

from lepl.matchers.matcher import Matcher, matcher_map
from lepl.matchers.support import FunctionWrapper, SequenceWrapper, \
    TrampolineWrapper, TransformableTrampolineWrapper
from lepl.regexp.core import Choice, Sequence, Repeat, Empty
from lepl.regexp.matchers import NfaRegexp
from lepl.regexp.interval import Character
from lepl.core.rewriters import copy_standard_attributes, clone, \
    DelayedClone, Rewriter
from lepl.support.lib import format, str, document


class RegexpContainer(object):
    '''
    The container referred to above, which carries a regular expression and
    an alternative matcher "up the tree" during rewriting.
    '''
    
    log = getLogger('lepl.regexp.rewriters.RegexpContainer')

    def __init__(self, matcher, regexp, use, add_reqd=False):
        self.matcher = matcher   # current best matcher (regexp or not)
        self.regexp = regexp     # the current regexp
        self.use = use           # is the regexp a win?
        self.add_reqd = add_reqd # we need "add" to combine values (from And)?
        
    def __str__(self):
        return ','.join([str(self.matcher.__class__), str(self.regexp), 
                         str(self.use), str(self.add_reqd)])

    @classmethod
    def to_regexps(cls, use, possibles, add_reqd=False):
        '''
        Convert to regular expressions.
        '''
        regexps = []
        for possible in possibles:
            if isinstance(possible, RegexpContainer):
                cls.log.debug(format('unpacking: {0!s}', possible))
                if add_reqd is None or possible.add_reqd == add_reqd:
                    regexps.append(possible.regexp)
                    # this flag indicates that it's "worth" using the regexp
                    # so we "inherit"
                    use = use or possible.use
                else:
                    raise Unsuitable('Add inconsistent.')
            else:
                cls.log.debug(format('cannot unpack: {0!s}', 
                                     possible.__class__))
                raise Unsuitable('Not a container.')
        return (use, regexps)
        
    @staticmethod
    def to_matcher(possible):
        '''
        Convert to a matcher.
        '''
        if isinstance(possible, RegexpContainer):
            return possible.matcher
        else:
            return possible
        
    @classmethod
    def build(cls, node, regexp, alphabet, matcher_type, use, 
               add_reqd=False, transform=True):
        '''
        Construct a container or matcher.
        '''
        if use and not add_reqd:
            matcher = single(alphabet, node, regexp, matcher_type, transform)
            # if matcher is a Transformable with a Transformation other than
            # the standard empty_adapter then we must stop
            if len(matcher.wrapper.functions) > 1:
                cls.log.debug(format('Force matcher: {0}', matcher.wrapper))
                return matcher
        else:
            matcher = node
        return RegexpContainer(matcher, regexp, use, add_reqd)
        

def single(alphabet, node, regexp, matcher_type, transform=True):
    '''
    Create a matcher for the given regular expression.
    '''
    # avoid dependency loops
    from lepl.matchers.transform import TransformationWrapper
    matcher = matcher_type(regexp, alphabet)
    copy_standard_attributes(node, matcher, describe=False, transform=transform)
    return matcher.precompose(TransformationWrapper(empty_adapter))


def empty_adapter(_stream, matcher):
    '''
    There is a fundamental mismatch between regular expressions and the 
    recursive descent parser on how empty matchers are handled.  The main 
    parser uses empty lists; regexp uses an empty string.  This is a hack
    that converts from one to the other.  I do not see a better solution.
    '''
    (results, stream_out) = matcher()
    if results == ['']:
        results = []
    return (results, stream_out)

        
class Unsuitable(Exception):
    '''
    Exception thrown when a sub-node does not contain a suitable matcher.
    '''
    pass


def make_clone(alphabet, old_clone, matcher_type, use_from_start):
    '''
    Factory that generates a clone suitable for rewriting recursive descent
    to regular expressions.
    '''
    
    # clone functions below take the "standard" clone and the node, and then
    # reproduce the normal argument list of the matcher being cloned.
    # they should return either a container or a matcher.
    
    # Avoid dependency loops
    from lepl.matchers.derived import add
    from lepl.matchers.combine import And, Or, DepthFirst
    from lepl.matchers.core import Any, Literal
    from lepl.matchers.transform import Transformable, Transform, \
        TransformationWrapper

    log = getLogger('lepl.regexp.rewriters.make_clone')
    
    def clone_any(use, original, restrict=None):
        '''
        We can always convert Any() to a regular expression; the only question
        is whether we have an open range or not.
        '''
        if restrict is None:
            char = Character([(alphabet.min, alphabet.max)], alphabet)
        else:
            char = Character(((char, char) for char in restrict), alphabet)
        log.debug(format('Any: cloned {0}', char))
        regexp = Sequence([char], alphabet)
        return RegexpContainer.build(original, regexp, alphabet, 
                                     matcher_type, use)
        
    def clone_or(use, original, *matchers):
        '''
        We can convert an Or only if all the sub-matchers have possible
        regular expressions.
        '''
        assert isinstance(original, Transformable)
        try:
            (use, regexps) = RegexpContainer.to_regexps(use, matchers)
            regexp = Choice(regexps, alphabet)
            log.debug(format('Or: cloned {0}', regexp))
            return RegexpContainer.build(original, regexp, alphabet, 
                                         matcher_type, use)
        except Unsuitable:
            log.debug(format('Or not rewritten: {0}', original))
            return original

    def clone_and(use, original, *matchers):
        '''
        We can convert an And only if all the sub-matchers have possible
        regular expressions, and even then we must tag the result unless
        an add transform is present.
        '''
        assert isinstance(original, Transformable)
        try:
            # since we're going to require add anyway, we're happy to take
            # other inputs, whether add is required or not.
            (use, regexps) = \
                RegexpContainer.to_regexps(use, matchers, add_reqd=None)
            # if we have regexp sub-expressions, join them
            regexp = Sequence(regexps, alphabet)
            log.debug(format('And: cloning {0}', regexp))
            if use and len(original.wrapper.functions) > 1 \
                    and original.wrapper.functions[0] is add:
                # we have additional functions, so cannot take regexp higher,
                # but use is True, so return a new matcher.
                # hack to copy across other functions
                original.wrapper = \
                        TransformationWrapper(original.wrapper.functions[1:])
                log.debug('And: OK (final)')
                # NEED TEST FOR THIS
                return single(alphabet, original, regexp, matcher_type) 
            elif len(original.wrapper.functions) == 1 \
                    and original.wrapper.functions[0] is add:
                # OR JUST ONE?
                # lucky!  we just combine and continue
                log.debug('And: OK')
                return RegexpContainer.build(original, regexp, alphabet, 
                                             matcher_type, use, transform=False)
            elif not original.wrapper:
                # regexp can't return multiple values, so hope that we have
                # an add
                log.debug('And: add required')
                return RegexpContainer.build(original, regexp, alphabet, 
                                             matcher_type, use, add_reqd=True)
            else:
                log.debug(format('And: wrong transformation: {0!r}',
                                 original.wrapper))
                return original
        except Unsuitable:
            log.debug(format('And: not rewritten: {0}', original))
            return original
    
    def clone_transform(use, original, matcher, wrapper, 
                          _raw=False, _args=False):
        '''
        We can assume that wrapper is a transformation.  add joins into
        a sequence.
        '''
        assert isinstance(wrapper, TransformationWrapper)
        try:
            # this is the only place add is required
            (use, [regexp]) = RegexpContainer.to_regexps(use, [matcher], 
                                                         add_reqd=True)
            log.debug(format('Transform: cloning {0}', regexp))
            if use and len(wrapper.functions) > 1 \
                    and wrapper.functions[0] is add:
                # we have additional functions, so cannot take regexp higher,
                # but use is True, so return a new matcher.
                # hack to copy across other functions
                original.wrapper = \
                    TransformationWrapper().extend(wrapper.functions[1:])
                log.debug('Transform: OK (final)')
                # NEED TEST FOR THIS
                return single(alphabet, original, regexp, matcher_type) 
            elif len(wrapper.functions) == 1 and wrapper.functions[0] is add:
                # exactly what we wanted!  combine and continue
                log.debug('Transform: OK')
                return RegexpContainer.build(original, regexp, alphabet, 
                                             matcher_type, use, transform=False)
            elif not wrapper:
                # we're just forwarding the add_reqd from before here
                log.debug('Transform: empty, add required')
                return RegexpContainer(original, regexp, use, add_reqd=True)
            else:
                log.debug(format('Transform: wrong transformation: {0!r}',
                                 original.wrapper))
                return original
        except Unsuitable:
            log.debug(format('Transform: not rewritten: {0}', original))
            return original
        
    def clone_literal(use, original, text):
        '''
        Literal values are easy to transform.
        '''
        chars = [Character([(c, c)], alphabet) for c in text]
        regexp = Sequence(chars, alphabet)
        log.debug(format('Literal: cloned {0}', regexp))
        return RegexpContainer.build(original, regexp, alphabet, 
                                     matcher_type, use)
    
    def clone_dfs(use, original, first, start, stop, rest=None):
        '''
        We only convert DFS if start=0 or 1, stop=1 or None and first and 
        rest are both regexps.
        
        This forces use=True as it is likely that a regexp is a gain.
        '''
        assert not isinstance(original, Transformable)
        try:
            if start not in (0, 1) or stop not in (1, None):
                raise Unsuitable()
            (use, [first, rest]) = \
                    RegexpContainer.to_regexps(True, [first, rest])
            # we need to be careful here to get the depth first bit right
            if stop is None:
                regexp = Sequence([first, Repeat([rest], alphabet)], alphabet)
                if start == 0:
                    regexp = Choice([regexp, Empty(alphabet)], alphabet)
            else:
                regexp = first
                if start == 0:
                    regexp = Choice([regexp, Empty(alphabet)], alphabet)
            log.debug(format('DFS: cloned {0}', regexp))
            return RegexpContainer.build(original, regexp, alphabet, 
                                         matcher_type, use, 
                                         add_reqd=stop is None)
        except Unsuitable:
            log.debug(format('DFS: not rewritten: {0}', original))
            return original
        
    def clone_wrapper(use, original, *args, **kargs):
        factory = original.factory
        if factory in map_:
            log.debug(format('Found {0}', factory))
            return map_[factory](use, original, *args, **kargs)
        else:
            log.debug(format('No clone for {0}, {1}', factory, map_.keys()))
            return original
        
    map_ = matcher_map({Any: clone_any, 
                        Or: clone_or, 
                        And: clone_and,
                        Transform: clone_transform,
                        Literal: clone_literal,
                        DepthFirst: clone_dfs,
                        FunctionWrapper: clone_wrapper,
                        SequenceWrapper: clone_wrapper,
                        TrampolineWrapper: clone_wrapper,
                        TransformableTrampolineWrapper: clone_wrapper})
    
    def clone_(node, args, kargs):
        '''
        Do the cloning, dispatching by type to the methods above.
        '''
        original_args = [RegexpContainer.to_matcher(arg) for arg in args]
        original_kargs = dict((name, RegexpContainer.to_matcher(kargs[name]))
                              for name in kargs)
        original = old_clone(node, original_args, original_kargs)
        type_ = type(node)
        if type_ in map_:
            # pylint: disable-msg=W0142
            return map_[type_](use_from_start, original, *args, **kargs)
        else:
            return original

    return clone_


class CompileRegexp(Rewriter):
    '''
    A rewriter that uses the given alphabet and matcher to compile simple
    matchers.
    
    The "use" parameter controls when regular expressions are substituted.
    If true, they are always used.  If false, they are used only if they
    are part of a tree that includes repetition.  The latter case generally
    gives more efficient parsers because it avoids converting already
    efficient literal matchers to regular expressions.
    '''
    
    def __init__(self, alphabet=None, use=True, matcher=NfaRegexp):
        if alphabet is None:
            alphabet = UnicodeAlphabet.instance()
        super(CompileRegexp, self).__init__(Rewriter.COMPILE_REGEXP,
            format('CompileRegexp({0}, {1}, {2})', alphabet, use, matcher))
        self.alphabet = alphabet
        self.use = use
        self.matcher = matcher
        
    def __call__(self, graph):
        new_clone = make_clone(self.alphabet, clone, self.matcher, self.use)
        graph = graph.postorder(DelayedClone(new_clone), Matcher)
        if isinstance(graph, RegexpContainer):
            graph = graph.matcher
        return graph 
