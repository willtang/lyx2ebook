
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
Tests for the lepl.bin.literal module.
'''

if bytes is str:
    print('Binary parsing unsupported in this Python version')
else:
    
    #from logging import basicConfig, DEBUG
    from unittest import TestCase
    
    from lepl.bin.bits import BitString
    from lepl.bin.literal import parse
    from lepl.support.node import Node
    
    
    # pylint: disable-msg=C0103, C0111, C0301
    # (dude this is just a test)


    class ParseTest(TestCase):
        '''
        Test whether we correctly parse a spec.
        '''
        
        def bassert(self, value, expected, length=None):
            x = BitString.from_int(expected, length)
            assert value == x, (value, x)
            
        def test_simple(self):
            b = parse('(0/1)')
            assert isinstance(b, Node), type(b)
            assert len(b) == 1, len(b)
            assert isinstance(b[0], BitString), type(b[0])
            assert len(b[0]) == 1, len(b[0])
            assert b[0].zero()
            b = parse('(0/1, 1/1)')
            assert isinstance(b, Node), type(b)
            assert len(b) == 2, len(b)
            assert isinstance(b[1], BitString), type(b[1])
            assert len(b[1]) == 1, len(b[1])
            assert not b[1].zero()
            b = parse('(a=0/1)')
            assert isinstance(b, Node), type(b)
            assert len(b) == 1, len(b)
            assert isinstance(b.a[0], BitString), type(b.a[0])
            assert len(b.a[0]) == 1, len(b.a[0])
            assert b.a[0].zero()
            b = parse('(a=(0/1))')
            assert isinstance(b, Node), type(b)
            assert len(b) == 1, len(b)
            assert isinstance(b.a[0], Node), type(b.a[0])
            assert len(b.a[0]) == 1, len(b.a[0])
            assert isinstance(b.a[0][0], BitString), type(b.a[0][0])
            assert len(b.a[0][0]) == 1, len(b.a[0][0])
            assert b.a[0][0].zero()
            b = parse('(0)')
            assert isinstance(b, Node), type(b)
            assert len(b) == 1, len(b)
            assert isinstance(b[0], BitString), type(b[0])
            assert len(b[0]) == 32, len(b[0])
            assert b[0].zero()
        
        def test_single(self):
            b = parse('''(123/8, foo=0x123/2.0,\nbar=1111100010001000b0)''')
            self.bassert(b[0], '0x7b') 
            self.bassert(b[1], '0x123', 16) 
            self.bassert(b.foo[0], '0x123', 16) 
            self.bassert(b[2], '1111100010001000b0') 
            self.bassert(b.bar[0], '1111100010001000b0') 
            
        def test_nested(self):
            b = parse('(123, (foo=123x0/2.))')
            self.bassert(b[0], 123)
            assert isinstance(b[1], Node), str(b)
            self.bassert(b[1].foo[0], 0x2301, 16)
        
        def test_named(self):
            #basicConfig(level=DEBUG)
            b = parse('A(B(1), B(2))')
            self.bassert(b.B[0][0], 1)
            self.bassert(b.B[1][0], 2)
    
        def test_repeat(self):
            b = parse('(1*3)')
            self.bassert(b[0], '010000000100000001000000x0')
            b = parse('(a=0x1234 * 3)')
            self.bassert(b.a[0], '341234123412x0')
    
