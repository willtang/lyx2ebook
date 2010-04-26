
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
Tests for indentation aware parsing.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl.lexer.matchers import Token
from lepl.matchers.derived import Word, Letter
from lepl.offside.lexer import Indent, Eol


# pylint: disable-msg=R0201
# unittest convention
class IndentTest(TestCase):
    '''
    Test the `Indent` token.
    '''
    
    def test_indent(self):
        '''
        Test simple matches against leading spaces.
        '''
        #basicConfig(level=DEBUG)
        text = '''
left
    four'''
        word = Token(Word(Letter()))
        indent = Indent()
        line1 = indent('') + Eol()
        line2 = indent('') & word('left') + Eol()
        line3 = indent('    ') & word('four') + Eol()
        expr = (line1 & line2 & line3)
        expr.config.default_line_aware()
        parser = expr.get_parse_string()
        result = parser(text)
        assert result == ['', '', 'left', '    ', 'four'], result
        

class TabTest(TestCase):
    '''
    Check that tabs are expanded.
    '''
    
    def test_indent(self):
        '''
        Test simple matches against leading spaces.
        '''
        #basicConfig(level=DEBUG)
        text = '''
 onespace
 \tspaceandtab'''
        word = Token(Word(Letter()))
        indent = Indent()
        line1 = indent('') & ~Eol()
        line2 = indent(' ') & word('onespace') & ~Eol()
        line3 = indent('     ') & word('spaceandtab') & ~Eol()
        expr = line1 & line2 & line3
        expr.config.default_line_aware(tabsize=4).trace(True)
        parser = expr.get_parse_string()
        result = parser(text)
        #print(result)
        assert result == ['', ' ', 'onespace', '     ', 'spaceandtab'], result
        
    
