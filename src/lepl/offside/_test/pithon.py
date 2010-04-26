
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
Test a Python-like grammar.
'''

# pylint: disable-msg=W0614, W0401, W0621, C0103, C0111, R0201, R0904
#@PydevCodeAnalysisIgnore

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import *


class PithonTest(TestCase):
    
    @property
    def parser(self):
        
        word = Token(Word(Lower()))
        continuation = Token(r'\\')
        symbol = Token(Any('()'))
        introduce = ~Token(':')
        comma = ~Token(',')
        
        CLine = ContinuedBLineFactory(continuation)
        
        statement = word[1:]
        args = Extend(word[:, comma]) > tuple
        function = word[1:] & ~symbol('(') & args & ~symbol(')')

        block = Delayed()
        blank = ~Line(Empty())
        comment = ~Line(Token('#.*'))
        line = (CLine(statement) | block | blank | comment) > list
        block += CLine((function | statement) & introduce) & Block(line[1:])
        
        program = (line[:] & Eos())
        program.config.default_line_aware(block_policy=rightmost).trace(True)
        return program.get_parse_string()
    
    def test_blocks(self):
        #basicConfig(level=DEBUG)
        program1 = '''
kopo fjire ifejfr
ogptkr jgitr gtr
ffjireofr(kfkorp, freopk):
  jifr fireo
  frefre jifoji
  jio frefre:
        jiforejifre fiorej
        jfore fire
        jioj
  jioj
jiojio
'''
        result = self.parser(program1)
        assert result == [[], 
                          ['kopo', 'fjire', 'ifejfr'], 
                          ['ogptkr', 'jgitr', 'gtr'], 
                          ['ffjireofr', ('kfkorp', 'freopk'), 
                           ['jifr', 'fireo'], 
                           ['frefre', 'jifoji'], 
                           ['jio', 'frefre',
                            ['jiforejifre', 'fiorej'], 
                            ['jfore', 'fire'], 
                            ['jioj']], 
                           ['jioj']], 
                          ['jiojio']], result
        
    def test_no_lexer(self):
        #basicConfig(level=DEBUG)
        try:
            self.parser('123')
            assert False, 'expected exception'
        except LexerError as error:
            assert str(error) == 'No lexer for \'123\' at ' \
                'line 1 character 0 of str: \'123\'.', str(error)
                
    def test_extend(self):
        #basicConfig(level=DEBUG)
        result = self.parser('''
def foo(abc, def,
        ghi):
  jgiog
''')
        assert result == [[], 
                          ['def', 'foo', ('abc', 'def', 'ghi'), 
                           ['jgiog']]], result
        
    def test_cline(self):
        #basicConfig(level=DEBUG)
        result = self.parser('''
this is a single \
  line spread over \
    many actual \
lines
and this is another
''')
        assert result == [[], 
                          ['this', 'is', 'a', 'single', 'line', 'spread', 
                           'over', 'many', 'actual', 'lines'], 
                           ['and', 'this', 'is', 'another']], result
                           
    def test_blanks(self):
        #basicConfig(level=DEBUG)
        result = self.parser('''
def foo():
  a blank line can be
  
  inside a block
  
or can separate blocks
''')
        assert result == [[], 
                          ['def', 'foo', (), 
                           ['a', 'blank', 'line', 'can', 'be'], 
                           [], 
                           ['inside', 'a', 'block'], 
                           []
                          ], 
                          ['or', 'can', 'separate', 'blocks']
                         ], result
                           
    def test_comments(self):
        #basicConfig(level=DEBUG)
        result = self.parser('''
# a comment here
def foo():
  # one here
  contents
# wrong indentation!
  more content''')
        assert result == [[], [], 
                          ['def', 'foo', (), 
                           [], 
                           ['contents'], 
                           [], 
                           ['more', 'content']]], result
                           
    def test_all(self):
        #basicConfig(level=DEBUG)
        result = self.parser('''
this is a grammar with a similar 
line structure to python

# it supports comments
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
  # and we can have blank lines inside a block:
  
  like this
''')
        assert result == \
        [ [], 
          ['this', 'is', 'a', 'grammar', 'with', 'a', 'similar'], 
          ['line', 'structure', 'to', 'python'], 
          [], 
          [], 
          ['if', 'something', 
            ['then', 'we', 'indent']], 
          ['else', 
            ['something', 'else'], 
          []], 
          ['def', 'function', ('a', 'b', 'c'), 
            ['we', 'can', 'nest', 'blocks', 
              ['like', 'this']], 
            ['and', 'we', 'can', 'also', 'have', 'explicit', 
             'continuations', 'with', 'any', 'indentation'], 
            []], 
          ['same', 'for', ('argument', 'lists'), 
            ['which', 'do', 'not', 'need', 'the'], 
            ['continuation', 'marker'],
            [],
            [],
            ['like', 'this']]], result
