
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
Tests for the lepl.support.list module.
'''

#from logging import basicConfig, DEBUG, INFO
from unittest import TestCase

from lepl import *
from lepl._test.base import assert_str
from lepl.support.list import clone_sexpr, count_sexpr, join, \
    sexpr_flatten, sexpr_to_str


class FoldTest(TestCase):
    
    def test_clone(self):
        def test(list_):
            copy = clone_sexpr(list_)
            assert copy == list_, sexpr_to_str(copy)
        test([])
        test([1,2,3])
        test([[1],2,3])
        test([[[1]],2,3])
        test([[[1]],2,[3]])
        test([[[1]],'2',[3]])
        test(((1),List([2,3,[4]])))

    def test_count(self):
        def test(list_, value):
            measured = count_sexpr(list_)
            assert measured == value, measured
        test([], 0)
        test([1,2,3], 3)
        test([[1],2,3], 3)
        test([[[1,2],3],'four',5], 5)
        
    def test_flatten(self):
        def test(list_, joined, flattened):
            if joined is not None:
                result = join(list_)
                assert result == joined, result
            result = sexpr_flatten(list_)
            assert result == flattened, result
        test([[1],[2, [3]]], [1,2,[3]], [1,2,3])
        test([], [], [])
        test([1,2,3], None, [1,2,3])
        test([[1],2,3], None, [1,2,3])
        test([[[1,'two'],3],'four',5], None, [1,'two',3,'four',5])

    def test_sexpr_to_string(self):
        def test(list_, value):
            result = sexpr_to_str(list_)
            assert result == value, result
        test([1,2,3], '[1,2,3]')
        test((1,2,3), '(1,2,3)')
        test(List([1,2,3]), 'List([1,2,3])')
        class Foo(List): pass
        test(Foo([1,2,(3,List([4]))]), 'Foo([1,2,(3,List([4]))])')


class AstTest(TestCase):
    
    def test_ast(self):
        
        class Term(List): pass
        class Factor(List): pass
        class Expression(List): pass
            
        expr   = Delayed()
        number = Digit()[1:,...]                         >> int
        
        with Separator(Drop(Regexp(r'\s*'))):
            term    = number | '(' & expr & ')'          > Term
            muldiv  = Any('*/')
            factor  = term & (muldiv & term)[:]          > Factor
            addsub  = Any('+-')
            expr   += factor & (addsub & factor)[:]      > Expression
            line    = expr & Eos()
            
        ast = line.parse_string('1 + 2 * (3 + 4 - 5)')[0]
        text = str(ast)
        assert_str(text, """Expression
 +- Factor
 |   `- Term
 |       `- 1
 +- '+'
 `- Factor
     +- Term
     |   `- 2
     +- '*'
     `- Term
         +- '('
         +- Expression
         |   +- Factor
         |   |   `- Term
         |   |       `- 3
         |   +- '+'
         |   +- Factor
         |   |   `- Term
         |   |       `- 4
         |   +- '-'
         |   `- Factor
         |       `- Term
         |           `- 5
         `- ')'""")

        