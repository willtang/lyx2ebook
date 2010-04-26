
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
Show how the BLine and Block tokens can be used
'''

# pylint: disable-msg=W0401, W0614, W0621, C0103, C0111, R0201, C0301, R0904
#@PydevCodeAnalysisIgnore


from logging import basicConfig, DEBUG

from lepl import *
from lepl._example.support import Example


class OffsideExample(Example):
    
    def test_offside(self):
        #basicConfig(level=DEBUG)
        introduce = ~Token(':')
        word = Token(Word(Lower()))
        scope = Delayed()
        line = (BLine(word[:] | Empty()) > list) | scope
        scope += BLine(word[:] & introduce) & Block(line[:]) > list
        program = line[:]
        program.config.default_line_aware(block_policy=2)
        parser = program.get_parse_string()
        self.examples([(lambda: parser('''
abc def
ghijk:
  mno pqr:
    stuv
  wx yz
'''), "[[], ['abc', 'def'], ['ghijk', ['mno', 'pqr', ['stuv']], ['wx', 'yz']]]")])

    def test_offside2(self):
        #basicConfig(level=DEBUG)
        introduce = ~Token(':')
        word = Token(Word(Lower()))
        statement = Delayed()
        simple = BLine(word[:])
        empty = Line(Empty())
        block = BLine(word[:] & introduce) & Block(statement[:])
        statement += (simple | empty | block) > list
        program = statement[:]
        program.config.default_line_aware(block_policy=2)
        parser = program.get_parse_string()
        self.examples([(lambda: parser('''
abc def
ghijk:
  mno pqr:
    stuv
  wx yz
'''),
"[[], ['abc', 'def'], ['ghijk', ['mno', 'pqr', ['stuv']], ['wx', 'yz']]]")])
        
   
    def test_pithon(self):
        #basicConfig(level=DEBUG)
        
        word = Token(Word(Lower()))
        continuation = Token(r'\\')
        symbol = Token(Any('()'))
        introduce = ~Token(':')
        comma = ~Token(',')

        CLine = ContinuedBLineFactory(continuation)
                
        statement = Delayed()

        empty = Line(Empty())
        simple = CLine(word[1:])
        ifblock = CLine(word[1:] & introduce) & Block(statement[1:])

        args = Extend(word[:, comma]) > tuple
        fundef = word[1:] & ~symbol('(') & args & ~symbol(')')
        function = CLine(fundef & introduce) & Block(statement[1:])
        
        statement += (empty | simple | ifblock | function) > list
        program = statement[:]
        
        program.config.default_line_aware(block_policy=2).no_full_first_match()
        parser = program.get_parse_string()

        self.examples([(lambda: parser('''
this is a grammar with a similar 
line structure to python

if something:
  then we indent
else:
  something else
  
def function(a, b, c):
  we can nest blocks:
    like this
  and we can also \
    have explicit continuations \
    with \
any \
       indentation
       
same for (argument,
          lists):
  which do not need the
  continuation marker
'''), 
"[[], ['this', 'is', 'a', 'grammar', 'with', 'a', 'similar'], "
"['line', 'structure', 'to', 'python'], [], "
"['if', 'something', ['then', 'we', 'indent']], "
"['else', ['something', 'else'], []], "
"['def', 'function', ('a', 'b', 'c'), "
"['we', 'can', 'nest', 'blocks', ['like', 'this']], "
"['and', 'we', 'can', 'also', 'have', 'explicit', 'continuations', "
"'with', 'any', 'indentation'], []], "
"['same', 'for', ('argument', 'lists'), "
"['which', 'do', 'not', 'need', 'the'], "
"['continuation', 'marker']]]")])
        
        
    def test_initial_offset(self):
        #basicConfig(level=DEBUG)
        word = Token(Word(Lower()))
        line = Delayed()
        block = Block(line[1:])
        # this also tests left recursion and blocks
        line += BLine(word | Empty()) | block
        program = line[:]
        program.config.default_line_aware(block_policy=4, block_start=3).no_full_first_match()
        parser = program.get_parse_string()
        result = parser('''
   foo
       bar
''')
        assert result == [], result
         