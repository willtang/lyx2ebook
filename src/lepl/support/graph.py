
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
Graph traversal - supports generic Python classes, but has extensions for 
classes that record their own constructor arguments (and so allow deep 
cloning of graphs). 

The fundamental `dfs_edges` routine will traverse over (ie provides an iterator 
that returns (flag, node) pairs, where flag describes the type of node and 
ordering) a graph made of iterable Python objects.  Only the __iter__ method
(implemented by all containers) is required.  However, in general this is too
broad (for example, Strings are iterable, and single character strings contain 
themselves), so a type can be specified which identifies those nodes to
be treated as "interior" nodes.   Children of interior nodes are returned as
"leaf" nodes, but are not iterated over themselves.

The `order` function provides a simpler interface to this traversal, allowing
a particular order to be generated, and, for example, optionally excluding leaf
nodes.

`ConstructorGraphNode` is motivated by data constructors and exposes its 
constructor arguments (this is important because if we are cloning a graph 
we want to replace constructor arguments that correspond to child nodes with 
their clones).  This currently has a single implementation, 
`ArgAsAttributeMixin` (there used to be another, but it was equivalent to
the generic case with `SimpleWalker`).

The 'Walker' (`SimpleWalker` and `ConstructorWalker`) and `Visitor` classes
provide a different approach to traversing the graph (compared to the simple
sequences of nodes provided by `dfs_edges` et al), that reflects the emphasis
on constructors described above: the walker takes a visitor sub-class and 
calls it in a way that replicates the original calls to the node constructors.
'''

from collections import Sequence, deque

from lepl.support.lib import compose, safe_in, safe_add, empty, format


FORWARD = 1    # forward edge
BACKWARD = 2   # backward edge
NONTREE = 4    # cyclic edge
ROOT = 8       # root node (not an edge)
NODE = 16      # child is a 'normal' node (of the given type)
LEAF = 32      # child is a leaf node (not the given type)

POSTORDER = BACKWARD | NONTREE
PREORDER = FORWARD | NONTREE


# pylint: disable-msg=R0911
# many yields appropriate here
def dfs_edges(node, type_):
    '''
    Iterative DFS, based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
    
    Returns forward and reverse edges.  Also returns root node in correct 
    order for pre- (FORWARD) and post- (BACKWARD) ordering.

    ``type_`` selects which values are iterated over.  Children which are
    not of this type are flagged with LEAF.
    '''
    while isinstance(node, type_):
        try:
            stack = [(node, iter(node), ROOT)]
            yield node, node, FORWARD | ROOT
            visited = set()
            safe_add(visited, node) # cannot track loops in unhashable objects
            while stack:
                parent, children, ptype = stack[-1]
                try:
                    child = next(children)
                    if isinstance(child, type_):
                        if safe_in(child, visited, False):
                            yield parent, child, NONTREE
                        else:
                            stack.append((child, iter(child), NODE))
                            yield parent, child, FORWARD | NODE
                            safe_add(visited, child)
                    else:
                        stack.append((child, empty(), LEAF))
                        yield parent, child, FORWARD | LEAF
                except StopIteration:
                    stack.pop()
                    if stack:
                        yield stack[-1][0], parent, BACKWARD | ptype
            yield node, node, BACKWARD | ROOT
            return
        except Reset:
            yield # in response to the throw (ignored by caller)


class Reset(Exception):
    '''
    An exception that can be passed to dfs_edges to reset the traversal.
    '''
    pass


def reset(generator):
    '''
    Reset the traversal by raising Reset.
    '''
    generator.throw(Reset())
    

def order(node, include, type_, exclude=0):
    '''
    An ordered sequence of nodes.  The ordering is given by 'include' (see
    the constants PREORDER etc above).
    '''
    while True:
        try:
            for (_parent, child, direction) in dfs_edges(node, type_):
                if (direction & include) and not (direction & exclude):
                    yield child
            return
        except Reset:
            yield # in response to the throw (ignored by caller)
            

def preorder(node, type_, exclude=0):
    '''
    The nodes in preorder.
    '''
    return order(node, PREORDER, type_, exclude=exclude)


def postorder(node, type_, exclude=0):
    '''
    The nodes in postorder.
    '''
    return order(node, POSTORDER, type_, exclude=exclude)


def leaves(node, type_=None):
    '''
    The leaf nodes.
    '''
    if type_ is None:
        type_ = type(node)
    return order(node, FORWARD, type_, exclude=NODE|ROOT)


def loops(node, type_):
    '''
    Return all loops from the given node.
    
    Each loop is a list that starts and ends with the given node.
    '''
    stack = [[node]]
    known = set([node]) # avoid getting lost in sub-loops
    while stack:
        ancestors = stack.pop()
        parent = ancestors[-1]
        if isinstance(parent, type_):
            for child in parent:
                family = list(ancestors)
                family.append(child)
                if child is node:
                    yield family
                else:
                    if not safe_in(child, known):
                        stack.append(family)
                        safe_add(known, child)


# pylint: disable-msg=R0903
# interface
class ConstructorGraphNode(object):
    '''
    An interface that provides information on constructor arguments.
    
    This is used by `ConstructorWalker` to provide the results of
    walking child nodes in the same format as those nodes were provided in
    the constructor.  The main advantage is that the names of named
    arguments are associated with the appropriate results.
    
    For this to work correctly there is assumed to be a close relationship 
    between constructor arguments and children  (there is a somewhat implicit 
    link between Python object constructors and type constructors in, say, 
    Haskell).  Exactly how constructor argmuents and children match depends
    on the implementation, but `ConstructorWalker` assumes that child
    nodes (from __iter__()) are visited before the same nodes appear in
    constructor arguments during depth-first postorder traversal.
    '''

    # pylint: disable-msg=R0201
    # interface
    def _constructor_args(self):
        '''
        Regenerate the constructor arguments (returns (args, kargs)).
        '''
        raise Exception('Not implemented')
    

class ArgAsAttributeMixin(ConstructorGraphNode):
    '''
    Constructor arguments are stored as attributes; their names are also
    stored in order so that the arguments can be constructed.  This assumes
    that all names are unique.  '*args' are named "without the *".
    '''
    
    def __init__(self):
        super(ArgAsAttributeMixin, self).__init__()
        self.__arg_names = []
        self.__karg_names = []

    def __set_attribute(self, name, value):
        '''
        Add a single argument as a simple property.
        '''
        setattr(self, name, value)
        return name
            
    def _arg(self, **kargs):
        '''
        Set a single named argument as an attribute (the signature uses kargs
        so that the name does not need to be quoted).  The attribute name is
        added to self.__arg_names.
        '''
        assert len(kargs) == 1
        for name in kargs:
            self.__arg_names.append(self.__set_attribute(name, kargs[name]))
        
    def _karg(self, **kargs):
        '''
        Set a single keyword argument (ie with default) as an attribute (the 
        signature uses kargs so that the name does not need to be quoted).  
        The attribute name is added to self.__karg_names.
        '''
        assert len(kargs) == 1
        for name in kargs:
            self.__karg_names.append(self.__set_attribute(name, kargs[name]))
      
    def _args(self, **kargs):
        '''
        Set a *arg as an attribute (the signature uses kargs so that the 
        attribute name does not need to be quoted).  The name (without '*')
        is added to self.__arg_names.
        '''
        assert len(kargs) == 1
        for name in kargs:
            assert isinstance(kargs[name], Sequence), kargs[name] 
            self.__arg_names.append('*' + 
                                    self.__set_attribute(name, kargs[name]))
        
    def _kargs(self, kargs):
        '''
        Set **kargs as attributes.  The attribute names are added to 
        self.__arg_names.
        '''
        for name in kargs:
            self.__karg_names.append(self.__set_attribute(name, kargs[name]))
        
    def __args(self):
        '''
        All (non-keyword) arguments.
        '''
        args = [getattr(self, name)
                for name in self.__arg_names if not name.startswith('*')]
        for name in self.__arg_names:
            if name.startswith('*'):
                args.extend(getattr(self, name[1:]))
        return args
        
    def __kargs(self):
        '''
        All keyword argmuents.
        '''
        return dict((name, getattr(self, name)) for name in self.__karg_names)
        
    def _constructor_args(self):
        '''
        Regenerate the constructor arguments.
        '''
        return (self.__args(), self.__kargs())
    
    def __iter__(self):
        '''
        Return all children, in order.
        '''
        for arg in self.__args():
            yield arg
        for name in self.__karg_names:
            yield getattr(self, name)


class Visitor(object):
    '''
    The interface required by the walkers.
    
    ``loop`` is value returned when a node is re-visited.
    
    ``type_`` is set with the node type before constructor() is called.  This
    allows constructor() itself to be invoked with the Python arguments used to
    construct the original graph.
    '''
    
    def loop(self, value):
        '''
        Called on nodes that belong to a loop (eg. in the `ConstructorWalker`
        nodes are visited in postorder, and this is called when a node is
        *first* found as a constructor argument (before bing found in the
        "postorder" traversal)).
        
        By default, do nothing.
        '''
        pass
    
    def node(self, node):
        '''
        Called when first visiting a node.
        
        By default, do nothing.
        '''
        pass
        
    def constructor(self, *args, **kargs):
        '''
        Called for node instances.  The args and kargs are the values for
        the corresponding child nodes, as returned by this visitor.
        
        By default, do nothing.
        '''
        pass
    
    def leaf(self, value):
        '''
        Called for children that are not node instances.
        
        By default, do nothing.
        '''
        pass
    
    # pylint: disable-msg=R0201
    # interface
    def postprocess(self, result):
        '''
        Called after walking, passed the match to the initial node.
        '''
        return result


class ConstructorWalker(object):
    '''
    Tree walker (it handles cyclic graphs by ignoring repeated nodes).
    
    This is based directly on the catamorphism of the graph.  The visitor 
    encodes the type information.  It may help to see the constructor 
    arguments as type constructors.
    
    Nodes should be subclasses of `ConstructorGraphNode`.
    '''
    
    def __init__(self, root, type_):
        self.__root = root
        self.__type = type_
        
    def __call__(self, visitor):
        '''
        Apply the visitor to each node in turn.
        '''
        results = {}
        for node in postorder(self.__root, self.__type, exclude=LEAF):
            visitor.node(node)
            (args, kargs) = self.__arguments(node, visitor, results)
            # pylint: disable-msg=W0142
            results[node] = visitor.constructor(*args, **kargs)
        return visitor.postprocess(results[self.__root])
    
    def __arguments(self, node, visitor, results):
        '''
        Collect arguments for the constructor.
        '''
        # pylint: disable-msg=W0212
        # (this is the ConstructorGraphNode interface; it's purposefully
        # like that to avoid conflicting with Node attributes)
        (old_args, old_kargs) = node._constructor_args()
        (new_args, new_kargs) = ([], {})
        for arg in old_args:
            new_args.append(self.__value(arg, visitor, results))
        for name in old_kargs:
            new_kargs[name] = self.__value(old_kargs[name], visitor, results)
        return (new_args, new_kargs)
    
    def __value(self, node, visitor, results):
        '''
        Get a value for a particular constructor argument.
        '''
        if isinstance(node, self.__type):
            if node in results:
                return results[node]
            else:
                return visitor.loop(node)
        else:
            return visitor.leaf(node)
    
        
class SimpleWalker(object):
    '''
    This works like `ConstructorWalker` for generic classes.
    Since it has no knowledge of constructor arguments it assumes that all
    children are passed like '*args'.
    
    This allows visitors written for `ConstructorGraphNode` trees to be
    used with arbitrary objects (as long as they follow the convention
    described above).
    '''
    
    def __init__(self, root, type_):
        '''
        Create a walker for the graph starting at the given node.
        '''
        self.__root = root
        self.__type = type_
        
    def __call__(self, visitor):
        '''
        Apply the visitor to the nodes in the graph, in postorder.
        '''
        # pylint: disable-msg=W0142
        # (*args)
        pending = {}
        for (parent, node, kind) in dfs_edges(self.__root, self.__type):
            if kind & POSTORDER:
                if safe_in(node, pending):
                    args = pending[node]
                    del pending[node]
                else:
                    args = []
                if parent not in pending:
                    pending[parent] = []
                visitor.node(node)
                if kind & LEAF:
                    pending[parent].append(visitor.leaf(node))
                elif kind & NONTREE:
                    pending[parent].append(visitor.loop(node))
                else:
                    pending[parent].append(visitor.constructor(*args))
        return pending[self.__root][0]
    
                
class PostorderWalkerMixin(object):
    '''
    Add a 'postorder' method.
    '''
    
    def __init__(self):
        super(PostorderWalkerMixin, self).__init__()
        self.__postorder = None
        self.__postorder_type = None
        
    def postorder(self, visitor, type_):
        '''
        A shortcut that allows a visitor to be applied postorder.
        '''
        if self.__postorder is None or self.__postorder_type != type_:
            self.__postorder = ConstructorWalker(self, type_)
            self.__postorder_type = type_
        return self.__postorder(visitor)


class _LineOverflow(Exception):
    '''
    Used internally in `ConstructorStr`.
    '''
    pass


class ConstructorStr(Visitor):
    '''
    Reconstruct the constructors used to generate the graph as a string
    (useful for repr).
    
    Internally, data is stored as a list of (indent, line) pairs.
    '''
    
    def __init__(self, line_length=80):
        super(ConstructorStr, self).__init__()
        self.__line_length = line_length
        self.__name = None
        
    def node(self, node):
        '''
        Store the node's class name for later use.
        '''
        # TODO - clean this up
        try:
            self.__name = node.delegate.__class__.__name__
        except AttributeError:
            self.__name = node.__class__.__name__
        
    def loop(self, value):
        '''
        Replace loop nodes by a <loop> marker.
        '''
        return [[0, '<loop>']]
    
    def constructor(self, *args, **kargs):
        '''
        Build the constructor string, given the node and arguments.
        '''
        contents = []
        for arg in args:
            if contents:
                contents[-1][1] += ', '
            contents.extend([indent+1, line] for (indent, line) in arg)
        for name in kargs:
            if contents:
                contents[-1][1] += ', '
            arg = kargs[name]
            contents.append([arg[0][0]+1, name + '=' + arg[0][1]])
            contents.extend([indent+1, line] for (indent, line) in arg[1:])
        lines = [[0, self.__name + '(']] + contents
        lines[-1][1] += ')'
        return lines
    
    def leaf(self, value):
        '''
        Non-node nodes (attributes) are displayed using repr.
        '''
        return [[0, repr(value)]]

    def postprocess(self, lines):
        '''
        This is an ad-hoc algorithm to make the final string reasonably
        compact.  It's ugly, bug-prone and completely arbitrary, but it 
        seems to work....
        '''
        sections = deque()
        (scan, indent) = (0, -1)
        while scan < len(lines):
            (i, _) = lines[scan]
            if i > indent:
                indent = i
                sections.append((indent, scan))
            elif i < indent:
                (scan, indent) = self.__compress(lines, sections.pop()[1], scan)
            scan = scan + 1
        while sections:
            self.__compress(lines, sections.pop()[1], len(lines))
        return self.__format(lines)
    
    def __compress(self, lines, start, stop):
        '''
        Try a compact version first.
        '''
        try:
            return self.__all_on_one_line(lines, start, stop)
        except _LineOverflow:
            return self.__bunch_up(lines, start, stop)
        
    def __bunch_up(self, lines, start, stop):
        '''
        Scrunch adjacent lines together.
        '''
        (indent, _) = lines[start]
        while start+1 < stop:
            if indent == lines[start][0] and \
                    (start+1 >= stop or indent == lines[start+1][0]) and \
                    (start+2 >= stop or indent == lines[start+2][0]) and \
                    indent + len(lines[start][1]) + len(lines[start+1][1]) < \
                        self.__line_length:
                lines[start][1] += lines[start+1][1]
                del lines[start+1]
                stop -= 1
            else:
                start += 1
        return (stop, indent-1)

    def __all_on_one_line(self, lines, start, stop):
        '''
        Try all on one line.
        '''
        if start == 0:
            raise _LineOverflow()
        (indent, text) = lines[start-1]
        size = indent + len(text) 
        for (_, extra) in lines[start:stop]:
            size += len(extra)
            if size > self.__line_length:
                raise _LineOverflow()
            text += extra
        lines[start-1] = [indent, text]
        del lines[start:stop]
        return (start-1, indent)

    @staticmethod
    def __format(lines):
        '''
        Join lines together, given the indent.
        '''
        return '\n'.join(' ' * indent + line for (indent, line) in lines)
                
                
class GraphStr(Visitor):
    '''
    Generate an ASCII graph of the nodes.
    
    This should be used with `ConstructorWalker` and works rather like
    cloning, except that instead of generating a new set of nodes we
    generate a nested set of functions.  This set of functions has the
    same structure as the tree of nodes (we break cycles via loop).
    The leaf functions take prefixes and return an ASCII picture of
    what the leaf values should look like (including the prefixes).
    Functions higher up the tree are similar, except instead of returning
    a picture directly they extend the prefix and then call the functions
    that are their children.
    
    Once we have an entire tree of functions, we can call the root with
    an empty prefix and the functions will "cascade" down, building the
    prefixes necessary and passing them to the root functions that
    generate the final ASCII data.
    '''
    
    def __init__(self):
        super(GraphStr, self).__init__()
        self.__type = None
    
    def loop(self, value):
        '''
        Mark loops (what else could we do?)
        '''
        return lambda first, rest, name: \
            [first + name + (' ' if name else '') + '<loop>']
    
    def node(self, node):
        '''
        Store the class name.
        '''
        self.__type = node.__class__.__name__
    
    def constructor(self, *args, **kargs):
        '''
        Generate a function that can construct the local section of the
        graph when given the appropriate prefixes.
        '''
        def fun(first, rest, name, type_=self.__type):
            '''
            Build the ASCII picture; this is rather terse...  First is the
            prefix to the first line; rest is the prefix to the rest.  Args
            and Kargs are the equivalent functions for the constructor
            arguments; we evaluate them here as we "expend" the ASCII
            picture.
            '''
            spec = []
            for arg in args:
                spec.append((' +- ', ' |  ', '', arg))
            for arg in kargs:
                spec.append((' +- ', ' |  ', arg, kargs[arg]))
            # fix the last branch
            if spec:
                spec[-1] = (' `- ', '    ', spec[-1][2], spec[-1][3])
            yield first + name + (' ' if name else '') + type_
            for (first_, rest_, name_, fun_) in spec:
                for line in fun_(first_, rest_, name_):
                    yield rest + line
        return fun
    
    def leaf(self, value):
        '''
        Generate a function that can construct the local section of the
        graph when given the appropriate prefixes.
        '''
        return lambda first, rest, name: \
            [first + name + (' ' if name else '') + repr(value)]
    
    def postprocess(self, fun):
        '''
        Invoke the functions generated above and join the resulting lines.
        '''
        return '\n'.join(fun('', '', ''))
    

class Proxy(object):
    '''
    A simple proxy that allows us to re-construct cyclic graphs.  Used via
    `make_proxy`.
    
    Note - this is only used locally (in this module).  When cloning LEPL
    matcher graphs a different approach is used, based on `Delayed`. 
    '''
    
    def __init__(self, mutable_delegate):
        self.__mutable_delegate = mutable_delegate
        
    def __getattr__(self, name):
        return getattr(self.__mutable_delegate[0], name)
    

def make_proxy():
    '''
    Generate (setter, Proxy) pairs.  The setter will supply the value to
    be proxied later; the proxy itself can be place in the graph immediately.
    '''
    mutable_delegate = [None]
    def setter(value):
        '''
        This is called later to "tie the knot".
        '''
        mutable_delegate[0] = value
    return (setter, Proxy(mutable_delegate))


def clone(node, args, kargs):
    '''
    The basic clone function that is supplied to `Clone`.
    '''
    try:
        # pylint: disable-msg=W0142
        return type(node)(*args, **kargs)
    except TypeError as err:
        raise TypeError(format('Error cloning {0} with ({1}, {2}): {3}',
                               type(node), args, kargs, err))


class Clone(Visitor):
    '''
    Clone the graph, applying a particular clone function.
    '''
    
    def __init__(self, clone_=clone):
        super(Clone, self).__init__()
        self._clone = clone_
        self._proxies = {}
        self._node = None
    
    def loop(self, node):
        '''
        Wrap loop nodes in proxies.
        '''
        if node not in self._proxies:
            self._proxies[node] = make_proxy()
        return self._proxies[node][1]
    
    def node(self, node):
        '''
        Store the current node.
        '''
        self._node = node
    
    def constructor(self, *args, **kargs):
        '''
        Clone the node, back-patching proxies as necessary.
        '''
        node = self._clone(self._node, args, kargs)
        if self._node in self._proxies:
            self._proxies[self._node][0](node)
        return node
    
    def leaf(self, value):
        '''
        Don't clone leaf nodes.
        '''
        return value
    

def post_clone(function):
    '''
    Generate a clone function that applies the given function to the newly
    constructed node (so, when used with `Clone`, effectively performs a
    map on the graph).
    '''
    return compose(function, clone)

