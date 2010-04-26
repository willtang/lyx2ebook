
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
Tests for the lepl.offside.matchers module (currently unused).
'''

from unittest import TestCase


class SimpleLanguageTest(TestCase):
    '''
    A parser for a simple language, a little like python, that uses indents.
    '''
    
    PROGRAM = \
'''
# a simple function definition
def myfunc(a, b, c) = a + b + c

# a closure
def counter_from(n) =
  def counter() =
    n = n + 1
  counter
  
# multiline argument list and a different indent size
def first(a, b,
         c) =
   a
'''

#    def parser(self):
#        
#        word = Token('[a-z_][a-z0-9_]*')
#        number = Token(Integer)
#        symbol = Token('[^a-z0-9_]')
#        
#        # any indent, entire line
#        comment = symbol('#') + Star(Any())
#        
#        atom = number | word
#        # ignore line related tokens
#        args = symbol('(') + Freeform(atom[:,symbol(',')]) + symbol(')')
#        simple_expr = ...
#        expr = Line(simple_expr + Opt(comment))
#        
#        line_comment = LineAny(comment)
#        
#        # single line function is distinct
#        func1 = \
#          Line(word('def') + word + args + symbol('=') + expr + Opt(comment))
#        func = Line(word('def') + word + args + symbol('=') + Opt(comment)) + 
#               Block((expr|func|func1)[:])
#        
#        program = (func|func1)[:]
        