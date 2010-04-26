
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
Tests for the lepl.support.node module.
'''

#from logging import basicConfig, DEBUG, INFO
from unittest import TestCase

from lepl import Delayed, Digit, Any, Node, make_error, node_throw, Or, Space, \
    AnyBut, Eos
from lepl.support.graph import order, PREORDER, POSTORDER, LEAF
from lepl._test.base import assert_str


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102, C0321, R0201, R0903
# (dude this is just a test)

    
class NodeTest(TestCase):

    def test_node(self):
        #basicConfig(level=DEBUG)
        
        class Term(Node): pass
        class Factor(Node): pass
        class Expression(Node): pass

        expression  = Delayed()
        number      = Digit()[1:,...]                      > 'number'
        term        = (number | '(' / expression / ')')    > Term
        muldiv      = Any('*/')                            > 'operator'
        factor      = (term / (muldiv / term)[0::])        > Factor
        addsub      = Any('+-')                            > 'operator'
        expression += (factor / (addsub / factor)[0::])    > Expression
        
        p = expression.get_parse_string()
        ast = p('1 + 2 * (3 + 4 - 5)')
        assert_str(ast[0], """Expression
 +- Factor
 |   +- Term
 |   |   `- number '1'
 |   `- ' '
 +- operator '+'
 +- ' '
 `- Factor
     +- Term
     |   `- number '2'
     +- ' '
     +- operator '*'
     +- ' '
     `- Term
         +- '('
         +- Expression
         |   +- Factor
         |   |   +- Term
         |   |   |   `- number '3'
         |   |   `- ' '
         |   +- operator '+'
         |   +- ' '
         |   +- Factor
         |   |   +- Term
         |   |   |   `- number '4'
         |   |   `- ' '
         |   +- operator '-'
         |   +- ' '
         |   `- Factor
         |       `- Term
         |           `- number '5'
         `- ')'""")

class ListTest(TestCase):

    def test_list(self):
        #basicConfig(level=DEBUG)
        
        expression  = Delayed()
        number      = Digit()[1:,...]                   > 'number'
        term        = (number | '(' / expression / ')') > list
        muldiv      = Any('*/')                         > 'operator'
        factor      = (term / (muldiv / term)[0:])      > list
        addsub      = Any('+-')                         > 'operator'
        expression += (factor / (addsub / factor)[0:])  > list
        
        ast = expression.parse_string('1 + 2 * (3 + 4 - 5)')
        assert ast == [[[[('number', '1')], ' '], ('operator', '+'), ' ', [[('number', '2')], ' ', ('operator', '*'), ' ', ['(', [[[('number', '3')], ' '], ('operator', '+'), ' ', [[('number', '4')], ' '], ('operator', '-'), ' ', [[('number', '5')]]], ')']]]], ast


class ErrorTest(TestCase):

    def test_error(self):
        #basicConfig(level=INFO)
        
        class Term(Node): pass
        class Factor(Node): pass
        class Expression(Node): pass

        expression  = Delayed()
        number      = Digit()[1:,...]                                        > 'number'
        term        = Or(
            AnyBut(Space() | Digit() | '(')[1:,...]                          ^ 'unexpected text: {results[0]}', 
            number                                                           > Term,
            number ** make_error("no ( before '{stream_out}'") / ')'           >> node_throw,
            '(' / expression / ')'                                           > Term,
            ('(' / expression / Eos()) ** make_error("no ) for '{stream_in}'") >> node_throw)
        muldiv      = Any('*/')                                              > 'operator'
        factor      = (term / (muldiv / term)[0:,r'\s*'])                    >  Factor
        addsub      = Any('+-')                                              > 'operator'
        expression += (factor / (addsub / factor)[0:,r'\s*'])                >  Expression
        line        = expression / Eos()
       
        parser = line.get_parse_string()
        
        try:
            parser('1 + 2 * 3 + 4 - 5)')[0]
            assert False, 'expected error'
        except SyntaxError as e:
            assert e.msg == "no ( before ')'", e.msg

        try:
            parser('1 + 2 * (3 + 4 - 5')
            assert False, 'expected error'
        except SyntaxError as e:
            assert e.msg == "no ) for '(3 + 4 - 5'", e.msg
            
        try:
            parser('1 + 2 * foo')
            assert False, 'expected error'
        except SyntaxError as e:
            assert e.msg == "unexpected text: foo", e.msg


class EqualityTest(TestCase):
    
    def test_object_eq(self):
        a = Node('a')
        b = Node('a')
        assert a != b
        assert b != a
        assert a is not b
        assert b is not a
        assert a == a
        assert b == b
        assert a is a
        assert b is b
        
    def test_recursive_eq(self):
        a = Node('a', Node('b'))
        b = Node('a', Node('b'))
        c = Node('a', Node('c'))
        assert a._recursively_eq(b)
        assert not a._recursively_eq(c)
        

class ChildrenTest(TestCase):
    
    def test_children(self):
        a = Node('a')
        for c in a:
            assert c == 'a', c


class OrderTest(TestCase):

    def tree(self):
        return Node('a', 
                 Node('b',
                   Node('c',
                     Node('d'),
                     Node('e')),
                   Node('f')), 
                 Node('g'), 
                 Node('h',
                   Node('i',
                     Node('j'),
                     Node('k')),
                   Node('l')))
    
    def order(self, tree, flags):
        return list(map(lambda x: x[0], order(tree, flags, Node, LEAF)))
    
    def test_orders(self):
        tree = self.tree()
        ordered = self.order(tree, PREORDER)
        assert ordered == ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l'], ordered
        ordered = self.order(tree, POSTORDER)
        assert ordered == ['d', 'e', 'c', 'f', 'b', 'g', 'j', 'k', 'i', 'l', 'h', 'a'], ordered
        
    def test_str(self):
        text = str(self.tree())
        assert text == """Node
 +- 'a'
 +- Node
 |   +- 'b'
 |   +- Node
 |   |   +- 'c'
 |   |   +- Node
 |   |   |   `- 'd'
 |   |   `- Node
 |   |       `- 'e'
 |   `- Node
 |       `- 'f'
 +- Node
 |   `- 'g'
 `- Node
     +- 'h'
     +- Node
     |   +- 'i'
     |   +- Node
     |   |   `- 'j'
     |   `- Node
     |       `- 'k'
     `- Node
         `- 'l'""", text
        

class NestedNamedTest(TestCase):
    
    def tree(self):
        return Node(('a', Node('A')), ('b', Node('B')))
    
    def test_str(self):
        text = str(self.tree())
        assert text == """Node
 +- a
 |   `- 'A'
 `- b
     `- 'B'""", text
    
    
class NodeEqualityTest(TestCase):
    
    def test_equals(self):
        a = Node('abc')
        b = Node('abc')
        assert a == a
        assert not (a != a)
        assert not (a == b)
        assert a._recursively_eq(b)
        assert Node(a) != a
        assert Node(a)._recursively_eq(Node(a))
        assert not Node(a)._recursively_eq(a)
        