
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
Tests for the lepl.support.lib module.
'''

from unittest import TestCase

from lepl.support.lib import assert_type, CircularFifo


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, R0201, R0913
# (dude this is just a test)

    
class AssertTypeTestCase(TestCase):
    
    def test_ok(self):
        assert_type('', 1, int)
        assert_type('', '', str)
        assert_type('', None, int, none_ok=True)
        
    def test_bad(self):
        self.assert_bad('The foo attribute in Bar', '', int, False, 
                        "The foo attribute in Bar (value '') must be of type int.")
        self.assert_bad('The foo attribute in Bar', None, int, False, 
                        "The foo attribute in Bar (value None) must be of type int.")
        
    def assert_bad(self, name, value, type_, none_ok, msg):
        try:
            assert_type(name, value, type_, none_ok=none_ok)
            assert False, 'Expected failure'
        except TypeError as e:
            assert e.args[0] == msg, e.args[0]


class CircularFifoTest(TestCase):
    
    def test_expiry(self):
        fifo = CircularFifo(3)
        assert None == fifo.append(1)
        assert None == fifo.append(2)
        assert None == fifo.append(3)
        for i in range(4,10):
            assert i-3 == fifo.append(i)
            
    def test_pop(self):
        fifo = CircularFifo(3)
        for i in range(1,3):
            for j in range(i):
                assert None == fifo.append(j)
            for j in range(i):
                popped = fifo.pop()
                assert j == popped, '{0} {1} {2}'.format(i, j, popped)
        for i in range(4):
            fifo.append(i)
        assert 1 == fifo.pop()
        
    def test_list(self):
        fifo = CircularFifo(3)
        for i in range(7):
            fifo.append(i)
        assert [4,5,6] == list(fifo)
        fifo.append(7)
        assert [5,6,7] == list(fifo)
        fifo.append(8)
        assert [6,7,8] == list(fifo)
        fifo.append(9)
        assert [7,8,9] == list(fifo)
