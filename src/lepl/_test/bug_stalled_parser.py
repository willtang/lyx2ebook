
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
Tests for a regexp bug.
'''

# pylint: disable-msg=W0614, W0401, C0111, R0201
#@PydevCodeAnalysisIgnore


#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import *


class LeftRecursiveTest(TestCase):
    
#    def test_limited_lookahead(self):
#        '''
#        This stalls because Lookahead consumes nothing.  Can we detect this 
#        case?
#        '''
        #basicConfig(level=DEBUG)
#        
#        item     = Delayed()
#        item    += item[1:3] | ~Lookahead('\\')
#    
#        expr     = item[:2] & Drop(Eos())
##        parser = expr.string_parser(Configuration(rewriters=[memoize(LMemo)]))
#        parser = expr.get_parse_string()
#        print(parser.matcher)
#
#        parser('abc')

#    def test_plain_lookahead(self):
#        '''
#        This stalls because Lookahead consumes nothing.  Can we detect this 
#        case?
#        '''
        #basicConfig(level=DEBUG)
#        
#        item     = Delayed()
#        item    += item[1:] | ~Lookahead('\\')
#    
#        expr     = item & Drop(Eos())
#        parser = expr.get_parse_string()
#        print(parser.matcher)
#
#        parser('abc')

    def test_problem_from_regexp(self):

        item     = Delayed()
        item    += item[1:] 
        expr     = item & Drop(Eos())

        expr.config.no_full_first_match()
        parser = expr.get_parse_string()
#        print(parser.matcher)
        parser('abc')
