
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
Further tests for the lepl.offside.regexp module.
'''

# pylint: disable-msg=C0111, R0201
# tests


#from logging import basicConfig, DEBUG, INFO, ERROR
from unittest import TestCase

from lepl.lexer.matchers import Token
from lepl.offside.matchers import BLine
from lepl.offside.regexp import LineAwareAlphabet, SOL, EOL
from lepl.regexp.core import Compiler
from lepl.regexp.matchers import DfaRegexp
from lepl.regexp.str import make_str_parser
from lepl.regexp.unicode import UnicodeAlphabet
from lepl.support.lib import str


class RegexpTest(TestCase):
    
    def test_invert_bug_1(self):
        #basicConfig(level=DEBUG)
        match = DfaRegexp('(*SOL)[^c]*')
        match.config.default_line_aware().trace(True).no_full_first_match()
        result = list(match.match_string('abc'))[0][0]
        assert result == ['ab'], result
        
    def test_invert_bug_4(self):
        #basicConfig(level=DEBUG)
        bad = BLine(Token('[^a]*'))
        bad.config.line_aware(block_policy=2).left_memoize()
        parser = bad.get_parse_string()
        result = parser('123')
        assert result == ['123'], result
        
    def test_invert_bug_5(self):
        #basicConfig(level=DEBUG)
        bad = BLine(Token('[^(*SOL)(*EOL)a]*'))
        bad.config.default_line_aware(block_policy=2, 
                                      parser_factory=make_str_parser)
        bad.config.trace(True)
        parser = bad.get_parse_string()
        result = parser('123')
        assert result == ['123'], result
        
    def test_invert_bug_6(self):
        #basicConfig(level=DEBUG)
        bad = BLine(Token(str('[^(*SOL)(*EOL)a]*')))
        bad.config.default_line_aware(block_policy=2,
                                      parser_factory=make_str_parser)
        bad.config.trace(True)
        parser = bad.get_parse_string() 
        result = parser(str('123'))
        assert result == [str('123')], result
        
    def test_match_1(self):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), 
                                     make_str_parser)
        expr = Compiler.single(alphabet, '[a]').nfa()
        result = list(expr.match(str('a123')))
        assert result == [(str('label'), str('a'), str('123'))], result
        
    def test_match_2(self):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), 
                                     make_str_parser)
        expr = Compiler.single(alphabet, '[^a]').nfa()
        result = list(expr.match(str('123a')))
        assert result == [(str('label'), str('1'), str('23a'))], result
        
    def test_match_3(self):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), 
                                     make_str_parser)
        expr = Compiler.single(alphabet, '[^a]*').dfa()
        result = list(expr.match(str('123a')))
        assert result == [[str('label')], str('123'), str('a')], result
        
    def test_match_4(self):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), 
                                     make_str_parser)
        expr = Compiler.single(alphabet, '[^a]*').dfa()
        result = list(expr.match([str('1'), str('a')]))
        assert result == [[str('label')], [str('1')], [str('a')]], result
        
    def test_match_5(self):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), 
                                     make_str_parser)
        expr = Compiler.single(alphabet, '[^a]*').dfa()
        result = list(expr.match([SOL, str('1'), str('a')]))
        assert result == [[str('label')], [SOL, str('1')], [str('a')]], result
        
    def test_match_6(self):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), 
                                     make_str_parser)
        expr = Compiler.single(alphabet, '[^(*SOL)a]*').dfa()
        result = list(expr.match([SOL, str('1'), str('a')]))
        assert result == [[str('label')], [], [SOL, str('1'), str('a')]], \
            result

    def test_match_7(self):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), 
                                     make_str_parser)
        expr = Compiler.single(alphabet, '[^(*SOL)(*EOL)a]*').dfa()
        result = list(expr.match([str('1'), EOL]))
        assert result == [[str('label')], [str('1')], [EOL]], \
            result
