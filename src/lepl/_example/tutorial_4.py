
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103,R0201,R0903
#@PydevCodeAnalysisIgnore
# (the code style is for documentation, not "real")

'''
Examples from the documentation.
'''

#from logging import basicConfig, DEBUG
from operator import add, sub, mul, truediv
from timeit import timeit

from lepl import *
from lepl._example.support import Example


def add_sub_node():
    value = Token(UnsignedFloat())
    symbol = Token('[^0-9a-zA-Z \t\r\n]')
    number = Optional(symbol('-')) + value >> float
    group2, group3 = Delayed(), Delayed()

    # first layer, most tightly grouped, is parens and numbers
    parens = symbol('(') & group3 & symbol(')')
    group1 = parens | number

    # second layer, next most tightly grouped, is multiplication
    mul = group1 & symbol('*') & group2 > List
    div = group1 & symbol('/') & group2 > List
    group2 += mul | div | group1

    # third layer, least tightly grouped, is addition
    add = group2 & symbol('+') & group3 > List
    sub = group2 & symbol('-') & group3 > List
    group3 += add | sub | group2
    return group3

def error_1():
    value = Token(UnsignedFloat())
    symbol = Token('[^0-9a-zA-Z \t\r\n]')
    number = Optional(symbol('-')) + value >> float
    group2, group3 = Delayed(), Delayed()

    # first layer, most tightly grouped, is parens and numbers
    parens = symbol('(') & group3 & symbol(')')
    group1 = parens | number

    # second layer, next most tightly grouped, is multiplication
    mul = group1 & symbol('*') & group2 > List
    div = group1 & symbol('/') & group2 > List
    group2 += group1 | mul | div

    # third layer, least tightly grouped, is addition
    add = group2 & symbol('+') & group3 > List
    sub = group2 & symbol('-') & group3 > List
    group3 += group2 | add | sub
    return group3

def error_2():
    value = Token(UnsignedFloat())
    symbol = Token('[^0-9a-zA-Z \t\r\n]')
    number = Optional(symbol('-')) + value >> float
    group2, group3 = Delayed(), Delayed()

    # first layer, most tightly grouped, is parens and numbers
    parens = symbol('(') & group3 & symbol(')')
    group1 = parens | number

    # second layer, next most tightly grouped, is multiplication
    mul = group2 & symbol('*') & group2 > List
    div = group2 & symbol('/') & group2 > List
    group2 += group1 | mul | div

    # third layer, least tightly grouped, is addition
    add = group3 & symbol('+') & group3 > List
    sub = group3 & symbol('-') & group3 > List
    group3 += group2 | add | sub
    return group3

def node_1():
    class Add(List): pass
    class Sub(List): pass
    class Mul(List): pass
    class Div(List): pass
    value = Token(UnsignedFloat())
    symbol = Token('[^0-9a-zA-Z \t\r\n]')
    number = Optional(symbol('-')) + value >> float
    group2, group3 = Delayed(), Delayed()

    # first layer, most tightly grouped, is parens and numbers
    parens = ~symbol('(') & group3 & ~symbol(')')
    group1 = parens | number

    # second layer, next most tightly grouped, is multiplication
    mul = group1 & ~symbol('*') & group2 > Mul
    div = group1 & ~symbol('/') & group2 > Div
    group2 += mul | div | group1

    # third layer, least tightly grouped, is addition
    add = group2 & ~symbol('+') & group3 > Add
    sub = group2 & ~symbol('-') & group3 > Sub
    group3 += add | sub | group2
    return group3

def node_2():
    class Op(List):
        def __float__(self):
            return self._op(float(self[0]), float(self[1]))
    class Add(Op): _op = add
    class Sub(Op): _op = sub
    class Mul(Op): _op = mul
    class Div(Op): _op = truediv
    value = Token(UnsignedFloat())
    symbol = Token('[^0-9a-zA-Z \t\r\n]')
    number = Optional(symbol('-')) + value >> float
    group2, group3 = Delayed(), Delayed()
    # first layer, most tightly grouped, is parens and numbers
    parens = ~symbol('(') & group3 & ~symbol(')')
    group1 = parens | number
    # second layer, next most tightly grouped, is multiplication
    mul_ = group1 & ~symbol('*') & group2 > Mul
    div_ = group1 & ~symbol('/') & group2 > Div
    group2 += mul_ | div_ | group1
    # third layer, least tightly grouped, is addition
    add_ = group2 & ~symbol('+') & group3 > Add
    sub_ = group2 & ~symbol('-') & group3 > Sub
    group3 += add_ | sub_ | group2
    return group3


class Tutorial4Example(Example):
    
    def run_add_sub_node(self):
        return add_sub_node()

    def run_error_1(self):
        return error_1()
    
    def unlimited_run_error_1(self):
        matcher = self.run_error_1()
        matcher.config.no_full_first_match()
        return matcher

    def run_error_2(self):
        return error_2()
    
    def unlimited_run_error_2(self):
        matcher = self.run_error_2()
        matcher.config.no_full_first_match()
        return matcher
    
    def test_all(self):
        
        self.examples([
(lambda: self.run_add_sub_node().parse('1+2*(3-4)+5/6+7')[0],
"""List
 +- 1.0
 +- '+'
 `- List
     +- List
     |   +- 2.0
     |   +- '*'
     |   +- '('
     |   +- List
     |   |   +- 3.0
     |   |   +- '-'
     |   |   `- 4.0
     |   `- ')'
     +- '+'
     `- List
         +- List
         |   +- 5.0
         |   +- '/'
         |   `- 6.0
         +- '+'
         `- 7.0"""),
(lambda: self.run_error_1().parse('1+2*(3-4)+5/6+7')[0], 
"""lepl.stream.maxdepth.FullFirstMatchException: The match failed at '+',
Line 1, character 1 of str: '1+2*(3-4)+5/6+7'.
"""),
(lambda: len(list(self.unlimited_run_error_1().parse_all('1+2*(3-4)+5/6+7'))), 
"""6"""),
(lambda: (self.run_error_1() & Eos()).parse('1+2*(3-4)+5/6+7')[0], 
"""List
 +- 1.0
 +- '+'
 `- List
     +- List
     |   +- 2.0
     |   +- '*'
     |   +- '('
     |   +- List
     |   |   +- 3.0
     |   |   +- '-'
     |   |   `- 4.0
     |   `- ')'
     +- '+'
     `- List
         +- List
         |   +- 5.0
         |   +- '/'
         |   `- 6.0
         +- '+'
         `- 7.0"""),
(lambda: len(list((self.unlimited_run_error_1() & Eos()).parse_all('1+2*(3-4)+5/6+7'))), 
"""1"""),
(lambda: self.run_error_2().parse('1+2*(3-4)+5/6+7')[0], 
"""lepl.stream.maxdepth.FullFirstMatchException: The match failed at '+',
Line 1, character 1 of str: '1+2*(3-4)+5/6+7'.
"""),
(lambda: len(list(self.unlimited_run_error_2().parse_all('1+2*(3-4)+5/6+7'))), 
"""12"""),
(lambda: (self.run_error_2() & Eos()).parse('1+2*(3-4)+5/6+7')[0], 
"""List
 +- 1.0
 +- '+'
 `- List
     +- List
     |   +- 2.0
     |   +- '*'
     |   +- '('
     |   +- List
     |   |   +- 3.0
     |   |   +- '-'
     |   |   `- 4.0
     |   `- ')'
     +- '+'
     `- List
         +- List
         |   +- 5.0
         |   +- '/'
         |   `- 6.0
         +- '+'
         `- 7.0"""),
(lambda: len(list((self.unlimited_run_error_2() & Eos()).parse_all('1+2*(3-4)+5/6+7'))), 
"""5"""),
(lambda: node_1().parse('1+2*(3-4)+5/6+7')[0],
"""Add
 +- 1.0
 `- Add
     +- Mul
     |   +- 2.0
     |   `- Sub
     |       +- 3.0
     |       `- 4.0
     `- Add
         +- Div
         |   +- 5.0
         |   `- 6.0
         `- 7.0"""),
(lambda: node_2().parse('1+2*(3-4)+5/6+7')[0],
"""Add
 +- 1.0
 `- Add
     +- Mul
     |   +- 2.0
     |   `- Sub
     |       +- 3.0
     |       `- 4.0
     `- Add
         +- Div
         |   +- 5.0
         |   `- 6.0
         `- 7.0"""),
(lambda: float(node_2().parse('1+2*(3-4)+5/6+7')[0]),
"""6.83333333333"""),
])


if __name__ == '__main__':
        
    parser = add_sub_node().get_parse()
    print(timeit('parser("1+2*(3-4)+5/6+7")',
                 'from __main__ import parser', number=100))
    
    parser = (error_1() & Eos()).get_parse()
    print(timeit('parser("1+2*(3-4)+5/6+7")',
                 'from __main__ import parser', number=100))
    
    parser = (error_2() & Eos()).get_parse()
    print(timeit('parser("1+2*(3-4)+5/6+7")',
                 'from __main__ import parser', number=100))

