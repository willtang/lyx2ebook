
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
Base classes for AST nodes (and associated functions).
'''

from lepl.support.graph import GraphStr, ConstructorGraphNode, ConstructorWalker,\
    postorder
from lepl.support.lib import LogMixin, basestring, format


class NodeException(Exception):
    '''
    Exception raised when we have problems dynamically creating nodes.
    '''


def is_named(arg):
    '''
    Is this is "named tuple"?
    '''
    return (isinstance(arg, tuple) or isinstance(arg, list)) \
            and len(arg) == 2 and isinstance(arg[0], basestring)
            
            
def new_named_node(name, node):
    '''
    Generate a sub-class of Node, with the given name as type, as long as
    it is not already a subclass.
    '''
    if type(node) != Node:
        raise NodeException(
            format('Will not coerce a node subclass ({0}) to {1}',
                   type(node), name))
    class_ = type(name, (Node,), {})
    (args, kargs) = node._constructor_args()
    return class_(*args, **kargs)


def coerce(arg):
    '''
    Convert named nodes to nodes with that name.
    '''
    if is_named(arg) and isinstance(arg[1], Node):
        return new_named_node(arg[0], arg[1])
    else:
        return arg
    

# pylint: disable-msg=R0903
# it's not supposed to have public attributes, because it exposes contents
class Node(LogMixin, ConstructorGraphNode):
    '''
    A base class for AST nodes.

    It is designed to be applied to a list of results, via ``>``.

    Nodes support both simple list--like behaviour::
    
      >>> abc = Node('a', 'b', 'c')
      >>> abc[1]
      'b'
      >>> abc[1:]
      ['b', 'c']
      >>> abc[:-1]
      ['a', 'b']
    
    and dict--like behaviour through attributes::
    
      >>> fb = Node(('foo', 23), ('bar', 'baz'))
      >>> fb.foo
      [23]
      >>> fb.bar
      ['baz']
    
    Both mixed together::
    
      >>> fb = Node(('foo', 23), ('bar', 'baz'), 43, 'zap', ('foo', 'again'))
      >>> fb[:]
      [23, 'baz', 43, 'zap', 'again']
      >>> fb.foo
      [23, 'again']
    
    Note how ``('name', value)`` pairs have a special meaning in the constructor.
    This is supported by the creation of "named pairs"::
    
      >>> letter = Letter() > 'letter'
      >>> digit = Digit() > 'digit'
      >>> example = (letter | digit)[:] > Node
      >>> n = example.parse('abc123d45e')[0]
      >>> n.letter
      ['a', 'b', 'c', 'd', 'e']
      >>> n.digit
      ['1', '2', '3', '4', '5']
    
    However, a named pair with a Node as a value is coerced into a subclass of
    Node with the given name (this keeps Nodes connected into a single tree and
    so simplifies traversal).
    '''
    
    def __init__(self, *args):
        '''
        Expects a single list of arguments, as will be received if invoked with
        the ``>`` operator.
        '''
        super(Node, self).__init__()
        self.__postorder = ConstructorWalker(self, Node)
        self.__children = []
        self.__paths = []
        self.__names = set()
        for arg in map(coerce, args):
            if is_named(arg):
                self.__add_named_child(arg[0], arg[1])
            elif isinstance(arg, Node):
                self.__add_named_child(arg.__class__.__name__, arg)
            else:
                self.__add_anon_child(arg)
        
    def __add_named_child(self, name, value):
        '''
        Add a value associated with a name (either a named pair or the class
        of a Node subclass).
        '''
        index = self.__add_attribute(name, value)
        self.__children.append(value)
        self.__paths.append((name, index))
        
    def __add_anon_child(self, value):
        '''
        Add a nameless value.
        '''
        index = len(self.__children)
        self.__children.append(value)
        self.__paths.append(index)
            
    def __add_attribute(self, name, value):
        '''
        Attributes are associated with lists of (named) values.
        '''
        if name not in self.__names:
            self.__names.add(name)
            setattr(self, name, [])
        attr = getattr(self, name)
        index = len(attr)
        attr.append(value)
        return index
        
    def __dir__(self):
        '''
        The names of all the attributes constructed from the results.
        '''
        # this must return a list, not an iterator (Python requirement)
        return list(self.__names)
    
    def __getitem__(self, index):
        return self.__children[index]
    
    def __iter__(self):
        return iter(self.__children)
    
    def __str__(self):
        visitor = NodeTreeStr()
        return self.__postorder(visitor)
    
    def __repr__(self):
        return self.__class__.__name__ + '(...)'
    
    def __len__(self):
        return len(self.__children)
    
    def __bool__(self):
        return bool(self.__children)
    
    # Python 2.6
    def __nonzero__(self):
        return self.__bool__()
    
    def _recursively_eq(self, other):
        '''
        This compares two nodes by recursively comparing their contents.
        It may be useful for testing, for example, but care should be taken
        to avoid its use on cycles of objects.
        '''
        try:
            siblings = iter(other)
        except TypeError:
            return False
        for child in self:
            try:
                sibling = next(siblings)
                try:
                    # pylint: disable-msg=W0212
                    if not child._recursively_eq(sibling):
                        return False
                except AttributeError:
                    if child != sibling:
                        return False
            except StopIteration:
                return False
        try:
            next(siblings)
            return False
        except StopIteration:
            return True
        
    def _constructor_args(self):
        '''
        Regenerate the constructor arguments (returns (args, kargs)).
        '''
        args = []
        for (path, value) in zip(self.__paths, self.__children):
            if isinstance(path, int):
                args.append(value)
            else:
                name = path[0]
                if name == value.__class__.__name__:
                    args.append(value)
                else:
                    args.append((name, value))
        return (args, {})
    
    
# pylint: disable-msg=R0903
# __ method
class MutableNode(Node):
    '''
    Extend `Node` to allow children to be set.
    '''
    
    def __setitem__(self, index, value):
        self.__children[index] = value
        
        
class NodeTreeStr(GraphStr):
    '''
    Extend `GraphStr` to handle named pairs - this generates an 'ASCII tree'
    representation of the node graph.
    '''
    
    def leaf(self, arg):
        '''
        Leaf nodes are either named or simple values.
        '''
        if is_named(arg):
            return lambda first, rest, name_: \
                    [first + arg[0] + (' ' if arg[0] else '') + repr(arg[1])]
        else:
            return super(NodeTreeStr, self).leaf(arg)
    

def node_throw(node):
    '''
    Raise an error, if one exists in the results (AST trees are traversed).
    Otherwise, the results are returned (invoke with ``>>``).
    '''
    for child in postorder(node, Node):
        if isinstance(child, Exception):
            raise child
    return node


# Below unrelated to nodes - move?

def make_dict(contents):
    '''
    Construct a dict from a list of named pairs (other values in the list
    will be discarded).  Invoke with ``>`` after creating named pairs with
    ``> string``.
    '''
    return dict(entry for entry in contents
                 if isinstance(entry, tuple) 
                 and len(entry) == 2
                 and isinstance(entry[0], basestring))


def join_with(separator=''):
    '''
    Join results together (via separator.join()) into a single string.
    
    Invoke as ``> join_with(',')``, for example.
    '''
    def fun(results):
        '''
        Delay evaluation.
        '''
        return separator.join(results)
    return fun
