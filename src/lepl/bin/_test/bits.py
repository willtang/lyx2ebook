
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
Tests for the lepl.bin.bits module.
'''

if bytes is str:
    print('Binary parsing unsupported in this Python version')
else:

    #from logging import basicConfig, DEBUG
    from unittest import TestCase
    
    from lepl.bin.bits import Int, unpack_length, BitString, swap_table
    
    
    # pylint: disable-msg=C0103, C0111, C0301, W0702, C0324
    # (dude this is just a test)

    
    class IntTest(TestCase):
        
        def test_int(self):
            one = Int(1, 1)
            assert type(one) == Int
            assert 1 == one
            assert len(one) == 1
            assert str(one) == '1'
            assert repr(one) == 'Int(1,1)'
            assert 3 * one == 3
    
    
    class BitStringTest(TestCase):
    
        def test_lengths(self):
            assert 0 == unpack_length(0), unpack_length(0)
            assert 1 == unpack_length(1), unpack_length(1)
            assert 7 == unpack_length(7), unpack_length(7)
            assert 8 == unpack_length(8), unpack_length(8)
            assert 9 == unpack_length(9), unpack_length(9)
            assert 0 == unpack_length(0.), unpack_length(0.)
            assert 1 == unpack_length(0.1), unpack_length(0.1)
            assert 7 == unpack_length(0.7), unpack_length(0.7)
            assert 8 == unpack_length(1.), unpack_length(1.)
            assert 8 == unpack_length(1.0), unpack_length(1.0)
            assert 9 == unpack_length(1.1), unpack_length(1.1)
            assert 15 == unpack_length(1.7), unpack_length(1.7)
            assert 16 == unpack_length(2.), unpack_length(2.)
            self.assert_error(lambda: unpack_length(0.8))
            
        def assert_error(self, thunk):
            try:
                thunk()
                assert False, 'expected error'
            except:
                pass
            
        def assert_length_value(self, length, value, b):
            assert len(b) == length, (len(b), length)
            assert b.to_bytes() == value, (b.to_bytes(), value, b)
        
        def test_from_byte(self):
            self.assert_error(lambda: BitString.from_byte(-1))
            self.assert_length_value(8, b'\x00', BitString.from_byte(0))
            self.assert_length_value(8, b'\x01', BitString.from_byte(1))
            self.assert_length_value(8, b'\xff', BitString.from_byte(255))
            self.assert_error(lambda: BitString.from_byte(256))
        
        def test_from_bytearray(self):
            self.assert_length_value(8, b'\x00', BitString.from_bytearray(b'\x00'))
            self.assert_length_value(16, b'ab', BitString.from_bytearray(b'ab'))
            self.assert_length_value(16, b'ab', BitString.from_bytearray(bytearray(b'ab')))
            
        def test_from_int(self):
            self.assert_length_value(3, b'\x00', BitString.from_int('0o0'))
            self.assert_error(lambda: BitString.from_int('1o0'))
            self.assert_error(lambda: BitString.from_int('00o0'))
            self.assert_error(lambda: BitString.from_int('100o0'))
            self.assert_error(lambda: BitString.from_int('777o0'))
            self.assert_length_value(9, b'\x40\x00', BitString.from_int('0o100'))
            self.assert_length_value(9, b'\xfe\x01', BitString.from_int('0o776'))
            self.assert_length_value(12, b'\xff\x03', BitString.from_int('0x3ff'))
            self.assert_length_value(12, b'\xff\x03', BitString.from_int('0o1777'))
            self.assert_length_value(16, b'\x03\xff', BitString.from_int('03ffx0'))
            self.assert_length_value(3, b'\x04', BitString.from_int('0b100'))
            self.assert_length_value(1, b'\x01', BitString.from_int('1b0'))
            self.assert_length_value(2, b'\x02', BitString.from_int('01b0'))
            self.assert_length_value(9, b'\x00\x01', BitString.from_int('000000001b0'))
            self.assert_length_value(9, b'\x01\x01', BitString.from_int('100000001b0'))
            self.assert_length_value(16, b'\x0f\x33', BitString.from_int('1111000011001100b0'))
            
        def test_from_sequence(self):
            self.assert_length_value(8, b'\x01', BitString.from_sequence([1], BitString.from_byte))
            self.assert_error(lambda: BitString.from_sequence([256], BitString.from_byte))
            self.assert_length_value(16, b'\x01\x02', BitString.from_sequence([1,2], BitString.from_byte))
        
        def test_from_int_with_length(self):
            self.assert_error(lambda: BitString.from_int(1, 0))
            self.assert_error(lambda: BitString.from_int(0, 1))
            self.assert_error(lambda: BitString.from_int(0, 7))
            self.assert_length_value(8, b'\x00', BitString.from_int(0, 8))
            self.assert_error(lambda: BitString.from_int(0, 0.1))
            self.assert_length_value(8, b'\x00', BitString.from_int(0, 1.))
            self.assert_length_value(1, b'\x00', BitString.from_int('0x0', 1))
            self.assert_length_value(7, b'\x00', BitString.from_int('0x0', 7))
            self.assert_length_value(8, b'\x00', BitString.from_int('0x0', 8))
            self.assert_length_value(1, b'\x00', BitString.from_int('0x0', 0.1))
            self.assert_length_value(8, b'\x00', BitString.from_int('0x0', 1.))
            self.assert_length_value(16, b'\x34\x12', BitString.from_int(0x1234, 16))
            self.assert_length_value(16, b'\x34\x12', BitString.from_int('0x1234', 16))
            self.assert_length_value(16, b'\x12\x34', BitString.from_int('1234x0', 16))
            self.assert_length_value(16, b'\x34\x12', BitString.from_int('4660', 16))
            self.assert_length_value(16, b'\x34\x12', BitString.from_int('0d4660', 16))
            self.assert_length_value(16, b'\x12\x34', BitString.from_int('4660d0', 16))
            
        def test_str(self):
            b = BitString.from_int32(0xabcd1234)
            assert str(b) == '00101100 01001000 10110011 11010101b0/32', str(b)
            b = BitString.from_int('0b110')
            assert str(b) == '011b0/3', str(b)
    
        def test_invert(self):
            #basicConfig(level=DEBUG)
            self.assert_length_value(12, b'\x00\x0c', ~BitString.from_int('0x3ff'))
        
        def test_add(self):
            acc = BitString()
            for i in range(8):
                acc += BitString.from_int('0o' + str(i))
            # >>> hex(0o76543210)
            # '0xfac688'
            self.assert_length_value(24, b'\x88\xc6\xfa', acc)
            acc = BitString()
            for i in range(7):
                acc += BitString.from_int('0o' + str(i))
            self.assert_length_value(21, b'\x88\xc6\x1a', acc)
        
        def test_get_item(self):
            a = BitString.from_int('01001100011100001111b0')
            b = a[:]
            assert a == b, (a, b)
            b = a[0:]
            assert a == b, (a, b)
            b = a[-1::-1]
            assert BitString.from_int('11110000111000110010b0') == b, b
            b = a[0]
            assert BitString.from_int('0b0') == b, (b, str(b), BitString.from_int('0b0'))
            b = a[1]
            assert BitString.from_int('1b0') == b, b
            b = a[0:2]
            assert BitString.from_int('01b0') == b, b
            b = a[0:2]
            assert BitString.from_int('0b10') == b, b
            b = a[-5:]
            assert BitString.from_int('01111b0') == b, b
            b = a[-1:-6:-1]
            assert BitString.from_int('11110b0') == b, b
            b = a[1:-1]
            assert BitString.from_int('100110001110000111b0') == b, b
            
        def assert_round_trip(self, start, stop=None, length=None):
            if stop is None:
                stop = start
            result = BitString.from_int(start, length=length).to_int()
            assert result == stop, (result, stop)
            if length is not None:
                assert len(result) == length, (result, length)
            
        def test_to_int(self):
            self.assert_round_trip(0)
            self.assert_round_trip(1)
            self.assert_round_trip(1, length=1)
            self.assert_round_trip(467)
            self.assert_round_trip(467, length=16)
            self.assert_round_trip(467, length=19)
    
            
    class SwapTableTest(TestCase):
        
        def test_swap(self):
            table = swap_table()
            assert table[0x0f] == 0xf0, hex(table[0x0f])
            assert table[0xff] == 0xff
            assert table[0] == 0
            assert table[10] == 80, table[10]
