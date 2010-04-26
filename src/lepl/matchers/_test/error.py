
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
Tests for the lepl.matchers.error module.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import Literal, Error
from lepl.matchers.error import make_error
from lepl.matchers.variables import TraceVariables


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102, C0321, W0141, R0201
# (dude this is just a test)

    
class MessageTest(TestCase):
    '''
    Check generation of Error nodes.
    '''
    
    def test_simple(self):
        '''
        Test a message with no formatting.
        '''
        parser = (Literal('abc') > 'name') ** make_error('msg')
        parser.config.no_full_first_match()
        node = parser.parse('abc')[0]
        assert isinstance(node, Error)
        assert node[0] == 'msg', node[0]
        assert str(node).startswith('msg ('), str(node)
        assert isinstance(node, Exception), type(node)

    def test_formatted(self):
        '''
        Test a message with formatting.
        '''
        parser = (Literal('abc') > 'name') ** make_error('msg {stream_in}')
        parser.config.no_full_first_match()
        node = parser.parse('abc')[0]
        assert isinstance(node, Error)
        assert node[0] == 'msg abc', node[0]
        assert str(node).startswith('msg abc ('), str(node)
        assert isinstance(node, Exception), type(node)
        
    def test_bad_format(self):
        '''
        Test a message with bad formatting.
        '''
        try:
            parser = (Literal('abc') > 'name') ** make_error('msg {0}')
            parser.config.no_full_first_match()
            list(parser.match('abc'))
            assert False, 'expected error'
        except IndexError:
            pass

    def test_list(self):
        '''
        Code has an exception for handling lists.
        '''
        #basicConfig(level=DEBUG)
        with TraceVariables():
            parser = (Literal([1, 2, 3]) > 'name') ** make_error('msg {stream_in}')
        parser.config.no_full_first_match()
        node = parser.parse([1, 2, 3])[0]
        assert isinstance(node, Error)
        assert node[0] == 'msg [1, 2, 3]', node[0]
        assert str(node).startswith('msg [1, 2, 3] ('), str(node)
        assert isinstance(node, Exception), type(node)
        