
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
An example that avoids using tokens with the line aware parsing.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

# pylint: disable-msg=W0614
from lepl import *


class TextTest(TestCase):

    def parser(self, regexp):
        '''
        Construct a parser that uses "offside rule" parsing, but which
        avoids using tokens in the grammar.
        '''
        
        # we still need one token, which matches "all the text"
        Text = Token(regexp)
        
        def TLine(contents):
            '''
            A version of BLine() that takes text-based matchers.
            '''
            return BLine(Text(contents))
        
        # from here on we use TLine instead of BLine and don't worry about
        # tokens.
        
        # first define the basic grammar
        with Separator(~Space()[:]):
            name = Word()
            args = name[:, ',']
            fundef = 'def' & name & '(' & args & ')' & ':'
            # in reality we would have more expressions!
            expression = Literal('pass') 
        
        # then define the block structure
        statement = Delayed()
        simple = TLine(expression)
        empty = TLine(Empty())
        block = TLine(fundef) & Block(statement[:])
        statement += (simple | empty | block) > list
        program = statement[:]
        
        program.config.default_line_aware(block_policy=2)
        return program.get_parse_string()
        
    def do_parse(self, parser):
        return parser('''pass
def foo():
  pass
  def bar():
    pass
''')
        
    def test_plus(self):
        parser = self.parser('[^\n]+')
        result = self.do_parse(parser)
        assert result == [['pass'], 
                          ['def', 'foo', '(', ')', ':', 
                           ['pass'], 
                           ['def', 'bar', '(', ')', ':', 
                            ['pass']]]], result

    def test_star(self):
        #basicConfig(level=DEBUG)
        parser = self.parser('[^\n]*')
        try:
            self.do_parse(parser)
            assert False, 'Expected error'
        except RuntimeLexerError:
            pass
        