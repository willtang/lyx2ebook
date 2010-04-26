
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,R0914
#@PydevCodeAnalysisIgnore
# (the code style is for documentation, not "real")

'''
Examples from the documentation.
'''

#from logging import basicConfig, DEBUG

from lepl import *
from lepl._example.support import Example


class ArgsExample(Example):
    
    def test_args(self):
        #basicConfig(level=DEBUG)
    
        comma  = Drop(',') 
        none   = Literal('None')                        >> (lambda x: None)
        bool   = (Literal('True') | Literal('False'))   >> (lambda x: x == 'True')
        ident  = Word(Letter() | '_', 
                      Letter() | '_' | Digit())
        float_ = Float()                                >> float 
        int_   = Integer()                              >> int
        str_   = String() | String("'")
        item   = str_ | int_ | float_ | none | bool | ident       
        with Separator(~Regexp(r'\s*')):
            value  = Delayed()
            list_  = Drop('[') & value[:, comma] & Drop(']') > list
            tuple_ = Drop('(') & value[:, comma] & Drop(')') > tuple
            value += list_ | tuple_ | item  
            arg    = value                                   >> 'arg'
            karg   = ((ident & Drop('=') & value)            > tuple) >> 'karg'
            expr   = (karg | arg)[:, comma] & Drop(Eos())    > Node
            
        parser = expr.get_parse_string()
        ast = parser('True, type=rect, sizes=[3, 4], coords = ([1,2],[3,4])')
        self.examples([(lambda: ast[0], '''Node
 +- arg True
 +- karg ('type', 'rect')
 +- karg ('sizes', [3, 4])
 `- karg ('coords', ([1, 2], [3, 4]))'''),
                       (lambda: ast[0].arg, '[True]'),
                       (lambda: ast[0].karg, 
                        "[('type', 'rect'), ('sizes', [3, 4]), ('coords', ([1, 2], [3, 4]))]")])
        
        ast = parser('None, str="a string"')
        self.examples([(lambda: ast[0], """Node
 +- arg None
 `- karg ('str', 'a string')"""),
                       (lambda: ast[0].arg, "[None]"),
                       (lambda: ast[0].karg, "[('str', 'a string')]")])
