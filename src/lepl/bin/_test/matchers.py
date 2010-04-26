
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
Tests for the lepl.bin.matchers module.
'''

if bytes is str:
    print('Binary parsing unsupported in this Python version')
else:

    #from logging import basicConfig, DEBUG
    from unittest import TestCase
    
    from lepl.bin.encode import dispatch_table, simple_serialiser
    from lepl.bin.literal import parse
    from lepl.bin.matchers import BEnd, Const
    from lepl.support.node import Node
    
    
    # pylint: disable-msg=C0103, C0111, C0301
    # (dude this is just a test)
    
    class MatcherTest(TestCase):
        '''
        Test whether we correctly match some data.
        '''
        
        def test_match(self):
            #basicConfig(level=DEBUG)
            
            # first, define some test data - we'll use a simple definition
            # language, but you could also construct this directly in Python
            # (Frame, Header etc are auto-generated subclasses of Node). 
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
        
            # next, define a parser for the header structure
            # this is mainly literal values, but we make the two addresses
            # big-endian integers, which will be read from the data
            
            # this looks very like "normal" lepl because it is - there's 
            # nothing in lepl that forces the data being parsed to be text. 
            
            preamble  = ~Const('0b10101010')[7]
            start     = ~Const('0b10101011')
            destn     = BEnd(6.0)                > 'destn'
            source    = BEnd(6.0)                > 'source'
            ethertype = ~Const('0800x0') 
            header    = preamble & start & destn & source & ethertype > Node
            
            # so, what do the test data look like?
#            print(mac)
    # Frame
    #  +- Header
    #  |   +- preamble BitString(b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa', 56, 0)
    #  |   +- start BitString(b'\xab', 8, 0)
    #  |   +- destn BitString(b'\x01\x02\x03\x04\x05\x06', 48, 0)
    #  |   +- source BitString(b'\x07\x08\t\n\x0b\x0c', 48, 0)
    #  |   `- ethertype BitString(b'\x08\x00', 16, 0)
    #  +- Data
    #  |   +- BitString(b'\x01', 8, 0)
    #  |   +- BitString(b'\x02', 8, 0)
    #  |   +- BitString(b'\x03', 8, 0)
    #  |   `- BitString(b'\x04', 8, 0)
    #  `- CRC
    #      `- BitString(b'\x00\x00\x00\xea', 32, 0)    
    
            # we can serialize that to a BitString        
            b = simple_serialiser(mac, dispatch_table())
            assert str(b) == 'aaaaaaaaaaaaaaab123456789abc801234000eax0/240'
    
            # and then we can parse it
            header.config.no_full_first_match()
            p = header.parse(b)[0]
#            print(p)
    # Node
    #  +- destn Int(1108152157446,48)
    #  `- source Int(7731092785932,48)
    
            # the destination address
            assert hex(p.destn[0]) == '0x10203040506'
    
            # the source address
            assert hex(p.source[0]) == '0x708090a0b0c'
