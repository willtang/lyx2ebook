
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
Rewriters modify the graph of matchers before it is used to generate a 
parser.
'''

from lepl.support.graph import Visitor, preorder, loops, order, NONTREE, \
    dfs_edges, LEAF
from lepl.matchers.combine import DepthFirst, DepthNoTrampoline, \
    BreadthFirst, BreadthNoTrampoline, And, AndNoTrampoline, \
    Or, OrNoTrampoline
from lepl.matchers.core import Delayed
from lepl.matchers.matcher import Matcher, is_child, FactoryMatcher, \
    matcher_type, MatcherTypeException, matcher_map
from lepl.matchers.support import NoTrampolineTransformableWrapper
from lepl.support.lib import lmap, format, LogMixin


class Rewriter(LogMixin):
    
    # ordering
    SET_ARGUMENTS = 10
    FULL_FIRST_MATCH = 20
    FLATTEN = 30
    COMPILE_REGEXP = 40
    OPTIMIZE_OR = 50
    LEXER = 60
    COMPOSE_TRANSFORMS = 70
    DIRECT_EVALUATION = 80
    MEMOIZE = 90
       
    def __init__(self, order, name=None, exclusive=True):
        super(Rewriter, self).__init__()
        self.order = order
        self.name = name if name else self.__class__.__name__
        self.exclusive = exclusive
        
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.exclusive or self is other
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        if self.exclusive:
            return hash(self.__class__)
        else:
            return super(Rewriter, self).__hash__()
        
    def __lt__(self, other):
        if not isinstance(other, Rewriter):
            return True
        elif self.exclusive or self.order != other.order:
            return self.order < other.order
        else:
            return hash(self) < hash(other)
            
    def __ge__(self, other):
        return not self.__lt__(other)
    
    def __gt__(self, other):
        if not isinstance(other, Rewriter):
            return True
        elif self.exclusive or self.order != other.order:
            return self.order > other.order
        else:
            return hash(self) > hash(other)

    def __le__(self, other):
        return not self.__gt__(other)
    
    def __call__(self, matcher):
        return matcher
    
    def __str__(self):
        return self.name
    
    
def clone(node, args, kargs):
    '''
    Clone including matcher-specific attributes.
    '''
    from lepl.support.graph import clone as old_clone
    copy = old_clone(node, args, kargs)
    copy_standard_attributes(node, copy)
    return copy


def copy_standard_attributes(node, copy, describe=True, transform=True):
    '''
    Handle the additional attributes that matchers may have.
    '''
    from lepl.matchers.support import Transformable
    if isinstance(node, Transformable) and transform:
        copy.wrapper = node.wrapper
    if isinstance(node, FactoryMatcher):
        copy.factory = node.factory


class DelayedClone(Visitor):    
    '''
    A version of `Clone()` that uses `Delayed()` rather
    that `Proxy()` to handle circular references.  Also caches results to
    avoid duplications.
    '''
    
    def __init__(self, clone_=clone):
        super(DelayedClone, self).__init__()
        self._clone = clone_
        self._visited = {}
        self._loops = set()
        self._node = None
    
    def loop(self, node):
        '''
        This is called for nodes that are involved in cycles when they are
        needed as arguments but have not themselves been cloned.
        '''
        # delayed import to avoid dependency loops
        from lepl.matchers.core import Delayed
        if node not in self._visited:
            self._visited[node] = Delayed()
            self._loops.add(node)
        return self._visited[node]
    
    def node(self, node):
        '''
        Store the current node.
        '''
        self._node = node
        
    def constructor(self, *args, **kargs):
        '''
        Clone the node, taking care to handle loops.
        '''
        # delayed import to avoid dependency loops
        if self._node not in self._visited:
            self._visited[self._node] = self.__clone_node(args, kargs)
        # if this is one of the loops we replaced with a delayed instance,
        # then we need to patch the delayed matcher
        elif self._node in self._loops and \
                not self._visited[self._node].matcher:
            self._visited[self._node] += self.__clone_node(args, kargs)
        return self._visited[self._node]
    
    def __clone_node(self, args, kargs):
        '''
        Before cloning, drop any Delayed from args and kargs.  Afterwards,
        check if this is a Delaed instance and, if so, return the contents.
        This helps keep the number of Delayed instances from exploding.
        '''
        args = lmap(self.__drop, args)
        kargs = dict((key, self.__drop(kargs[key])) for key in kargs)
        return self.__drop(self._clone(self._node, args, kargs))
    
    @staticmethod
    def __drop(node):
        '''
        Filter `Delayed` instances where possible (if they have the matcher
        defined and are nor transformed).
        '''
        # delayed import to avoid dependency loops
        from lepl.matchers.core import Delayed
        from lepl.matchers.transform import Transformable
        if isinstance(node, Delayed) and node.matcher and \
                not (isinstance(node, Transformable) and node.wrapper):
            return node.matcher
        else:
            return node
    
    def leaf(self, value):
        '''
        Leaf values are unchanged.
        '''
        return value
    
    
def post_clone(function):
    '''
    Generate a clone function that applies the given function to the newly
    constructed node, except for Delayed instances (which are effectively
    proxies and so have no functionality of their own) (so, when used with 
    `DelayedClone`, effectively performs a map on the graph).
    '''
    from lepl.matchers.core import Delayed
    def new_clone(node, args, kargs):
        '''
        Apply function as well as clone.
        '''
        copy = clone(node, args, kargs)
        # ignore Delayed since that would (1) effectively duplicate the
        # action and (2) they come and go with each cloning.
        if not isinstance(node, Delayed):
            copy = function(copy)
        return copy
    return new_clone


class Flatten(Rewriter):
    '''
    A rewriter that flattens `And` and `Or` lists.
    '''
    
    def __init__(self):
        super(Flatten, self).__init__(Rewriter.FLATTEN)
    
    def __call__(self, graph):
        from lepl.matchers.combine import And, Or
        def new_clone(node, old_args, kargs):
            '''
            The flattening cloner.
            '''
            table = matcher_map({And: '*matchers', Or: '*matchers'})
            new_args = []
            type_ = matcher_type(node, fail=False)
            if type_ in table:
                attribute_name = table[type_]
                for arg in old_args:
                    if matcher_type(arg, fail=False) is type_ \
                            and not arg.wrapper \
                            and not node.wrapper:
                        if attribute_name.startswith('*'):
                            new_args.extend(getattr(arg, attribute_name[1:]))
                        else:
                            new_args.append(getattr(arg, attribute_name))
                    else:
                        new_args.append(arg)
            if not new_args:
                new_args = old_args
            return clone(node, new_args, kargs)
        return graph.postorder(DelayedClone(new_clone), Matcher)
    

class ComposeTransforms(Rewriter):
    '''
    A rewriter that joins adjacent transformations into a single
    operation, avoiding trampolining in some cases.
    '''

    def __init__(self):
        super(ComposeTransforms, self).__init__(Rewriter.COMPOSE_TRANSFORMS)
        
    def __call__(self, graph):
        from lepl.matchers.transform import Transform, Transformable
        def new_clone(node, args, kargs):
            '''
            The joining cloner.
            '''
            # must always clone to expose the matcher (which was cloned earlier - 
            # it is not node.matcher)
            copy = clone(node, args, kargs)
            if isinstance(copy, Transform) \
                    and isinstance(copy.matcher, Transformable):
                return copy.matcher.compose(copy.wrapper)
            else:
                return copy
        return graph.postorder(DelayedClone(new_clone), Matcher)


class Memoize(Rewriter):
    '''
    A rewriter that adds the given memoizer to all nodes in the matcher
    graph.
    '''
    
    def __init__(self, memoizer):
        super(Memoize, self).__init__(Rewriter.MEMOIZE,
                                      format('Memoize({0})', memoizer.__name__))
        self.memoizer = memoizer
        
    def __call__(self, graph):
        return graph.postorder(DelayedClone(post_clone(self.memoizer)), Matcher)


class AutoMemoize(Rewriter):
    '''
    Apply two different memoizers, one to left recursive loops and the
    other elsewhere (either can be omitted).
    
    `conservative` refers to the algorithm used to detect loops; False
    may classify some left--recursive loops as right--recursive.
    '''
    
    def __init__(self, conservative=False, left=None, right=None):
        super(AutoMemoize, self).__init__(Rewriter.MEMOIZE,
            format('AutoMemoize({0}, {1}, {2})', conservative, left, right))
        self.conservative = conservative
        self.left = left
        self.right = right

    def __call__(self, graph):
        dangerous = set()
        for head in order(graph, NONTREE, Matcher):
            for loop in either_loops(head, self.conservative):
                for node in loop:
                    dangerous.add(node)
        def new_clone(node, args, kargs):
            '''
            Clone with the appropriate memoizer 
            (cannot use post_clone as need to test original)
            '''
            copy = clone(node, args, kargs)
            if isinstance(node, Delayed):
                # no need to memoize the proxy (if we do, we also break 
                # rewriting, since we "hide" the Delayed instance)
                return copy
            elif node in dangerous:
                if self.left:
                    return self.left(copy)
                else:
                    return copy
            else:
                if self.right:
                    return self.right(copy)
                else:
                    return copy
        return graph.postorder(DelayedClone(new_clone), Matcher)


def left_loops(node):
    '''
    Return (an estimate of) all left-recursive loops from the given node.
    
    We cannot know for certain whether a loop is left recursive because we
    don't know exactly which parsers will consume data.  But we can estimate
    by assuming that all matchers eventually (ie via their children) consume
    something.  We can also improve that slightly by ignoring `Lookahead`.
    
    So we estimate left-recursive loops as paths that start and end at
    the given node, and which are first children of intermediate nodes
    unless the node is `Or`, or the preceding matcher is a
    `Lookahead`.  
    
    Each loop is a list that starts and ends with the given node.
    '''
    from lepl.matchers.combine import Or
    from lepl.matchers.core import Lookahead
    stack = [[node]]
    known = set([node]) # avoid getting lost in embedded loops
    while stack:
        ancestors = stack.pop()
        parent = ancestors[-1]
        if isinstance(parent, Matcher):
            for child in parent:
                family = list(ancestors) + [child]
                if child is node:
                    yield family
                else:
                    if child not in known:
                        stack.append(family)
                        known.add(child)
                if not is_child(parent, Or, fail=False) and \
                        not is_child(child, Lookahead, fail=False):
                    break
    
                    
def either_loops(node, conservative):
    '''
    Select between the conservative and liberal loop detection algorithms.
    '''
    if conservative:
        return loops(node, Matcher)
    else:
        return left_loops(node)
    

class OptimizeOr(Rewriter):
    '''
    A rewriter that re-arranges `Or` matcher contents for left--recursive 
    loops.
    
    When a left-recursive rule is used, it is much more efficient if it
    appears last in an `Or` statement, since that forces the alternates
    (which correspond to the terminating case in a recursive function)
    to be tested before the LMemo limit is reached.
    
    This rewriting may change the order in which different results for
    an ambiguous grammar are returned.
    
    `conservative` refers to the algorithm used to detect loops; False
    may classify some left--recursive loops as right--recursive.
    '''
    
    def __init__(self, conservative=True):
        super(OptimizeOr, self).__init__(Rewriter.OPTIMIZE_OR)
        self.conservative = conservative

    def __call__(self, graph):
        from lepl.matchers.core import Delayed
        from lepl.matchers.combine import Or
        for delayed in [x for x in preorder(graph, Matcher) 
                        if isinstance(x, Delayed)]:
            for loop in either_loops(delayed, self.conservative):
                for i in range(len(loop)):
                    if is_child(loop[i], Or, fail=False):
                        # we cannot be at the end of the list here, since that
                        # is a Delayed instance
                        # copy from tuple to list
                        loop[i].matchers = list(loop[i].matchers)
                        matchers = loop[i].matchers
                        target = loop[i+1]
                        # move target to end of list
                        index = matchers.index(target)
                        del matchers[index]
                        matchers.append(target)
        return graph


class SetArguments(Rewriter):
    '''
    Add/replace named arguments while cloning.
    
    This rewriter is not exclusive - several different instances canb be
    defined in parallel.
    '''
    
    def __init__(self, type_, **extra_kargs):
        super(SetArguments, self).__init__(Rewriter.SET_ARGUMENTS,
            format('SetArguments({0}, {1})', type_, extra_kargs), False)
        self.type = type_
        self.extra_kargs = extra_kargs
        
    def __call__(self, graph):
        def new_clone(node, args, kargs):
            '''
            As clone, but add in any extra kargs if the node is an instance
            of the given type.
            '''
            if isinstance(node, self.type):
                for key in self.extra_kargs:
                    kargs[key] = self.extra_kargs[key]
            return clone(node, args, kargs)
        return graph.postorder(DelayedClone(new_clone), Matcher)


class DirectEvaluation(Rewriter):
    '''
    Replace given matchers if all Matcher arguments are subclasses of
    `NoTrampolineTransformableWrapper`
    
    `spec` is a map from original matcher type to the replacement.
    '''
    
    def __init__(self, spec=None):
        super(DirectEvaluation, self).__init__(Rewriter.DIRECT_EVALUATION,
            format('DirectEvaluation({0})', spec))
        if spec is None:
            spec = {DepthFirst: DepthNoTrampoline,
                    BreadthFirst: BreadthNoTrampoline,
                    And: AndNoTrampoline,
                    Or: OrNoTrampoline}
        self.spec = spec

    def __call__(self, graph):
        def new_clone(node, args, kargs):
            type_, ok = None, False
            for parent in self.spec:
                if is_child(node, parent):
                    type_ = self.spec[parent]
            if type_:
                ok = True
                for arg in args:
                    if isinstance(arg, Matcher) and not \
                            isinstance(arg, NoTrampolineTransformableWrapper):
                        ok = False
                for name in kargs:
                    arg = kargs[name]
                    if isinstance(arg, Matcher) and not \
                            isinstance(arg, NoTrampolineTransformableWrapper):
                        ok = False
            if not ok:
                type_ = type(node)
            try:
                copy = type_(*args, **kargs)
                copy_standard_attributes(node, copy)
                return copy
            except TypeError as err:
                raise TypeError(format('Error cloning {0} with ({1}, {2}): {3}',
                                       type_, args, kargs, err))
        return graph.postorder(DelayedClone(new_clone), Matcher)
    
    
class FullFirstMatch(Rewriter):
    '''
    If the parser fails, raise an error at the maxiumum depth.
    
    `eos` controls whether or not the entire input must be consumed for the
    parse to be considered a success. 
    '''
    
    def __init__(self, eos=False):
        super(FullFirstMatch, self).__init__(Rewriter.FULL_FIRST_MATCH,
                                       format('FullFirstMatch({0})', eos))
        self.eos = eos
        
    def __call__(self, graph):
        from lepl.stream.maxdepth import FullFirstMatch
        return FullFirstMatch(graph, self.eos)


class NodeStats(object):
    '''
    Provide statistics and access by type to nodes.
    '''
    
    def __init__(self, matcher=None):
        self.loops = 0
        self.leaves = 0
        self.total = 0
        self.others = 0
        self.duplicates = 0
        self.unhashable = 0
        self.types = {}
        self.__known = set()
        if matcher is not None:
            self.add_all(matcher)
        
    def add(self, type_, node):
        '''
        Add a node of a given type.
        '''
        try:
            node_type = matcher_type(node)
        except MatcherTypeException:
            node_type = type(node)
        if type_ & LEAF:
            self.leaves += 1
        if type_ & NONTREE and is_child(node_type, Matcher, fail=False):
            self.loops += 1
        try:
            if node not in self.__known:
                self.__known.add(node)
                if node_type not in self.types:
                    self.types[node_type] = set()
                self.types[node_type].add(node)
                if is_child(node_type, Matcher):
                    self.total += 1
                else:
                    self.others += 1
            else:
                self.duplicates += 1
        except:
            self.unhashable += 1
            
    def add_all(self, matcher):
        '''
        Add all nodes.
        '''
        for (_parent, child, type_) in dfs_edges(matcher, Matcher):
            self.add(type_, child)

    def __str__(self):
        counts = format('total:      {total:3d}\n'
                        'leaves:     {leaves:3d}\n'
                        'loops:      {loops:3d}\n'
                        'duplicates: {duplicates:3d}\n'
                        'others:     {others:3d}\n'
                        'unhashable: {unhashable:3d}\n', **self.__dict__)
        keys = list(self.types.keys())
        keys.sort(key=repr)
        types = '\n'.join([format('{0:40s}: {1:3d}', key, len(self.types[key]))
                           for key in keys])
        return counts + types
