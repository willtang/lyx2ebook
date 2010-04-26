
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
Tests for the lepl.matchers.core module.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl._test.base import BaseTest, assert_str
from lepl.matchers.combine import And, Or
from lepl.matchers.core import Any, Literal, Eof, Regexp, Delayed, Lookahead, \
    Consumer, PostMatch
from lepl.matchers.derived import Word, Digit, Integer, Columns, Drop
from lepl.matchers.monitor import Commit
from lepl.support.node import Node


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102, C0321, W0141, R0201, R0904, R0903
# (dude this is just a test)

    
class AnyTest(TestCase):
    
    def test_any(self):
        matcher = Any()
        result = matcher.parse('a')
        assert result, result


class AndTest(BaseTest):

    def test_simple(self):
        #basicConfig(level=DEBUG)
        self.assert_join([1], Any(), [[1]])
        self.assert_join([1,2], And(Any(), Any()), [[1, 2]])
        self.assert_join([1,2,3], And(Any(), Any()), [[1, 2]])
        self.assert_join([1], And(Any(), Any()), [])
        
    def test_and(self):
        #basicConfig(level=DEBUG)
        self.assert_join([1,2], Any() & Any(), [[1, 2]])
        self.assert_join([1,2,3], Any() & Any(), [[1, 2]])
        self.assert_join([1,2,3], Any() & Any() & Any(), [[1, 2, 3]])
        self.assert_join([1], Any() & Any(), [])
        
    def assert_join(self, stream, match, target):
        match.config.no_full_first_match()
        result = list(match.parse_items_all(stream, sub_list=False))
        assert target == result, result

    def test_add(self):
        #basicConfig(level=DEBUG)
        self.assert_list(['1','2'], Any() + Any(), [['12']], 
                         sub_list=False, join=''.join)
        self.assert_list(['1','2','3'], Any() + Any(), [['12']], 
                         sub_list=False, join=''.join)
        self.assert_list(['1','2','3'], Any() + Any() + Any(), [['123']], 
                         sub_list=False, join=''.join)
        self.assert_list(['1'], Any() + Any(), [])
    
    
class CoercionTest(BaseTest):
    
    def test_right(self):
        #basicConfig(level=DEBUG)
        self.assert_direct('12', Any() + '2', [['12']])
         
    def test_left(self):
        #basicConfig(level=DEBUG)
        self.assert_direct('12', '1' + Any(), [['12']])
         

class OrTest(BaseTest):

    def test_simple(self):
        self.assert_direct('a', Or(Any('x'), Any('a'), Any()), [['a'],['a']])

    def test_bar(self):
        self.assert_direct('a', Any('x') | Any('a') | Any(), [['a'],['a']])
        
        
#class FirstTest(BaseTest):
#    
#    def test_first(self):
#        s = Space()
#        aline = '#define' & ~s[1:] & Word() & ~s[1:] & Word() > list
#        bline = AnyBut(s[0:] & Newline())[1:]
#        line = aline % ~bline
#        parser = line[0:,~(s[0:] & Newline())]
#        parser.config.no_full_first_match()
#        parser.config.clear()
#        n = len(list(parser.match('#define A 1\ncrap n stuff\n#define B 22\n')))
#        assert n == 16, n
#        r = parser.parse('#define A 1\ncrap n stuff\n#define B 22\n')
#        assert r == [['#define', 'A', '1'], ['#define', 'B', '22']], r


class LookaheadTest(BaseTest):
    
    def test_simple(self):
        self.assert_direct('ab', Any() + Lookahead('c') + Any(), [])
        self.assert_direct('ab', Any() + Lookahead('b') + Any(), [['ab']])

    def test_bang(self):
        self.assert_direct('ab', Any() + ~Lookahead('c') + Any(), [['ab']])
        self.assert_direct('ab', Any() + ~Lookahead('b') + Any(), [])


class CommitTest(BaseTest):
    
    def test_commit(self):
        self.assert_direct('abcd', 
            (Any()[0::'b'] + (Literal('d') | 
                              Literal('cd') + Commit() | 
                              Literal('bcd')) + Eof()), 
            [['abcd'], ['abcd']])
        

class RegexpTest(BaseTest):
    
    def test_group(self):
        self.assert_direct('  123x', Regexp(r'\s*\d+') & Any(), [['  123', 'x']])
        
    def test_groups(self):
        self.assert_direct('  123x', Regexp(r'\s*(\d)(\d+)') & Any(), [['1','23','x']])


class WordTest(BaseTest):
    
    def test_phone(self):
        self.assert_direct('andrew, 3333253', Word() / ',' / Integer() / Eof(), 
                           [['andrew', ',', ' ', '3333253']])
        
        
class EofTest(BaseTest):
    
    def test_eof(self):
        self.assert_direct('foo ', 'foo' / Eof(), [['foo', ' ']])
        

class LiteralTest(BaseTest):
    
    def test_literal(self):
        self.assert_direct('foo ', Literal('foo'), [['foo']])
        
        
class TransformTest(BaseTest):
    
    @staticmethod
    def mkappend(x):
        return lambda a: a + x
    
    def test_apply(self):
        # note extra list 
        self.assert_direct('foo ', Literal('foo') > self.mkappend(['b']), [[['foo', 'b']]])
        
    def test_kapply(self):
        # note extra list 
        self.assert_direct('foo ', Literal('foo') >> self.mkappend('b'), [['foob']])
        
    def test_nested(self):
        # note extra list 
        self.assert_direct('foo ', 
                           (Literal('foo') >> self.mkappend('b')) > self.mkappend(['c']), 
                           [[['foob', 'c']]])
        
        
class StrTest(TestCase):
    
    def assert_same(self, text1, text2):
        assert_str(text1, text2)
#        assert self.__clean(text1) == self.__clean(text2), text1
    
    def __clean(self, text):
        depth = 0
        result = ''
        for c in text:
            if c == '<':
                depth += 1
            elif c == '>':
                depth -= 1
            elif depth == 0:
                result += c
        return result

    def test_str(self):
        class Term(Node): pass
        class Factor(Node): pass
        class Expression(Node): pass

        expression  = Delayed()
        number      = Digit()[1:,...]                      > 'number'
        term        = (number | '(' / expression / ')')    > Term
        muldiv      = Any('*/')                            > 'operator'
        factor      = (term / (muldiv / term)[0::])        > Factor
        addsub      = Any('+-')                            > 'operator'
        expression += (factor / (addsub / factor)[0::])    > Expression

        description = repr(expression)
        self.assert_same(description, r'''Delayed(matcher=Transform:<apply>(
 TransformableTrampolineWrapper<And:<>>(
  Transform:<apply>(
   TransformableTrampolineWrapper<And:<>>(
    Transform:<apply>(
     TransformableTrampolineWrapper<Or:<>>(
      Transform:<apply>(
       Transform:<add>(
        TrampolineWrapper<DepthFirst>(
         start=1,
         stop=None,
         rest=FunctionWrapper<Any:<>>('0123456789'),
         first=FunctionWrapper<Any:<>>('0123456789')),
        TransformationWrapper(<add>)),
       TransformationWrapper(<apply>)),
      TransformableTrampolineWrapper<And:<>>(
       TransformableTrampolineWrapper<And:<>>(
        FunctionWrapper<Literal:<>>('('),
        Transform:<add>(
         TrampolineWrapper<DepthFirst>(
          start=0,
          stop=None,
          rest=FunctionWrapper<Any:<>>(' \t'),
          first=FunctionWrapper<Any:<>>(' \t')),
         TransformationWrapper(<add>)),
        [Delayed]),
       Transform:<add>(
        TrampolineWrapper<DepthFirst>(
         start=0,
         stop=None,
         rest=FunctionWrapper<Any:<>>(' \t'),
         first=FunctionWrapper<Any:<>>(' \t')),
        TransformationWrapper(<add>)),
       FunctionWrapper<Literal:<>>(')'))),
     TransformationWrapper(<apply>)),
    Transform:<add>(
     TrampolineWrapper<DepthFirst>(
      start=0,
      stop=None,
      rest=FunctionWrapper<Any:<>>(' \t'),
      first=FunctionWrapper<Any:<>>(' \t')),
     TransformationWrapper(<add>)),
    TrampolineWrapper<DepthFirst>(
     start=0,
     stop=None,
     rest=TransformableTrampolineWrapper<And:<>>(
      Transform:<apply>(
       FunctionWrapper<Any:<>>('*/'),
       TransformationWrapper(<apply>)),
      Transform:<add>(
       TrampolineWrapper<DepthFirst>(
        start=0,
        stop=None,
        rest=FunctionWrapper<Any:<>>(' \t'),
        first=FunctionWrapper<Any:<>>(' \t')),
       TransformationWrapper(<add>)),
      Transform:<apply>(
       TransformableTrampolineWrapper<Or:<>>(
        Transform:<apply>(
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=1,
           stop=None,
           rest=FunctionWrapper<Any:<>>('0123456789'),
           first=FunctionWrapper<Any:<>>('0123456789')),
          TransformationWrapper(<add>)),
         TransformationWrapper(<apply>)),
        TransformableTrampolineWrapper<And:<>>(
         TransformableTrampolineWrapper<And:<>>(
          FunctionWrapper<Literal:<>>('('),
          Transform:<add>(
           TrampolineWrapper<DepthFirst>(
            start=0,
            stop=None,
            rest=FunctionWrapper<Any:<>>(' \t'),
            first=FunctionWrapper<Any:<>>(' \t')),
           TransformationWrapper(<add>)),
          [Delayed]),
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=0,
           stop=None,
           rest=FunctionWrapper<Any:<>>(' \t'),
           first=FunctionWrapper<Any:<>>(' \t')),
          TransformationWrapper(<add>)),
         FunctionWrapper<Literal:<>>(')'))),
       TransformationWrapper(<apply>))),
     first=TransformableTrampolineWrapper<And:<>>(
      Transform:<apply>(
       FunctionWrapper<Any:<>>('*/'),
       TransformationWrapper(<apply>)),
      Transform:<add>(
       TrampolineWrapper<DepthFirst>(
        start=0,
        stop=None,
        rest=FunctionWrapper<Any:<>>(' \t'),
        first=FunctionWrapper<Any:<>>(' \t')),
       TransformationWrapper(<add>)),
      Transform:<apply>(
       TransformableTrampolineWrapper<Or:<>>(
        Transform:<apply>(
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=1,
           stop=None,
           rest=FunctionWrapper<Any:<>>('0123456789'),
           first=FunctionWrapper<Any:<>>('0123456789')),
          TransformationWrapper(<add>)),
         TransformationWrapper(<apply>)),
        TransformableTrampolineWrapper<And:<>>(
         TransformableTrampolineWrapper<And:<>>(
          FunctionWrapper<Literal:<>>('('),
          Transform:<add>(
           TrampolineWrapper<DepthFirst>(
            start=0,
            stop=None,
            rest=FunctionWrapper<Any:<>>(' \t'),
            first=FunctionWrapper<Any:<>>(' \t')),
           TransformationWrapper(<add>)),
          [Delayed]),
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=0,
           stop=None,
           rest=FunctionWrapper<Any:<>>(' \t'),
           first=FunctionWrapper<Any:<>>(' \t')),
          TransformationWrapper(<add>)),
         FunctionWrapper<Literal:<>>(')'))),
       TransformationWrapper(<apply>))))),
   TransformationWrapper(<apply>)),
  Transform:<add>(
   TrampolineWrapper<DepthFirst>(
    start=0,
    stop=None,
    rest=FunctionWrapper<Any:<>>(' \t'),
    first=FunctionWrapper<Any:<>>(' \t')),
   TransformationWrapper(<add>)),
  TrampolineWrapper<DepthFirst>(
   start=0,
   stop=None,
   rest=TransformableTrampolineWrapper<And:<>>(
    Transform:<apply>(
     FunctionWrapper<Any:<>>('+-'),
     TransformationWrapper(<apply>)),
    Transform:<add>(
     TrampolineWrapper<DepthFirst>(
      start=0,
      stop=None,
      rest=FunctionWrapper<Any:<>>(' \t'),
      first=FunctionWrapper<Any:<>>(' \t')),
     TransformationWrapper(<add>)),
    Transform:<apply>(
     TransformableTrampolineWrapper<And:<>>(
      Transform:<apply>(
       TransformableTrampolineWrapper<Or:<>>(
        Transform:<apply>(
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=1,
           stop=None,
           rest=FunctionWrapper<Any:<>>('0123456789'),
           first=FunctionWrapper<Any:<>>('0123456789')),
          TransformationWrapper(<add>)),
         TransformationWrapper(<apply>)),
        TransformableTrampolineWrapper<And:<>>(
         TransformableTrampolineWrapper<And:<>>(
          FunctionWrapper<Literal:<>>('('),
          Transform:<add>(
           TrampolineWrapper<DepthFirst>(
            start=0,
            stop=None,
            rest=FunctionWrapper<Any:<>>(' \t'),
            first=FunctionWrapper<Any:<>>(' \t')),
           TransformationWrapper(<add>)),
          [Delayed]),
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=0,
           stop=None,
           rest=FunctionWrapper<Any:<>>(' \t'),
           first=FunctionWrapper<Any:<>>(' \t')),
          TransformationWrapper(<add>)),
         FunctionWrapper<Literal:<>>(')'))),
       TransformationWrapper(<apply>)),
      Transform:<add>(
       TrampolineWrapper<DepthFirst>(
        start=0,
        stop=None,
        rest=FunctionWrapper<Any:<>>(' \t'),
        first=FunctionWrapper<Any:<>>(' \t')),
       TransformationWrapper(<add>)),
      TrampolineWrapper<DepthFirst>(
       start=0,
       stop=None,
       rest=TransformableTrampolineWrapper<And:<>>(
        Transform:<apply>(
         FunctionWrapper<Any:<>>('*/'),
         TransformationWrapper(<apply>)),
        Transform:<add>(
         TrampolineWrapper<DepthFirst>(
          start=0,
          stop=None,
          rest=FunctionWrapper<Any:<>>(' \t'),
          first=FunctionWrapper<Any:<>>(' \t')),
         TransformationWrapper(<add>)),
        Transform:<apply>(
         TransformableTrampolineWrapper<Or:<>>(
          Transform:<apply>(
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=1,
             stop=None,
             rest=FunctionWrapper<Any:<>>('0123456789'),
             first=FunctionWrapper<Any:<>>('0123456789')),
            TransformationWrapper(<add>)),
           TransformationWrapper(<apply>)),
          TransformableTrampolineWrapper<And:<>>(
           TransformableTrampolineWrapper<And:<>>(
            FunctionWrapper<Literal:<>>('('),
            Transform:<add>(
             TrampolineWrapper<DepthFirst>(
              start=0,
              stop=None,
              rest=FunctionWrapper<Any:<>>(' \t'),
              first=FunctionWrapper<Any:<>>(' \t')),
             TransformationWrapper(<add>)),
            [Delayed]),
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=0,
             stop=None,
             rest=FunctionWrapper<Any:<>>(' \t'),
             first=FunctionWrapper<Any:<>>(' \t')),
            TransformationWrapper(<add>)),
           FunctionWrapper<Literal:<>>(')'))),
         TransformationWrapper(<apply>))),
       first=TransformableTrampolineWrapper<And:<>>(
        Transform:<apply>(
         FunctionWrapper<Any:<>>('*/'),
         TransformationWrapper(<apply>)),
        Transform:<add>(
         TrampolineWrapper<DepthFirst>(
          start=0,
          stop=None,
          rest=FunctionWrapper<Any:<>>(' \t'),
          first=FunctionWrapper<Any:<>>(' \t')),
         TransformationWrapper(<add>)),
        Transform:<apply>(
         TransformableTrampolineWrapper<Or:<>>(
          Transform:<apply>(
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=1,
             stop=None,
             rest=FunctionWrapper<Any:<>>('0123456789'),
             first=FunctionWrapper<Any:<>>('0123456789')),
            TransformationWrapper(<add>)),
           TransformationWrapper(<apply>)),
          TransformableTrampolineWrapper<And:<>>(
           TransformableTrampolineWrapper<And:<>>(
            FunctionWrapper<Literal:<>>('('),
            Transform:<add>(
             TrampolineWrapper<DepthFirst>(
              start=0,
              stop=None,
              rest=FunctionWrapper<Any:<>>(' \t'),
              first=FunctionWrapper<Any:<>>(' \t')),
             TransformationWrapper(<add>)),
            [Delayed]),
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=0,
             stop=None,
             rest=FunctionWrapper<Any:<>>(' \t'),
             first=FunctionWrapper<Any:<>>(' \t')),
            TransformationWrapper(<add>)),
           FunctionWrapper<Literal:<>>(')'))),
         TransformationWrapper(<apply>))))),
     TransformationWrapper(<apply>))),
   first=TransformableTrampolineWrapper<And:<>>(
    Transform:<apply>(
     FunctionWrapper<Any:<>>('+-'),
     TransformationWrapper(<apply>)),
    Transform:<add>(
     TrampolineWrapper<DepthFirst>(
      start=0,
      stop=None,
      rest=FunctionWrapper<Any:<>>(' \t'),
      first=FunctionWrapper<Any:<>>(' \t')),
     TransformationWrapper(<add>)),
    Transform:<apply>(
     TransformableTrampolineWrapper<And:<>>(
      Transform:<apply>(
       TransformableTrampolineWrapper<Or:<>>(
        Transform:<apply>(
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=1,
           stop=None,
           rest=FunctionWrapper<Any:<>>('0123456789'),
           first=FunctionWrapper<Any:<>>('0123456789')),
          TransformationWrapper(<add>)),
         TransformationWrapper(<apply>)),
        TransformableTrampolineWrapper<And:<>>(
         TransformableTrampolineWrapper<And:<>>(
          FunctionWrapper<Literal:<>>('('),
          Transform:<add>(
           TrampolineWrapper<DepthFirst>(
            start=0,
            stop=None,
            rest=FunctionWrapper<Any:<>>(' \t'),
            first=FunctionWrapper<Any:<>>(' \t')),
           TransformationWrapper(<add>)),
          [Delayed]),
         Transform:<add>(
          TrampolineWrapper<DepthFirst>(
           start=0,
           stop=None,
           rest=FunctionWrapper<Any:<>>(' \t'),
           first=FunctionWrapper<Any:<>>(' \t')),
          TransformationWrapper(<add>)),
         FunctionWrapper<Literal:<>>(')'))),
       TransformationWrapper(<apply>)),
      Transform:<add>(
       TrampolineWrapper<DepthFirst>(
        start=0,
        stop=None,
        rest=FunctionWrapper<Any:<>>(' \t'),
        first=FunctionWrapper<Any:<>>(' \t')),
       TransformationWrapper(<add>)),
      TrampolineWrapper<DepthFirst>(
       start=0,
       stop=None,
       rest=TransformableTrampolineWrapper<And:<>>(
        Transform:<apply>(
         FunctionWrapper<Any:<>>('*/'),
         TransformationWrapper(<apply>)),
        Transform:<add>(
         TrampolineWrapper<DepthFirst>(
          start=0,
          stop=None,
          rest=FunctionWrapper<Any:<>>(' \t'),
          first=FunctionWrapper<Any:<>>(' \t')),
         TransformationWrapper(<add>)),
        Transform:<apply>(
         TransformableTrampolineWrapper<Or:<>>(
          Transform:<apply>(
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=1,
             stop=None,
             rest=FunctionWrapper<Any:<>>('0123456789'),
             first=FunctionWrapper<Any:<>>('0123456789')),
            TransformationWrapper(<add>)),
           TransformationWrapper(<apply>)),
          TransformableTrampolineWrapper<And:<>>(
           TransformableTrampolineWrapper<And:<>>(
            FunctionWrapper<Literal:<>>('('),
            Transform:<add>(
             TrampolineWrapper<DepthFirst>(
              start=0,
              stop=None,
              rest=FunctionWrapper<Any:<>>(' \t'),
              first=FunctionWrapper<Any:<>>(' \t')),
             TransformationWrapper(<add>)),
            [Delayed]),
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=0,
             stop=None,
             rest=FunctionWrapper<Any:<>>(' \t'),
             first=FunctionWrapper<Any:<>>(' \t')),
            TransformationWrapper(<add>)),
           FunctionWrapper<Literal:<>>(')'))),
         TransformationWrapper(<apply>))),
       first=TransformableTrampolineWrapper<And:<>>(
        Transform:<apply>(
         FunctionWrapper<Any:<>>('*/'),
         TransformationWrapper(<apply>)),
        Transform:<add>(
         TrampolineWrapper<DepthFirst>(
          start=0,
          stop=None,
          rest=FunctionWrapper<Any:<>>(' \t'),
          first=FunctionWrapper<Any:<>>(' \t')),
         TransformationWrapper(<add>)),
        Transform:<apply>(
         TransformableTrampolineWrapper<Or:<>>(
          Transform:<apply>(
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=1,
             stop=None,
             rest=FunctionWrapper<Any:<>>('0123456789'),
             first=FunctionWrapper<Any:<>>('0123456789')),
            TransformationWrapper(<add>)),
           TransformationWrapper(<apply>)),
          TransformableTrampolineWrapper<And:<>>(
           TransformableTrampolineWrapper<And:<>>(
            FunctionWrapper<Literal:<>>('('),
            Transform:<add>(
             TrampolineWrapper<DepthFirst>(
              start=0,
              stop=None,
              rest=FunctionWrapper<Any:<>>(' \t'),
              first=FunctionWrapper<Any:<>>(' \t')),
             TransformationWrapper(<add>)),
            [Delayed]),
           Transform:<add>(
            TrampolineWrapper<DepthFirst>(
             start=0,
             stop=None,
             rest=FunctionWrapper<Any:<>>(' \t'),
             first=FunctionWrapper<Any:<>>(' \t')),
            TransformationWrapper(<add>)),
           FunctionWrapper<Literal:<>>(')'))),
         TransformationWrapper(<apply>))))),
     TransformationWrapper(<apply>))))),
 TransformationWrapper(<apply>)))''')
        parser = expression.get_parse()
        description = parser.matcher.tree()
        self.assert_same(description, r"""TransformableTrampolineWrapper
 +- Transform
 |   +- Delayed
 |   |   `- matcher TransformableTrampolineWrapper
 |   |       +- TransformableTrampolineWrapper
 |   |       |   +- TransformableTrampolineWrapper
 |   |       |   |   +- NfaRegexp
 |   |       |   |   |   +- Sequence(...)
 |   |       |   |   |   `- alphabet <Unicode>
 |   |       |   |   `- TransformableTrampolineWrapper
 |   |       |   |       +- FunctionWrapper
 |   |       |   |       |   `- '('
 |   |       |   |       +- NfaRegexp
 |   |       |   |       |   +- Sequence(...)
 |   |       |   |       |   `- alphabet <Unicode>
 |   |       |   |       +- Transform
 |   |       |   |       |   +- <loop>
 |   |       |   |       |   `- TransformationWrapper(<apply>)
 |   |       |   |       +- NfaRegexp
 |   |       |   |       |   +- Sequence(...)
 |   |       |   |       |   `- alphabet <Unicode>
 |   |       |   |       `- FunctionWrapper
 |   |       |   |           `- ')'
 |   |       |   +- NfaRegexp
 |   |       |   |   +- Sequence(...)
 |   |       |   |   `- alphabet <Unicode>
 |   |       |   `- TrampolineWrapper
 |   |       |       +- start 0
 |   |       |       +- stop None
 |   |       |       +- rest TransformableTrampolineWrapper
 |   |       |       |   +- FunctionWrapper
 |   |       |       |   |   `- '*/'
 |   |       |       |   +- NfaRegexp
 |   |       |       |   |   +- Sequence(...)
 |   |       |       |   |   `- alphabet <Unicode>
 |   |       |       |   `- TransformableTrampolineWrapper
 |   |       |       |       +- NfaRegexp
 |   |       |       |       |   +- Sequence(...)
 |   |       |       |       |   `- alphabet <Unicode>
 |   |       |       |       `- TransformableTrampolineWrapper
 |   |       |       |           +- FunctionWrapper
 |   |       |       |           |   `- '('
 |   |       |       |           +- NfaRegexp
 |   |       |       |           |   +- Sequence(...)
 |   |       |       |           |   `- alphabet <Unicode>
 |   |       |       |           +- Transform
 |   |       |       |           |   +- <loop>
 |   |       |       |           |   `- TransformationWrapper(<apply>)
 |   |       |       |           +- NfaRegexp
 |   |       |       |           |   +- Sequence(...)
 |   |       |       |           |   `- alphabet <Unicode>
 |   |       |       |           `- FunctionWrapper
 |   |       |       |               `- ')'
 |   |       |       `- first TransformableTrampolineWrapper
 |   |       |           +- FunctionWrapper
 |   |       |           |   `- '*/'
 |   |       |           +- NfaRegexp
 |   |       |           |   +- Sequence(...)
 |   |       |           |   `- alphabet <Unicode>
 |   |       |           `- TransformableTrampolineWrapper
 |   |       |               +- NfaRegexp
 |   |       |               |   +- Sequence(...)
 |   |       |               |   `- alphabet <Unicode>
 |   |       |               `- TransformableTrampolineWrapper
 |   |       |                   +- FunctionWrapper
 |   |       |                   |   `- '('
 |   |       |                   +- NfaRegexp
 |   |       |                   |   +- Sequence(...)
 |   |       |                   |   `- alphabet <Unicode>
 |   |       |                   +- Transform
 |   |       |                   |   +- <loop>
 |   |       |                   |   `- TransformationWrapper(<apply>)
 |   |       |                   +- NfaRegexp
 |   |       |                   |   +- Sequence(...)
 |   |       |                   |   `- alphabet <Unicode>
 |   |       |                   `- FunctionWrapper
 |   |       |                       `- ')'
 |   |       +- NfaRegexp
 |   |       |   +- Sequence(...)
 |   |       |   `- alphabet <Unicode>
 |   |       `- TrampolineWrapper
 |   |           +- start 0
 |   |           +- stop None
 |   |           +- rest TransformableTrampolineWrapper
 |   |           |   +- FunctionWrapper
 |   |           |   |   `- '+-'
 |   |           |   +- NfaRegexp
 |   |           |   |   +- Sequence(...)
 |   |           |   |   `- alphabet <Unicode>
 |   |           |   `- TransformableTrampolineWrapper
 |   |           |       +- TransformableTrampolineWrapper
 |   |           |       |   +- NfaRegexp
 |   |           |       |   |   +- Sequence(...)
 |   |           |       |   |   `- alphabet <Unicode>
 |   |           |       |   `- TransformableTrampolineWrapper
 |   |           |       |       +- FunctionWrapper
 |   |           |       |       |   `- '('
 |   |           |       |       +- NfaRegexp
 |   |           |       |       |   +- Sequence(...)
 |   |           |       |       |   `- alphabet <Unicode>
 |   |           |       |       +- Transform
 |   |           |       |       |   +- <loop>
 |   |           |       |       |   `- TransformationWrapper(<apply>)
 |   |           |       |       +- NfaRegexp
 |   |           |       |       |   +- Sequence(...)
 |   |           |       |       |   `- alphabet <Unicode>
 |   |           |       |       `- FunctionWrapper
 |   |           |       |           `- ')'
 |   |           |       +- NfaRegexp
 |   |           |       |   +- Sequence(...)
 |   |           |       |   `- alphabet <Unicode>
 |   |           |       `- TrampolineWrapper
 |   |           |           +- start 0
 |   |           |           +- stop None
 |   |           |           +- rest TransformableTrampolineWrapper
 |   |           |           |   +- FunctionWrapper
 |   |           |           |   |   `- '*/'
 |   |           |           |   +- NfaRegexp
 |   |           |           |   |   +- Sequence(...)
 |   |           |           |   |   `- alphabet <Unicode>
 |   |           |           |   `- TransformableTrampolineWrapper
 |   |           |           |       +- NfaRegexp
 |   |           |           |       |   +- Sequence(...)
 |   |           |           |       |   `- alphabet <Unicode>
 |   |           |           |       `- TransformableTrampolineWrapper
 |   |           |           |           +- FunctionWrapper
 |   |           |           |           |   `- '('
 |   |           |           |           +- NfaRegexp
 |   |           |           |           |   +- Sequence(...)
 |   |           |           |           |   `- alphabet <Unicode>
 |   |           |           |           +- Transform
 |   |           |           |           |   +- <loop>
 |   |           |           |           |   `- TransformationWrapper(<apply>)
 |   |           |           |           +- NfaRegexp
 |   |           |           |           |   +- Sequence(...)
 |   |           |           |           |   `- alphabet <Unicode>
 |   |           |           |           `- FunctionWrapper
 |   |           |           |               `- ')'
 |   |           |           `- first TransformableTrampolineWrapper
 |   |           |               +- FunctionWrapper
 |   |           |               |   `- '*/'
 |   |           |               +- NfaRegexp
 |   |           |               |   +- Sequence(...)
 |   |           |               |   `- alphabet <Unicode>
 |   |           |               `- TransformableTrampolineWrapper
 |   |           |                   +- NfaRegexp
 |   |           |                   |   +- Sequence(...)
 |   |           |                   |   `- alphabet <Unicode>
 |   |           |                   `- TransformableTrampolineWrapper
 |   |           |                       +- FunctionWrapper
 |   |           |                       |   `- '('
 |   |           |                       +- NfaRegexp
 |   |           |                       |   +- Sequence(...)
 |   |           |                       |   `- alphabet <Unicode>
 |   |           |                       +- Transform
 |   |           |                       |   +- <loop>
 |   |           |                       |   `- TransformationWrapper(<apply>)
 |   |           |                       +- NfaRegexp
 |   |           |                       |   +- Sequence(...)
 |   |           |                       |   `- alphabet <Unicode>
 |   |           |                       `- FunctionWrapper
 |   |           |                           `- ')'
 |   |           `- first TransformableTrampolineWrapper
 |   |               +- FunctionWrapper
 |   |               |   `- '+-'
 |   |               +- NfaRegexp
 |   |               |   +- Sequence(...)
 |   |               |   `- alphabet <Unicode>
 |   |               `- TransformableTrampolineWrapper
 |   |                   +- TransformableTrampolineWrapper
 |   |                   |   +- NfaRegexp
 |   |                   |   |   +- Sequence(...)
 |   |                   |   |   `- alphabet <Unicode>
 |   |                   |   `- TransformableTrampolineWrapper
 |   |                   |       +- FunctionWrapper
 |   |                   |       |   `- '('
 |   |                   |       +- NfaRegexp
 |   |                   |       |   +- Sequence(...)
 |   |                   |       |   `- alphabet <Unicode>
 |   |                   |       +- Transform
 |   |                   |       |   +- <loop>
 |   |                   |       |   `- TransformationWrapper(<apply>)
 |   |                   |       +- NfaRegexp
 |   |                   |       |   +- Sequence(...)
 |   |                   |       |   `- alphabet <Unicode>
 |   |                   |       `- FunctionWrapper
 |   |                   |           `- ')'
 |   |                   +- NfaRegexp
 |   |                   |   +- Sequence(...)
 |   |                   |   `- alphabet <Unicode>
 |   |                   `- TrampolineWrapper
 |   |                       +- start 0
 |   |                       +- stop None
 |   |                       +- rest TransformableTrampolineWrapper
 |   |                       |   +- FunctionWrapper
 |   |                       |   |   `- '*/'
 |   |                       |   +- NfaRegexp
 |   |                       |   |   +- Sequence(...)
 |   |                       |   |   `- alphabet <Unicode>
 |   |                       |   `- TransformableTrampolineWrapper
 |   |                       |       +- NfaRegexp
 |   |                       |       |   +- Sequence(...)
 |   |                       |       |   `- alphabet <Unicode>
 |   |                       |       `- TransformableTrampolineWrapper
 |   |                       |           +- FunctionWrapper
 |   |                       |           |   `- '('
 |   |                       |           +- NfaRegexp
 |   |                       |           |   +- Sequence(...)
 |   |                       |           |   `- alphabet <Unicode>
 |   |                       |           +- Transform
 |   |                       |           |   +- <loop>
 |   |                       |           |   `- TransformationWrapper(<apply>)
 |   |                       |           +- NfaRegexp
 |   |                       |           |   +- Sequence(...)
 |   |                       |           |   `- alphabet <Unicode>
 |   |                       |           `- FunctionWrapper
 |   |                       |               `- ')'
 |   |                       `- first TransformableTrampolineWrapper
 |   |                           +- FunctionWrapper
 |   |                           |   `- '*/'
 |   |                           +- NfaRegexp
 |   |                           |   +- Sequence(...)
 |   |                           |   `- alphabet <Unicode>
 |   |                           `- TransformableTrampolineWrapper
 |   |                               +- NfaRegexp
 |   |                               |   +- Sequence(...)
 |   |                               |   `- alphabet <Unicode>
 |   |                               `- TransformableTrampolineWrapper
 |   |                                   +- FunctionWrapper
 |   |                                   |   `- '('
 |   |                                   +- NfaRegexp
 |   |                                   |   +- Sequence(...)
 |   |                                   |   `- alphabet <Unicode>
 |   |                                   +- Transform
 |   |                                   |   +- <loop>
 |   |                                   |   `- TransformationWrapper(<apply>)
 |   |                                   +- NfaRegexp
 |   |                                   |   +- Sequence(...)
 |   |                                   |   `- alphabet <Unicode>
 |   |                                   `- FunctionWrapper
 |   |                                       `- ')'
 |   `- TransformationWrapper(<apply>)
 `- True""")

class ColumnsTest(BaseTest):
    
    def test_columns(self):
        self.assert_direct('0123456789', 
                           Columns(((0,3), Any()[3,...]),
                                   ((0,4), Any()[4:,...]),
                                   ((5,8), Any()[3:,...])),
                           [['012', '0123', '567']])

    def test_table(self):
        #basicConfig(level=DEBUG)
        self.assert_direct(
'''0123456789
abcdefghij
''', 
                           Columns(((0,3), Any()[3:,...]),
                                   ((0,4), Any()[4:,...]),
                                   ((5,8), Any()[3:,...]))[2],
                           [['012', '0123', '567',
                             'abc', 'abcd', 'fgh']])


class ConsumerTest(BaseTest):
    
    def test_simple(self):
        parser = Consumer(Any()).get_parse()
        result = parser('a')
        assert ['a'] == result, result
        
    def test_fail(self):
        matcher = Consumer(Any('b'))
        matcher.config.no_full_first_match()
        parser = matcher.get_parse()
        result = parser('a')
        assert None == result, result
        
    def test_complex(self):
        '''
        This test requires evaluation of sub-matchers via trampolining; if
        it fails then there may be an issue with generator_matcher.
        '''
        parser = Consumer(Any() & Any('b')).get_parse()
        result = parser('ab')
        assert ['a', 'b'] == result, result


class PostMatchTest(BaseTest):
    
    def test_normal(self):
        matcher = PostMatch(Drop(Any()[:]) & Any(), r'[0-9]')
        matcher.config.no_full_first_match()
        results = list(matcher.parse_all('12a'))
        assert results == [['2'], ['1']], results

    def test_not(self):
        matcher = PostMatch(Drop(Any()[:]) & Any(), r'[0-9]', not_=True)
        matcher.config.no_full_first_match()
        results = list(matcher.parse_all('12a'))
        assert results == [['a']], results
