
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
Support for matcher tests.
'''

#from logging import basicConfig, DEBUG
from re import sub
from unittest import TestCase

from lepl.support.lib import basestring, str
from lepl.stream.maxdepth import FullFirstMatchException


class BaseTest(TestCase):
    
    def assert_direct(self, stream, match, target):
        match.config.no_full_first_match()
        result = [x for (x, _s) in match.match_string(stream)]
        assert target == result, result
    
    def assert_fail(self, stream, match):
        try:
            match.match_string(stream)
            assert 'Expected error'
        except FullFirstMatchException:
            pass
        
    def assert_list(self, stream, match, target, **kargs):
        match.config.no_full_first_match()
        matcher = match.get_parse_items_all()
        #print(matcher.matcher)
        result = list(matcher(stream, **kargs))
        assert target == result, result
        
    def assert_literal(self, stream, matcher):
        self.assert_direct(stream, matcher, [[stream]])

        
def assert_str(a, b):
    '''
    Assert two strings are approximately equal, allowing tests to run in
    Python 3 and 2.
    '''
    def clean(x):
        x = str(x)
        x = x.replace("u'", "'")
        x = x.replace("lepl.matchers.error.Error", "Error")
        x = x.replace("lepl.stream.maxdepth.FullFirstMatchException", "FullFirstMatchException")
        x = sub('<(.+) 0x[0-9a-fA-F]*>', '<\\1 0x...>', x)
        x = sub('(\\d+)L', '\\1', x)
        return x
    a = clean(a)
    b = clean(b)
    assert a == b, '"' + a + '" != "' + b + '"'
