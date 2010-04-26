
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
Tests for the lepl.support.graph module.
'''

from unittest import TestCase


from lepl.support.graph import ArgAsAttributeMixin, preorder, postorder, reset, \
    ConstructorWalker, Clone, make_proxy, LEAF, leaves
from lepl.support.node import Node


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102, C0321, W0141
# (dude this is just a test)

    
class SimpleNode(ArgAsAttributeMixin):
    
    # pylint: disable-msg=E1101
    
    def __init__(self, label, *nodes):
        super(SimpleNode, self).__init__()
        self._arg(label=label)
        self._args(nodes=nodes)
        
    def __str__(self):
        return str(self.label)
    
    def __repr__(self):
        args = [str(self.label)]
        args.extend(map(repr, self.nodes))
        return 'SimpleNode(%s)' % ','.join(args)
    
    def __getitem__(self, index):
        return self.nodes[index]
    
    def __len__(self):
        return len(self.nodes)
    

def graph():
    return SimpleNode(1,
                SimpleNode(11,
                     SimpleNode(111),
                     SimpleNode(112)),
                SimpleNode(12))
        
class OrderTest(TestCase):
    
    def test_preorder(self):
        result = [node.label for node in preorder(graph(), SimpleNode, exclude=LEAF)]
        assert result == [1, 11, 111, 112, 12], result
        
    def test_postorder(self):
        result = [node.label for node in postorder(graph(), SimpleNode, exclude=LEAF)]
        assert result == [111, 112, 11, 12, 1], result
        
        
class ResetTest(TestCase):
    
    def test_reset(self):
        nodes = preorder(graph(), SimpleNode, exclude=LEAF)
        assert next(nodes).label == 1
        assert next(nodes).label == 11
        reset(nodes)
        assert next(nodes).label == 1
        assert next(nodes).label == 11


class CloneTest(TestCase):
    
    def test_simple(self):
        g1 = graph()
        g2 = ConstructorWalker(g1, SimpleNode)(Clone())
        assert repr(g1) == repr(g2)
        assert g1 is not g2
    
    def assert_same(self, text1, text2):
        assert self.__clean(text1) == self.__clean(text2), self.__clean(text1)
    
    def __clean(self, text):
        depth = 0
        result = ''
        for c in text:
            if c == '<':
                depth += 1
            elif c == '>':
                depth -= 1
            elif depth == 0:
                result += c
        return result

    def test_loop(self):
        (s, n) = make_proxy()
        g1 = SimpleNode(1,
                SimpleNode(11,
                     SimpleNode(111),
                     SimpleNode(112),
                     n),
                SimpleNode(12))
        s(g1)
        g2 = ConstructorWalker(g1, SimpleNode)(Clone())
        self.assert_same(repr(g1), repr(g2))

    def test_loops(self):
        (s1, n1) = make_proxy()
        (s2, n2) = make_proxy()
        g1 = SimpleNode(1,
                SimpleNode(11,
                     SimpleNode(111, n2),
                     SimpleNode(112),
                     n1),
                SimpleNode(12, n1))
        s1(g1)
        s2(next(iter(g1)))
        g2 = ConstructorWalker(g1, SimpleNode)(Clone())
        self.assert_same(repr(g1), repr(g2))
        
    def test_loops_with_proxy(self):
        (s1, n1) = make_proxy()
        (s2, n2) = make_proxy()
        g1 = SimpleNode(1,
                SimpleNode(11,
                     SimpleNode(111, n2),
                     SimpleNode(112),
                     n1),
                SimpleNode(12, n1))
        s1(g1)
        s2(next(iter(g1)))
        g2 = ConstructorWalker(g1, SimpleNode)(Clone())
        g3 = ConstructorWalker(g2, SimpleNode)(Clone())
        self.assert_same(repr(g1), repr(g3))
#        print(repr(g3))


class GenericOrderTest(TestCase):
    
    def test_preorder(self):
        g = [1, [11, [111, 112], 12]]
        result = [node for node in preorder(g, list) if isinstance(node, int)]
        assert result == [1, 11, 111, 112, 12], result
        
    def test_postorder(self):
        '''
        At first I was surprised about this (compare with SimpleNode results above),
        but these are leaf nodes, so postorder doesn't change anything (there's
        no difference between "before visiting" and "after visiting" a leaf). 
        '''
        g = [1, [11, [111, 112], 12]]
        result = [node for node in postorder(g, list) if isinstance(node, int)]
        assert result == [1, 11, 111, 112, 12], result
        
        
class LeafTest(TestCase):
    
    def test_order(self):
        tree = Node(1, 2, Node(3, Node(4), Node(), 5))
        result = list(leaves(tree, Node))
        assert result == [1,2,3,4,5], result
        