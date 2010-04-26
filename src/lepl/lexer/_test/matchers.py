
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
Wide range of tests for lexer.
'''

# pylint: disable-msg=R0201, R0904, R0903, R0914
# tests

#from logging import basicConfig, DEBUG
from math import sin, cos
from operator import add, sub, truediv, mul
from unittest import TestCase

from lepl import Token, Literal, Float, LexerError, Node, Delayed, Any, Eos, \
    UnsignedFloat, Or, RuntimeLexerError
from lepl.support.lib import str


def str26(value):
    '''
    Convert to string with crude hack for 2.6 Unicode
    '''
    string = str(value)
    return string.replace("u'", "'")


class RegexpCompilationTest(TestCase):
    '''
    Test whether embedded matchers are converted to regular expressions.
    '''
    
    def test_literal(self):
        '''
        Simple literal should compile directly.
        '''
        token = Token(Literal('abc'))
        token.compile()
        assert token.regexp == 'abc', repr(token.regexp)
        
    def test_float(self):
        '''
        A float is more complex, but still compiles.
        '''
        token = Token(Float())
        token.compile()
        assert token.regexp == \
            '([\\+\\-]|)(([0-9]([0-9])*|)\\.[0-9]([0-9])*|' \
            '[0-9]([0-9])*(\\.|))([Ee]([\\+\\-]|)[0-9]([0-9])*|)', \
            repr(token.regexp)
        
    def test_impossible(self):
        '''
        Cannot compile arbitrary functions.
        '''
        try:
            token = Token(Float() > (lambda x: x))
            token.compile()
            assert False, 'Expected error'
        except LexerError:
            pass


class TokenRewriteTest(TestCase):
    '''
    Test token support.
    '''
    
    def test_defaults(self):
        '''
        Basic configuration.
        '''
        reals = (Token(Float()) >> float)[:]
        reals.config.lexer()
        parser = reals.get_parse()
        results = parser('1 2.3')
        assert results == [1.0, 2.3], results
    
    def test_string_arg(self):
        '''
        Skip anything(not just spaces)
        '''
        words = Token('[a-z]+')[:]
        words.config.lexer(discard='.')
        parser = words.get_parse()
        results = parser('abc defXghi')
        assert results == ['abc', 'def', 'ghi'], results
        
    def test_bad_error_msg(self):
        '''
        An ugly error message (can't we improve this?)
        '''
        #basicConfig(level=DEBUG)
        words = Token('[a-z]+')[:]
        words.config.lexer()
        parser = words.get_parse()
        try:
            parser('abc defXghi')
            assert False, 'expected error'
        except RuntimeLexerError as err:
            assert str(err) == "No lexer for 'Xghi' at line 1 " \
                "character 7 of str: 'abc defXghi'.", str(err)
        
    def test_good_error_msg(self):
        '''
        Better error message with streams.
        '''
        #basicConfig(level=DEBUG)
        words = Token('[a-z]+')[:]
        words.config.lexer()
        parser = words.get_parse_string()
        try:
            parser('abc defXghi')
            assert False, 'expected error'
        except RuntimeLexerError as err:
            assert str(err) == 'No lexer for \'Xghi\' at line 1 character 7 ' \
                'of str: \'abc defXghi\'.', str(err)
        
    def test_expr_with_functions(self):
        '''
        Expression with function calls and appropriate binding.
        '''
        
        #basicConfig(level=DEBUG)
        
        # pylint: disable-msg=C0111, C0321
        class Call(Node): pass
        class Term(Node): pass
        class Factor(Node): pass
        class Expression(Node): pass
            
        value  = Token(Float())                         > 'value'
        name   = Token('[a-z]+')
        symbol = Token('[^a-zA-Z0-9\\. ]')
        
        expr    = Delayed()
        open_   = ~symbol('(')
        close   = ~symbol(')')
        funcn   = name                                  > 'name'
        call    = funcn & open_ & expr & close          > Call
        term    = call | value | open_ & expr & close   > Term
        muldiv  = symbol(Any('*/'))                     > 'operator'
        factor  = term & (muldiv & term)[:]             > Factor
        addsub  = symbol(Any('+-'))                     > 'operator'
        expr   += factor & (addsub & factor)[:]         > Expression
        line    = expr & Eos()
        
        line.config.trace(True).lexer()
        parser = line.get_parse_string()
        results = str26(parser('1 + 2*sin(3+ 4) - 5')[0])
        assert results == """Expression
 +- Factor
 |   `- Term
 |       `- value '1'
 +- operator '+'
 +- Factor
 |   +- Term
 |   |   `- value '2'
 |   +- operator '*'
 |   `- Term
 |       `- Call
 |           +- name 'sin'
 |           `- Expression
 |               +- Factor
 |               |   `- Term
 |               |       `- value '3'
 |               +- operator '+'
 |               `- Factor
 |                   `- Term
 |                       `- value '4'
 +- operator '-'
 `- Factor
     `- Term
         `- value '5'""", '[' + results + ']'
        

    def test_expression2(self):
        '''
        As before, but with evaluation.
        '''
        
        #basicConfig(level=DEBUG)
        
        # we could do evaluation directly in the parser actions. but by
        # using the nodes instead we allow future expansion into a full
        # interpreter
        
        # pylint: disable-msg=C0111, C0321
        class BinaryExpression(Node):
            op = lambda x, y: None
            def __float__(self):
                return self.op(float(self[0]), float(self[1]))
        
        class Sum(BinaryExpression): op = add
        class Difference(BinaryExpression): op = sub
        class Product(BinaryExpression): op = mul
        class Ratio(BinaryExpression): op = truediv
        
        class Call(Node):
            funs = {'sin': sin,
                    'cos': cos}
            def __float__(self):
                return self.funs[self[0]](self[1])
            
        # we use unsigned float then handle negative values explicitly;
        # this lets us handle the ambiguity between subtraction and
        # negation which requires context (not available to the the lexer)
        # to resolve correctly.
        number  = Token(UnsignedFloat())
        name    = Token('[a-z]+')
        symbol  = Token('[^a-zA-Z0-9\\. ]')
        
        expr    = Delayed()
        factor  = Delayed()
        
        float_  = Or(number                            >> float,
                     ~symbol('-') & number             >> (lambda x: -float(x)))
        
        open_   = ~symbol('(')
        close   = ~symbol(')')
        trig    = name(Or('sin', 'cos'))
        call    = trig & open_ & expr & close          > Call
        parens  = open_ & expr & close
        value   = parens | call | float_
        
        ratio   = value & ~symbol('/') & factor        > Ratio
        prod    = value & ~symbol('*') & factor        > Product
        factor += prod | ratio | value
        
        diff    = factor & ~symbol('-') & expr         > Difference
        sum_    = factor & ~symbol('+') & expr         > Sum
        expr   += sum_ | diff | factor | value
        
        line    = expr & Eos()
        parser  = line.get_parse()
        
        def myeval(text):
            return float(parser(text)[0])
        
        self.assertAlmostEqual(myeval('1'), 1)
        self.assertAlmostEqual(myeval('1 + 2*3'), 7)
        self.assertAlmostEqual(myeval('1 - 4 / (3 - 1)'), -1)
        self.assertAlmostEqual(myeval('1 -4 / (3 -1)'), -1)
        self.assertAlmostEqual(myeval('1 + 2*sin(3+ 4) - 5'), -2.68602680256)


class ErrorTest(TestCase):
    '''
    Test various error messages.
    '''

    def test_mixed(self):
        '''
        Cannot mix tokens and non-tokens at same level.
        '''
        bad = Token(Any()) & Any()
        try:
            bad.get_parse()
            assert False, 'expected failure'
        except LexerError as err:
            assert str(err) == 'The grammar contains a mix of Tokens and ' \
                               'non-Token matchers at the top level. If ' \
                               'Tokens are used then non-token matchers ' \
                               'that consume input must only appear "inside" ' \
                               'Tokens.  The non-Token matchers include: ' \
                               'Any(None).', str(err)
        else:
            assert False, 'wrong exception'

    def test_bad_space(self):
        '''
        An unexpected character fails to match.
        '''
        token = Token('a')
        token.config.clear().lexer(discard='b')
        parser = token.get_parse()
        assert parser('a') == ['a'], parser('a')
        assert parser('b') == None, parser('b')
        try:
            parser('c')
            assert False, 'expected failure'
        except RuntimeLexerError as err:
            assert str(err) == "No lexer for 'c' at line 1 " \
                "character 0 of str: 'c'.", str(err)

    def test_incomplete(self):
        '''
        A token is not completely consumed (this doesn't raise error messages,
        it just fails to match).
        '''
        token = Token('[a-z]+')(Any())
        token.config.no_full_first_match()
        parser = token.get_parse_string()
        assert parser('a') == ['a'], parser('a')
        # even though this matches the token, the Any() sub-matcher doesn't
        # consume all the contents
        assert parser('ab') == None, parser('ab')
        token = Token('[a-z]+')(Any(), complete=False)
        token.config.no_full_first_match()
        parser = token.get_parse_string()
        assert parser('a') == ['a'], parser('a')
        # whereas this is fine, since complete=False
        assert parser('ab') == ['a'], parser('ab')
    
    def test_none_discard(self):
        '''
        If discard is '', discard nothing.
        '''
        token = Token('a')
        token.config.lexer(discard='').no_full_first_match()
        parser = token[1:].get_parse()
        result = parser('aa')
        assert result == ['a', 'a'], result
        try:
            parser(' a')
        except RuntimeLexerError as error:
            assert str26(error) == "No discard for ' a'.", str26(error)
            