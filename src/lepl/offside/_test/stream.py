
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
Tests for the lepl.offside.stream module.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl.lexer.matchers import Token
from lepl.matchers.core import Regexp, Literal, Any
from lepl.offside.matchers import BLine, Indent, Eol
from lepl.offside.support import OffsideError
from lepl.regexp.matchers import DfaRegexp

class LineTest(TestCase):
    
    def test_bad_config(self):
        #basicConfig(level=DEBUG)
        text = Token('[^\n\r]+')
        quoted = Regexp("'[^']'")
        line = BLine(text(quoted))
        line.config.default_line_aware()
        parser = line.get_parse_string()
        try:
            parser("'a'")
            assert False, 'Expected error'
        except OffsideError as error:
            assert str(error).startswith('No initial indentation has been set.')
            
    def test_line(self):
        #basicConfig(level=DEBUG)
        text = Token('[^\n\r]+')
        quoted = Regexp("'[^']'")
        line = BLine(text(quoted))
        line.config.default_line_aware(block_start=0)
        parser = line.get_parse_string()
        assert parser("'a'") == ["'a'"]
        
    def test_offset(self):
        #basicConfig(level=DEBUG)
        text = Token('[^\n\r]+')
        line = BLine(text(~Literal('aa') & Regexp('.*')))
        line.config.default_line_aware(block_start=0)
        parser = line.get_parse_string()
        assert parser('aabc') == ['bc']
        # what happens with an empty match?
        check = ~Literal('aa') & Regexp('.*')
        check.config.no_full_first_match()
        assert check.parse('aa') == ['']
        assert parser('aa') == ['']
        
    def test_single_line(self):
        #basicConfig(level=DEBUG)
        line = DfaRegexp('(*SOL)[a-z]*(*EOL)')
        line.config.default_line_aware()
        parser = line.get_parse_string()
        assert parser('abc') == ['abc']
        
    def test_tabs(self):
        '''
        Use block_policy here so that the regexp parser that excludes SOL
        and EOL is used; otherwise Any()[:] matches those and we end up
        with a single monster token.
        '''
        line = Indent() & Token(Any()) & Eol()
        line.config.default_line_aware(tabsize=8, block_policy=0).trace(True)
        result = line.parse('a')
        assert result == ['', 'a', ''], result
        result = line.parse('\ta')
        assert result == ['        ', 'a', ''], result
        line.config.default_line_aware(tabsize=None, block_policy=0)
        result = line.parse('\ta')
        assert result == ['\t', 'a', ''], result
        line.config.default_line_aware(block_policy=0)
        result = line.parse('\ta')
        assert result == ['        ', 'a', ''], result

