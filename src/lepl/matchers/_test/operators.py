
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
Tests for the lepl.matchers.operators module.
'''

from threading import Thread
from unittest import TestCase

from lepl import Delayed, Any, Eos, Drop, Separator, Literal, Space, \
    SmartSeparator1, Optional


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102
# (dude this is just a test)

    
class ThreadTest(TestCase):
    '''
    Test for thread safety.
    '''
    
    def test_safety(self):
        matcher3 = Delayed()
        matcher4 = Delayed()
        matcher1 = Any()[::'b',...] & Eos()
        with Separator(Drop(Any('a')[:])):
            matcher2 = Any()[::'b',...] & Eos()
            # pylint: disable-msg=W0613
            def target(matcher3=matcher3, matcher4=matcher4):
                matcher3 += Any()[::'b',...] & Eos()
                with Separator(Drop(Any('b')[:])):
                    matcher4 += Any()[::'b',...] & Eos()
            t = Thread(target=target)
            t.start()
            t.join()
            matcher5 = Any()[::'b',...] & Eos()
        matcher6 = Any()[::'b',...] & Eos()
        text = 'cababab'
        assert text == matcher1.parse_string(text)[0], matcher1.parse_string(text)
        assert 'cbbb' == matcher2.parse_string(text)[0], matcher2.parse_string(text)
        assert text == matcher3.parse_string(text)[0], matcher3.parse_string(text)
        assert 'caaa' == matcher4.parse_string(text)[0], matcher4.parse_string(text)
        assert 'cbbb' == matcher5.parse_string(text)[0], matcher5.parse_string(text)
        assert text == matcher6.parse_string(text)[0], matcher6.parse_string(text)


class SpaceTest(TestCase):
    
    def word(self):
        return Literal("a") & Literal("bc")[1:,...]

    def test_spaces(self):
        with Separator(~Space()):
            s1 = self.word()[1:]
        s1.config.no_full_first_match()
        s1 = s1.get_parse_string()
        assert not s1("abc")
        assert s1("a bc")
        with Separator(None):
            s2 = self.word()[1:]
        s2.config.no_full_first_match()
        s2 = s2.get_parse_string()
        assert s2("abc")
        assert not s2("a bc")


class SmartSpace1Test(TestCase):
    
    def test_smart_spaces(self):
        with SmartSeparator1(Space()):
            parser = 'a' &  Optional('b') & 'c' & Eos()
        parser.config.no_full_first_match()
        assert parser.parse('a b c')
        assert parser.parse('a c')
        assert not parser.parse('a b c ')
        assert not parser.parse('a c ')
        assert not parser.parse('a bc')
        assert not parser.parse('ab c')
        assert not parser.parse('abc')
        assert not parser.parse('ac')
        assert not parser.parse('a  c')
