
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
Tests for the lepl.bin.encode module.
'''

if bytes is str:
    print('Binary parsing unsupported in this Python version')
else:

    from unittest import TestCase
    
    from lepl.bin.bits import BitString
    from lepl.bin.encode import dispatch_table, simple_serialiser
    from lepl.bin.literal import parse
    
    
    # pylint: disable-msg=C0103, C0111, C0301
    # (dude this is just a test)

    
    class EncodeTest(TestCase):
        '''
        Test whether we correctly encode
        '''
        
        def test_encode(self):
            mac = parse('''
    Frame(
      Header(
        preamble  = 0b10101010*7,
        start     = 0b10101011,
        destn     = 010203040506x0,
        source    = 0708090a0b0cx0,
        ethertype = 0800x0
      ),
      Data(1/8,2/8,3/8,4/8),
      CRC(234d0/4.)
    )
    ''')
        
            serial = simple_serialiser(mac, dispatch_table())
            bs = serial.bytes()
            for _index in range(7):
                b = next(bs)
                assert b == BitString.from_int('0b10101010').to_int(), b
            b = next(bs)
            assert b == BitString.from_int('0b10101011').to_int(), b
            