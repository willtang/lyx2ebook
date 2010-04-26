
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
An example from the manual based on a test in this package (currently not used
in docs because something similar is developed in the tutorial).
'''

from math import sin, cos
from operator import add, sub, truediv, mul

from lepl import Node, Token, UnsignedFloat, Delayed, Or, Eos
from lepl._example.support import Example


class Calculator(Example):
    '''
    Show how tokens can help simplify parsing of an expression; also
    give a simple interpreter.
    '''
    
    def test_calculation(self):
        '''
        We could do evaluation directly in the parser actions. but by
        using the nodes instead we allow future expansion into a full
        interpreter.
        '''
        
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
        
        float_  = Or(number                       >> float,
                     ~symbol('-') & number        >> (lambda x: -float(x)))
        
        open_   = ~symbol('(')
        close   = ~symbol(')')
        trig    = name(Or('sin', 'cos'))
        call    = trig & open_ & expr & close     > Call
        parens  = open_ & expr & close
        value   = parens | call | float_
        
        ratio   = value & ~symbol('/') & factor   > Ratio
        prod    = value & ~symbol('*') & factor   > Product
        factor += prod | ratio | value
        
        diff    = factor & ~symbol('-') & expr    > Difference
        sum_    = factor & ~symbol('+') & expr    > Sum
        expr   += sum_ | diff | factor | value
        
        line    = expr & Eos()
        parser  = line.get_parse()
        
        def calculate(text):
            return float(parser(text)[0])
        
        self.examples([(lambda: calculate('1'), '1.0'),
                       (lambda: calculate('1 + 2*3'), '7.0'),
                       (lambda: calculate('-1 - 4 / (3 - 1)'), '-3.0'),
                       (lambda: calculate('1 -4 / (3 -1)'), '-1.0'),
                       (lambda: calculate('1 + 2*sin(3+ 4) - 5'), 
                        '-2.68602680256')])
