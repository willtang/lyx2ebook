
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
Tests for the lepl.matchers.variables module.
'''

from io import StringIO
#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl._test.base import assert_str
from lepl.matchers.core import Any
from lepl.matchers.variables import NamedResult, TraceVariables


class ExplicitTest(TestCase):
    
    def test_wrapper(self):
        output = StringIO()
        matcher = NamedResult('foo', Any()[:], out=output)
        repr(matcher)
        matcher.config.clear()
        parser = matcher.get_match_string()
        list(parser('abc'))
        text = output.getvalue()
        assert_str(text, '''foo = ['a', 'b', 'c']
    "abc" -> ""
foo (2) = ['a', 'b']
    "abc" -> "c"
foo (3) = ['a']
    "abc" -> "bc"
foo (4) = []
    "abc" -> "abc"
! foo (after 4 matches)
    "abc"
''')
        
    def test_context(self):
        #basicConfig(level=DEBUG)
        output = StringIO()
        with TraceVariables(out=output):
            bar = Any()
        bar.config.no_full_first_match()
        repr(bar)
        list(bar.match('abc'))
        text = output.getvalue()
        assert_str(text, '''         bar = ['a']                            stream = 'bc'
         bar failed                             stream = 'abc'
''')

        