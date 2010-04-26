
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
Tests for the lepl.matchers.memo module.
'''

#from logging import basicConfig, DEBUG
from time import time
from unittest import TestCase

from lepl import Delayed, Any, Optional, Node, Literals, Eos, Token, Or


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102, C0321
# (dude this is just a test)

    
class MemoTest(TestCase):
    
    def test_right(self):
        
        #basicConfig(level=DEBUG)
        
        seq    = Delayed()
        letter = Any()
        seq   += letter & Optional(seq)
        
        #print(seq)
        seq.config.clear().right_memoize().trace(True)
        p = seq.get_match_string()
        #print(p.matcher)
        
        results = list(p('ab'))
        assert len(results) == 2, len(results)
        assert results[0][0] == ['a', 'b'], results[0][0]
        assert results[1][0] == ['a'], results[1][0]
        
    
    def test_left1a(self):
        
        #basicConfig(level=DEBUG)
        
        seq    = Delayed()
        letter = Any()
        seq   += Optional(seq) & letter
        
        seq.config.clear().left_memoize().trace(True)
        p = seq.get_match()
        #print(p.matcher)
        results = list(p('ab'))
        assert len(results) == 2, len(results)
        assert results[0][0] == ['a', 'b'], results[0][0]
        assert results[1][0] == ['a'], results[1][0]
        
        
    def test_left1b(self):
        
        #basicConfig(level=DEBUG)
        
        seq    = Delayed()
        letter = Any()
        seq   += Optional(seq) & letter
        
        seq.config.clear().left_memoize().trace(True)
        p = seq.get_match_string()
        results = list(p('ab'))
        assert len(results) == 2, len(results)
        assert results[0][0] == ['a', 'b'], results[0][0]
        assert results[1][0] == ['a'], results[1][0]
        
    
    def test_left2(self):
        
        #basicConfig(level=DEBUG)
        
        seq    = Delayed()
        letter = Any()
        seq   += letter | (seq  & letter)
        
        seq.config.clear().left_memoize().trace(True)
        p = seq.get_match_string()
        results = list(p('abcdef'))
        assert len(results) == 6, len(results)
        assert results[0][0] == ['a'], results[0][0]
        assert results[1][0] == ['a', 'b'], results[1][0]
        
    
    def test_complex(self):
        
        #basicConfig(level=DEBUG)
        
        class VerbPhrase(Node): pass
        class DetPhrase(Node): pass
        class SimpleTp(Node): pass
        class TermPhrase(Node): pass
        class Sentence(Node): pass
        
        verb        = Literals('knows', 'respects', 'loves')         > 'verb'
        join        = Literals('and', 'or')                          > 'join'
        proper_noun = Literals('helen', 'john', 'pat')               > 'proper_noun'
        determiner  = Literals('every', 'some')                      > 'determiner'
        noun        = Literals('boy', 'girl', 'man', 'woman')        > 'noun'
        
        verbphrase  = Delayed()
        verbphrase += verb | (verbphrase // join // verbphrase)      > VerbPhrase
        det_phrase  = determiner // noun                             > DetPhrase
        simple_tp   = proper_noun | det_phrase                       > SimpleTp
        termphrase  = Delayed()
        termphrase += simple_tp | (termphrase // join // termphrase) > TermPhrase
        sentence    = termphrase // verbphrase // termphrase & Eos() > Sentence
    
        sentence.config.clear().left_memoize().trace()
        p = sentence.get_match_string()
        
        text = 'every boy or some girl and helen and john or pat knows ' \
               'and respects or loves every boy or some girl and pat or ' \
               'john and helen'
#        text = 'every boy loves helen'
        count = 0
        for _meaning in p(text):
            count += 1
            if count < 3:
                #print(_meaning[0][0])
                pass
        #print(count)
        assert count == 392, count
    
    
class RecursionTest(TestCase):
    
    def right(self):
        matcher = Delayed()
        matcher += Any() & Optional(matcher)
        return matcher
    
    def right_token(self, contents=False):
        matcher = Delayed()
        inner = Token(Any())
        if contents:
            inner = inner(Or('a', 'b'))
        matcher += inner & Optional(matcher)
        return matcher
    
    def left(self):
        matcher = Delayed()
        matcher += Optional(matcher) & Any()
        return matcher
    
    def left_token(self, contents=False):
        matcher = Delayed()
        inner = Token(Any())
        if contents:
            inner = inner(Or('a', 'b'))
        matcher += Optional(matcher) & inner
        return matcher
    
    def do_test(self, parser):
        result = parser('ab')
        assert result == ['a', 'b'], result
        result = parser('aa')
        assert result == ['a', 'a'], result
        result = parser('aaa')
        assert result == ['a', 'a', 'a'], result
        result = parser('aba')
        assert result == ['a', 'b', 'a'], result
        
    def test_right_string(self):
        matcher = self.right()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_right_null(self):
        matcher = self.right()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())

    def test_right_token_string(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_right_token_null(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())
        
    def test_right_token_string_content(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token(True)
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_right_token_null_content(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token(True)
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())
        
    def test_right_string_clear(self):
        matcher = self.right()
        matcher.config.clear().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_right_null_clear(self):
        matcher = self.right()
        matcher.config.clear().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())

    def test_right_token_string_clear(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token()
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_right_token_null_clear(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token()
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse())
        
    def test_right_token_string_clear_content(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token(True)
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_right_token_null_clear_content(self):
        #basicConfig(level=DEBUG)
        matcher = self.right_token(True)
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse())
        
    def test_left_string(self):
        matcher = self.left()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_left_null(self):
        matcher = self.left()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())

    def test_left_token_string(self):
        matcher = self.left_token()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_left_token_null(self):
        matcher = self.left_token()
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())

    def test_left_token_string_content(self):
        matcher = self.left_token(True)
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_left_token_null_content(self):
        matcher = self.left_token(True)
        matcher.config.no_full_first_match().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())

    def test_left_string_clear(self):
        matcher = self.left()
        matcher.config.clear().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_left_null_clear(self):
        matcher = self.left()
        matcher.config.clear().auto_memoize(full=True).trace(True)
        self.do_test(matcher.get_parse())

    def test_left_token_string_clear(self):
        matcher = self.left_token()
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_left_token_null_clear(self):
        matcher = self.left_token()
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse())

    def test_left_token_string_clear_content(self):
        matcher = self.left_token(True)
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse_string())
        
    def test_left_token_null_clear_content(self):
        matcher = self.left_token(True)
        matcher.config.clear().auto_memoize(full=True).lexer().trace(True)
        self.do_test(matcher.get_parse())


#class PerformanceTest(TestCase):
#    
#    def matcher(self):
#    
#        class VerbPhrase(Node): pass
#        class DetPhrase(Node): pass
#        class SimpleTp(Node): pass
#        class TermPhrase(Node): pass
#        class Sentence(Node): pass
#        
#        verb        = Literals('knows', 'respects', 'loves')         > 'verb'
#        join        = Literals('and', 'or')                          > 'join'
#        proper_noun = Literals('helen', 'john', 'pat')               > 'proper_noun'
#        determiner  = Literals('every', 'some')                      > 'determiner'
#        noun        = Literals('boy', 'girl', 'man', 'woman')        > 'noun'
#        
#        verbphrase  = Delayed()
#        verbphrase += verb | (verbphrase // join // verbphrase)      > VerbPhrase
#        det_phrase  = determiner // noun                             > DetPhrase
#        simple_tp   = proper_noun | det_phrase                       > SimpleTp
#        termphrase  = Delayed()
#        termphrase += simple_tp | (termphrase // join // termphrase) > TermPhrase
#        sentence    = termphrase // verbphrase // termphrase & Eos() > Sentence
#    
#        return sentence
#    
#    def time_once(self, factory):
#        matcher = factory().get_parse_all()
#        start = time()
#        assert len(list(matcher(
#            'every boy or some girl and helen and john or pat knows '
#            'and respects or loves every boy or some girl and pat or '
#            'john and helen'))) == 392
#        return time() - start
#    
#    def repeat(self, count, factory):
#        time = 0
#        for _i in range(count):
#            time += self.time_once(factory)
#        return time
#            
#    def best_of(self, n, count, factory):
#        times = []
#        for _i in range(n):
#            times.append(self.repeat(count, factory))
#        return min(times)
#    
#    def test_timing(self):
#        (n, count) = (3, 2)
#        matcher = self.matcher()
#        def default_factory():
#            matcher.config.clear()
#            return matcher
#        default = self.best_of(n, count, default_factory)
#        def memo_factory():
#            matcher.config.clear().auto_memoize(full=True)
#            return matcher
#        memo = self.best_of(n, count, memo_factory)
#        assert default > 10 * memo, (default, memo)
        