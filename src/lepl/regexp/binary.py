
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
A proof-of-concept regexp implementation for binary data strings.

The hope is that one day we can parse binary data in the same way as text...
'''

from lepl.regexp.core import Compiler, Labelled
from lepl.regexp.str import StrAlphabet, make_str_parser


class BinaryAlphabet(StrAlphabet):
    '''
    An alphabet for binary strings.
    '''
    
    # pylint: disable-msg=E1002
    # (pylint bug?  this chains back to a new style abc)
    def __init__(self):
        super(BinaryAlphabet, self).__init__(0, 1)
    
    def before(self, char): 
        '''
        Must return the character before c in the alphabet.  Never called with
        min (assuming input data are in range).
        ''' 
        return char-1
    
    def after(self, char): 
        '''
        Must return the character after c in the alphabet.  Never called with
        max (assuming input data are in range).
        ''' 
        return char+1
    
    def from_char(self, char):
        '''
        Convert to 0 or 1.
        '''
        char = int(char)
        assert char in (0, 1)
        return char


BINARY = BinaryAlphabet()


# pylint: disable-msg=W0105, C0103
__compiled_binary_parser = make_str_parser(BINARY)
'''
Cache the parser to allow efficient re-use.
'''

def binary_single_parser(label, text):
    '''
    Parse a binary regular expression, returning the associated Regexp.
    '''
    return Compiler.single(BINARY,
                Labelled(label, __compiled_binary_parser(text), BINARY))


def binary_parser(*regexps):
    '''
    Parse a set of binary regular expressions, returning the associated Regexp.
    '''
    return Compiler.multiple(BINARY,
                [Labelled(label, __compiled_binary_parser(text), BINARY)
                 for (label, text) in regexps])


