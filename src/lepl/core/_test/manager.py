
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
Tests for the lepl.core.manager module.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl.matchers.derived import Eos
from lepl.matchers.core import Literal
from lepl.support.lib import LogMixin


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102, C0321, W0141, R0201, R0904
# (dude this is just a test)

    
class LimitedDepthTest(LogMixin, TestCase):
    '''
    The test here takes '****' and divides it amongst the matchers, all of
    which will take 0 to 4 matches.  The number of different permutations
    depends on backtracking and varies depending on the queue length
    available.
    '''
    
    def test_limited_depth(self):
        '''
        These show something is happening.  Whether they are exactly correct
        is another matter altogether...
        '''
        #basicConfig(level=DEBUG)
        # there was a major bug here that made this test vary often
        # it should now be fixed
        self.assert_range(3, 'g', [15,1,1,1,1,3,3,3,6,6,6,10,10,10,15], 4)
        self.assert_range(3, 'b', [15,1,1,1,1,5,5,5,5,5,5,5,5,5,5,15], 4)
        self.assert_range(3, 'd', [15,1,1,1,3,3,6,6,6,10,10,10,15], 4)
        
    def assert_range(self, n_match, direcn, results, multiplier):
        for index in range(len(results)):
            queue_len = index * multiplier
            expr = Literal('*')[::direcn,...][n_match] & Eos()
            expr.config.clear().manage(queue_len)
            matcher = expr.get_match_string()
            self.assert_count(matcher, queue_len, index, results[index])
            
    def assert_count(self, matcher, queue_len, index, count):
        results = list(matcher('****'))
        found = len(results)
        assert found == count, (queue_len, index, found, count)

    def test_single(self):
        #basicConfig(level=DEBUG)
        expr = Literal('*')[:,...][3]
        expr.config.clear().manage(5)
        match = expr.get_match_string()('*' * 4)
        list(match)
        