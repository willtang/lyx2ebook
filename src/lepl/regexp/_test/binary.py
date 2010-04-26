
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
Tests for the lepl.regexp.binary module.
'''

from unittest import TestCase

#from logging import basicConfig, DEBUG
from lepl.regexp.binary import binary_single_parser
from lepl.support.lib import format

# pylint: disable-msg=C0103, C0111, C0301, C0324, R0201, R0903, R0904
# (dude this is just a test)


def _test_parser(text):
    return binary_single_parser('label', text)

def label(text):
    return format('(?P<label>{0!s})', text)
    
class CharactersTest(TestCase):
    
    def test_dot(self):
        #basicConfig(level=DEBUG)
        c = _test_parser('.')
        assert label('.') == str(c), str(c)
#        assert 0 == c[0][0][0][0], type(c[0][0][0][0])
#        assert 1 == c[0][0][0][1], type(c[0][0][0][1])

    def test_brackets(self):
        #basicConfig(level=DEBUG)
        c = _test_parser('0')
        assert label('0') == str(c), str(c)
        # this is the lower bound for the interval
#        assert 0 == c[0][0][0][0], type(c[0][0][0][0])
        # and the upper - we really do have a digit
#        assert 0 == c[0][0][0][1], type(c[0][0][0][1])
        c = _test_parser('1')
        assert label('1') == str(c), str(c)
        c = _test_parser('0101')
        assert label('0101') == str(c), str(c)
   
    def test_star(self):
        c = _test_parser('0*')
        assert label('0*') == str(c), str(c)
        c = _test_parser('0(01)*1')
        assert label('0(01)*1') == str(c), str(c)
        
    def test_option(self):
        c = _test_parser('1?')
        assert label('1?') == str(c), str(c)
        c = _test_parser('0(01)?1')
        assert label('0(01)?1') == str(c), str(c)
        
    def test_choice(self):
        c = _test_parser('(0*|1)')
        assert label('(0*|1)') == str(c), str(c)


