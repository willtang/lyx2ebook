
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

from lepl import *
from lepl._example.support import Example


class Tutorial2Example(Example):
    
    def run_error(self):
        number = SignedFloat() >> float
        add = number & ~Literal('+') & number > sum
        return add.parse('12 + 30')
    
    def run_explicit_space(self):
        number = SignedFloat() >> float
        add = number & ~Space() & ~Literal('+') & ~Space() & number > sum
        return add.parse('12 + 30')
    
    def run_space_error(self):
        number = SignedFloat() >> float
        add = number & ~Space() & ~Literal('+') & ~Space() & number > sum
        return add.parse('12+30')

    def run_star(self, text):
        number = SignedFloat() >> float
        spaces = ~Star(Space())
        add = number & spaces & ~Literal('+') & spaces & number > sum
        return add.parse(text)
    
    def run_a3(self):
        a = Literal('a')
        return a[3].parse('aaa')

    def run_a24(self, text):
        a = Literal('a')
        return a[2:4].parse(text)
    
    def run_a24_all(self):
        a = Literal('a')
        return list(a[2:4].parse_all('aaaa'))
    
    def run_a01(self):
        a = Literal('a')
        return list(a[:1].parse_all('a'))

    def run_a4plus(self):
        a = Literal('a')
        return list(a[4:].parse_all('aaaaa'))
    
    def run_breadth(self):
        a = Literal('a')[2:4:'b']
        a.config.no_full_first_match()
        return list(a.parse_all('aaaa'))
    
    def run_brackets(self, text):
        number = SignedFloat() >> float
        spaces = ~Space()[:]
        add = number & spaces & ~Literal('+') & spaces & number > sum
        return add.parse(text)
    
    def run_nfa_regexp(self):
        return list(NfaRegexp('a*').parse_all('aaa'))
    
    def run_dfa_regexp(self):
        return list(DfaRegexp('a*').parse_all('aaa'))
    
    def run_regexp(self):
        return list(Regexp('a*').parse_all('aaa'))
    
    def run_token_1(self):
        value = Token(SignedFloat())
        symbol = Token('[^0-9a-zA-Z \t\r\n]')
        number = value >> float
        add = number & ~symbol('+') & number > sum
        return add.parse_string('12+30')
    
    def run_token_2(self, text):
        value = Token(UnsignedFloat())
        symbol = Token('[^0-9a-zA-Z \t\r\n]')
        number = Optional(symbol('-')) + value >> float
        add = number & ~symbol('+') & number > sum
        return add.parse(text)

    def test_all(self):
        self.examples([
(self.run_error,
"""lepl.stream.maxdepth.FullFirstMatchException: The match failed at ' + 30',
Line 1, character 2 of str: '12 + 30'.
"""),
(self.run_explicit_space,
"""[42.0]"""),
(self.run_space_error,
"""lepl.stream.maxdepth.FullFirstMatchException: The match failed at '+30',
Line 1, character 2 of str: '12+30'.
"""),
(lambda: self.run_star('12 + 30'),
"""[42.0]"""),
(lambda: self.run_star('12+30'),
"""[42.0]"""),
(lambda: self.run_star('12+     30'),
"""[42.0]"""),
(self.run_a3,
"""['a', 'a', 'a']"""),
(lambda: self.run_a24('aa'),
"""['a', 'a']"""),
(lambda: self.run_a24('aaaa'),
"""['a', 'a', 'a', 'a']"""),
(self.run_a24_all,
"""[['a', 'a', 'a', 'a'], ['a', 'a', 'a'], ['a', 'a']]"""),
(self.run_a01,
"""[['a'], []]"""),
(self.run_a4plus,
"""[['a', 'a', 'a', 'a', 'a'], ['a', 'a', 'a', 'a']]"""),
(self.run_breadth,
"""[['a', 'a'], ['a', 'a', 'a'], ['a', 'a', 'a', 'a']]"""),
(lambda: self.run_brackets('12 + 30'),
"""[42.0]"""),
(lambda: self.run_brackets('12+30'),
"""[42.0]"""),
(lambda: self.run_brackets('12+     30'),
"""[42.0]"""),
(self.run_nfa_regexp,
"""[['aaa'], ['aa'], ['a'], ['']]"""),
(self.run_dfa_regexp,
"""[['aaa']]"""),
(self.run_regexp,
"""[['aaa']]"""),
(self.run_token_1,
"""lepl.stream.maxdepth.FullFirstMatchException: The match failed at '+30',
Line 1, character 2 of str: '12+30'.
"""),
(lambda: self.run_token_2('12+30'),
"""[42.0]"""),
(lambda: self.run_token_2('12 + -30'),
"""[-18.0]"""),
])
        
