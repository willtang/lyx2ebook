
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
Tests for the lepl.stream.maxdepth module.
'''


from unittest import TestCase
from lepl import Any, Eos, Optional
from lepl.stream.maxdepth import FullFirstMatch, FullFirstMatchException, facade_factory


class FullFirstMatchTest(TestCase):
    
    def test_stream(self):
        matcher = Any('a')
        matcher.config.clear()
        result = list(matcher.match('b'))
        assert result == [], result
        (stream, _memory) = facade_factory('b')
        result = list(matcher.match_null(stream))
        assert result == [], result
    
    def test_exception(self):
        matcher = FullFirstMatch(Any('a'))
        matcher.config.clear()
        try:
            list(matcher.match('b'))
            assert False, 'expected error'
        except FullFirstMatchException as e:
            assert str(e) == """The match failed at 'b',
Line 1, character 0 of str: 'b'.""", str(e)
            
    def test_message(self):
        matcher = FullFirstMatch(Any('a'))
        matcher.config.clear()
        try:
            list(matcher.match_string('b'))
            assert False, 'expected error'
        except FullFirstMatchException as e:
            assert str(e) == """The match failed at 'b',
Line 1, character 0 of str: 'b'.""", str(e)
            
    def test_location(self):
        matcher = FullFirstMatch(Any('a')[:] & Eos())
        matcher.config.clear()
        try:
            list(matcher.match_string('aab'))
            assert False, 'expected error'
        except FullFirstMatchException as e:
            assert str(e) == """The match failed at 'b',
Line 1, character 2 of str: 'aab'.""", str(e)
            
    def test_ok(self):
        matcher = FullFirstMatch(Any('a'))
        matcher.config.clear()
        result = list(matcher.match_null('a'))
        assert result == [(['a'], '')], result
        

class FullFirstMatchConfigTest(TestCase):
    
    def test_exception(self):
        matcher = Any('a')
        matcher.config.full_first_match(eos=False)
        try:
            list(matcher.match('b'))
            assert False, 'expected error'
        except FullFirstMatchException as e:
            assert str(e) == """The match failed at 'b',
Line 1, character 0 of str: 'b'.""", str(e)
            
    def test_eos(self):
        matcher = Optional(Any('a'))
        matcher.config.full_first_match(eos=True)
        try:
            list(matcher.match('b'))
            assert False, 'expected error'
        except FullFirstMatchException as e:
            assert str(e) == """The match failed at 'b',
Line 1, character 0 of str: 'b'.""", str(e)
            
    def test_message(self):
        matcher = Any('a')
        matcher.config.full_first_match(eos=False)
        try:
            list(matcher.match_string('b'))
            assert False, 'expected error'
        except FullFirstMatchException as e:
            assert str(e) == """The match failed at 'b',
Line 1, character 0 of str: 'b'.""", str(e)
            
    def test_location(self):
        matcher = Any('a')[:]
        matcher.config.full_first_match(eos=True)
        try:
            list(matcher.match_string('aab'))
            assert False, 'expected error'
        except FullFirstMatchException as e:
            assert str(e) == """The match failed at 'b',
Line 1, character 2 of str: 'aab'.""", str(e)
            
    def test_ok(self):
        matcher = Any('a')
        matcher.config.full_first_match(eos=False)
        result = list(matcher.match_null('a'))
        assert result == [(['a'], '')], result
        matcher.config.full_first_match(eos=True)
        result = list(matcher.match_null('a'))
        assert result == [(['a'], '')], result
        
    
