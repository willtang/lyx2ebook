
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103
#@PydevCodeAnalysisIgnore
# (the code style is for documentation, not "real")

'''
Examples from the documentation.
'''

#from logging import basicConfig, getLogger, DEBUG, INFO

from lepl import *
from lepl._example.support import Example


class LexerExample(Example):
    
    def test_add(self):
        
        #basicConfig(level=DEBUG)
        #basicConfig(level=INFO)
        #getLogger('lepl.lexer.stream.lexed_simple_stream').setLevel(DEBUG)
        
        value = Token(UnsignedFloat())
        symbol = Token('[^0-9a-zA-Z \t\r\n]')
        number = value >> float
        add = number & ~symbol('+') & number > sum
        self.examples([
            (lambda: add.parse('12+30'), '[42.0]')])

    def test_bad(self):
        
        #basicConfig(level=DEBUG)
        #basicConfig(level=INFO)
        #getLogger('lepl.lexer.stream.lexed_simple_stream').setLevel(DEBUG)
        
        value = Token(SignedFloat())
        symbol = Token('[^0-9a-zA-Z \t\r\n]')
        number = value >> float
        add = number & ~symbol('+') & number > sum
        add.config.no_full_first_match()
        self.examples([
            (lambda: add.parse('12+30'), 'None')])

