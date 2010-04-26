
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
Tests for the lepl.regexp.matchers module.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import Separator, Regexp, NfaRegexp, DfaRegexp


# pylint: disable-msg=C0103, C0111, C0301
# (dude this is just a test)


class MatchersTest(TestCase):
    
    def test_nfa(self):
        #basicConfig(level=DEBUG)
        
        with Separator(~Regexp(r'\s*')):
            word = NfaRegexp('[A-Z][a-z]*')
            phrase = word[1:]
        phrase.config.no_full_first_match()
            
        results = list(phrase.match('Abc'))
        assert len(results) == 3, results
        assert results[0][0] == ['Abc'], results
        assert results[1][0] == ['Ab'], results
        assert results[2][0] == ['A'], results
        
        results = list(phrase.match('AbcDef'))
        assert len(results) == 6, results
        assert results[0][0] == ['Abc', 'Def'], results
        
        results = list(phrase.match('Abc Def'))
        assert len(results) == 6, results
        
    def test_dfa(self):
        #basicConfig(level=DEBUG)
        
        with Separator(~Regexp(r'\s*')):
            word = DfaRegexp('[A-Z][a-z]*')
            phrase = word[1:]
        phrase.config.no_full_first_match()
        
        results = list(phrase.match('Abc'))
        assert len(results) == 1, results
        assert results[0][0] == ['Abc'], results
        
        results = list(phrase.match('AbcDef'))
        assert len(results) == 2, results
        assert results[0][0] == ['Abc', 'Def'], results
        
        results = list(phrase.match('Abc Def'))
        assert len(results) == 2, results
        
    def test_full_first_match(self):
        #basicConfig(level=DEBUG)
        matcher = Regexp('a')
        assert matcher.parse('a')
        


