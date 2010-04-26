
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103,R0903,R0914
#@PydevCodeAnalysisIgnore
# (the code style is for documentation, not "real")

'''
Examples from the documentation.
'''

from lepl import *
from lepl._example.support import Example
from lepl._test.base import assert_str


class NodeExample(Example):
    
    def test_flat(self):
        
        expr   = Delayed()
        number = Digit()[1:,...]
        
        with Separator(r'\s*'):
            term    = number | '(' & expr & ')'
            muldiv  = Any('*/')
            factor  = term & (muldiv & term)[:]
            addsub  = Any('+-')
            expr   += factor & (addsub & factor)[:]
            line    = expr & Eos()

        def example1():
            return line.parse_string('1 + 2 * (3 + 4 - 5)')
        
        self.examples([(example1,
"['1', ' ', '', '+', ' ', '2', ' ', '*', ' ', '(', '', '3', ' ', '', '+', ' ', '4', ' ', '', '-', ' ', '5', '', '', ')', '']")
            ])
        
    def test_drop_empty(self):
        
        expr   = Delayed()
        number = Digit()[1:,...]
        
        with Separator(DropEmpty(Regexp(r'\s*'))):
            term    = number | '(' & expr & ')'
            muldiv  = Any('*/')
            factor  = term & (muldiv & term)[:]
            addsub  = Any('+-')
            expr   += factor & (addsub & factor)[:]
            line    = expr & Eos()

        def example1():
            return line.parse_string('1 + 2 * (3 + 4 - 5)')
        
        self.examples([(example1,
"['1', ' ', '+', ' ', '2', ' ', '*', ' ', '(', '3', ' ', '+', ' ', '4', ' ', '-', ' ', '5', ')']")
            ])
        

class ListExample(Example):
    
    def test_nested(self):
        
        expr   = Delayed()
        number = Digit()[1:,...]
        
        with Separator(Drop(Regexp(r'\s*'))):
            term    = number | (Drop('(') & expr & Drop(')') > list)
            muldiv  = Any('*/')
            factor  = (term & (muldiv & term)[:])
            addsub  = Any('+-')
            expr   += factor & (addsub & factor)[:]
            line    = expr & Eos()
            
        def example1():
            return line.parse_string('1 + 2 * (3 + 4 - 5)')
        
        self.examples([(example1,
"['1', '+', '2', '*', ['3', '+', '4', '-', '5']]")
            ])
        

class ListTreeExample(Example):

    def test_ast(self):
        
        class Term(List): pass
        class Factor(List): pass
        class Expression(List): pass
            
        expr   = Delayed()
        number = Digit()[1:,...]
        
        with DroppedSpace():
            term    = number | '(' & expr & ')'
            muldiv  = Any('*/')
            factor  = term & (muldiv & term)[:]         > Factor
            addsub  = Any('+-')
            expr   += factor & (addsub & factor)[:]     > Expression
            line    = expr & Eos()
            
        ast = line.parse_string('1 + 2 * (3 + 4 - 5)')[0]
        
        def example1():
            return ast
        
        def example2():
            return [child for child in ast]
                
        def example3():
            return [ast[i] for i in range(len(ast))]
                
        def example4():
            return ast[2][0][0]
        
        def example5():
            def per_list(type_, list_):
                return str(eval(''.join(list_)))
            def calculate(list_):
                return sexpr_fold(per_list=per_list)(list_)[0]
            return calculate(ast)
        
        def example6():
            return sexpr_fold(per_list=lambda t_, l: list(l))(ast)
            
        self.examples([(example1,
"""Expression
 +- Factor
 |   `- '1'
 +- '+'
 `- Factor
     +- '2'
     +- '*'
     +- '('
     +- Expression
     |   +- Factor
     |   |   `- '3'
     |   +- '+'
     |   +- Factor
     |   |   `- '4'
     |   +- '-'
     |   `- Factor
     |       `- '5'
     `- ')'"""),
                    (example2, 
"[Factor(...), '+', Factor(...)]"),
                    (example3, 
"[Factor(...), '+', Factor(...)]"),
                    (example4, '2'),
                    (example5, '5'),
                    (example6, """[['1'], '+', ['2', '*', '(', [['3'], '+', ['4'], '-', ['5']], ')']]""")
                    ])
                

# pylint: disable-msg=W0612
class TreeExample(Example):

    def test_ast(self):
        
        class Term(Node): pass
        class Factor(Node): pass
        class Expression(Node): pass
            
        expr   = Delayed()
        number = Digit()[1:,...]                        > 'number'
        
        with Separator(r'\s*'):
            term    = number | '(' & expr & ')'         > Term
            muldiv  = Any('*/')                         > 'operator'
            factor  = term & (muldiv & term)[:]         > Factor
            addsub  = Any('+-')                         > 'operator'
            expr   += factor & (addsub & factor)[:]     > Expression
            line    = expr & Eos()
            
        ast = line.parse_string('1 + 2 * (3 + 4 - 5)')[0]
        
        def example1():
            return ast
        
        def example2():
            return [child for child in ast]
                
        def example2b():
            return [ast[i] for i in range(len(ast))]
                
        def example3():
            return [(name, getattr(ast, name)) for name in dir(ast)]
        
        def example4():
            return ast.Factor[1].Term[0].number[0]
                
        self.examples([(example1,
"""Expression
 +- Factor
 |   +- Term
 |   |   `- number '1'
 |   `- ' '
 +- ''
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
         +- ''
         +- Expression
         |   +- Factor
         |   |   +- Term
         |   |   |   `- number '3'
         |   |   `- ' '
         |   +- ''
         |   +- operator '+'
         |   +- ' '
         |   +- Factor
         |   |   +- Term
         |   |   |   `- number '4'
         |   |   `- ' '
         |   +- ''
         |   +- operator '-'
         |   +- ' '
         |   `- Factor
         |       +- Term
         |       |   `- number '5'
         |       `- ''
         +- ''
         `- ')'"""),
                    (example2, 
"[Factor(...), '', '+', ' ', Factor(...)]"),
                    (example2b, 
"[Factor(...), '', '+', ' ', Factor(...)]"),
                    (example3, 
"[('Factor', [Factor(...), Factor(...)]), ('operator', ['+'])]"),
                    (example4, '2')
                    ])


class NestedNodeExample(Example):
    
    def test_nested(self):
        
        class Term(Node): pass
        class Factor(Node): pass
        class Expression(Node): pass
            
        expr   = Delayed()
        number = Digit()[1:,...]                         > 'number'
        
        with Separator(Drop(Regexp(r'\s*'))):
            term    = number | '(' & expr & ')'          > Term
            muldiv  = Any('*/')                          > 'operator'
            factor  = (term & (muldiv & term)[:] > Node) > 'factor'
            addsub  = Any('+-')                          > 'operator'
            expr   += factor & (addsub & factor)[:]      > Expression
            line    = expr & Eos()
            
        ast = line.parse_string('1 + 2 * (3 + 4 - 5)')[0]
        text = str(ast)
        assert_str(text, """Expression
 +- factor
 |   `- Term
 |       `- number '1'
 +- operator '+'
 `- factor
     +- Term
     |   `- number '2'
     +- operator '*'
     `- Term
         +- '('
         +- Expression
         |   +- factor
         |   |   `- Term
         |   |       `- number '3'
         |   +- operator '+'
         |   +- factor
         |   |   `- Term
         |   |       `- number '4'
         |   +- operator '-'
         |   `- factor
         |       `- Term
         |           `- number '5'
         `- ')'""")