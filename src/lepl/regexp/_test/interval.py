
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
Tests for the lepl.regexp.interval module.
'''

from unittest import TestCase

from lepl.regexp.interval import IntervalMap, TaggedFragments, Character
from lepl.regexp.unicode import UnicodeAlphabet


UNICODE = UnicodeAlphabet.instance()


# pylint: disable-msg=C0103, C0111, C0301, C0324
# (dude this is just a test)


class IntervalMapTest(TestCase):
    
    def test_single(self):
        m = IntervalMap()
        m[(1,2)] = 12
        assert m[0] == None, m[0]
        assert m[1] == 12, m[1]
        assert m[1.5] == 12, m[1.5]
        assert m[2] == 12, m[2]
        assert m[3] == None, m[3]
    
    def test_multiple(self):
        m = IntervalMap()
        m[(1,2)] = 12
        m[(4,5)] = 45
        for (i, v) in [(0, None), (1, 12), (2, 12), 
                       (3, None), (4, 45), (5, 45), (6, None)]:
            assert m[i] == v, (i, m[i])

    def test_delete(self):
        m = IntervalMap()
        m[(1,2)] = 12
        m[(4,5)] = 45
        for (i, v) in [(0, None), (1, 12), (2, 12), 
                       (3, None), (4, 45), (5, 45), (6, None)]:
            assert m[i] == v, (i, m[i])
        del m[(1,2)]
        for (i, v) in [(0, None), (1, None), (2, None), 
                       (3, None), (4, 45), (5, 45), (6, None)]:
            assert m[i] == v, (i, m[i])
        
        
class TaggedFragmentsTest(TestCase):
    
    def test_single(self):
        m = TaggedFragments(UNICODE)
        m.append(Character([('b', 'c')], UNICODE), 'bc')
        l = list(m)
        assert l == [(('b', 'c'), ['bc'])], l
        
    def test_overlap(self):
        m = TaggedFragments(UNICODE)
        m.append(Character([('b', 'd')], UNICODE), 'bd')
        m.append(Character([('c', 'e')], UNICODE), 'ce')
        l = list(m)
        assert l == [(('b', 'b'), ['bd']), 
                     (('c', 'd'), ['bd', 'ce']), 
                     (('e', 'e'), ['ce'])], l
        