
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
Tests for the lepl.regexp.rewriters module.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import Any, NfaRegexp, Literal, Add, And, Integer, Float, Word, Star
from lepl.regexp.rewriters import CompileRegexp


# pylint: disable-msg=C0103, C0111, C0301, C0324
# (dude this is just a test)


class RewriteTest(TestCase):
    
    def test_any(self):
        #basicConfig(level=DEBUG)
        char = Any()
        char.config.clear().compile_to_nfa(force=True)
        matcher = char.get_match_null()
        results = list(matcher('abc'))
        assert results == [(['a'], 'bc')], results
        assert isinstance(matcher.matcher, NfaRegexp)
        
    def test_or(self):
        #basicConfig(level=DEBUG)
        rx = Any('a') | Any('b') 
        rx.config.clear().compile_to_nfa(force=True)
        matcher = rx.get_match_null()
        results = list(matcher('bq'))
        assert results == [(['b'], 'q')], results
        results = list(matcher('aq'))
        assert results == [(['a'], 'q')], results
        assert isinstance(matcher.matcher, NfaRegexp)
        
    def test_plus(self):
        rx = Any('a') + Any('b') 
        rx.config.clear().compile_to_nfa(force=True)
        matcher = rx.get_match_null()
        results = list(matcher('abq'))
        assert results == [(['ab'], 'q')], results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        
    def test_add(self):
        rx = Add(And(Any('a'), Any('b'))) 
        rx.config.clear().compile_to_nfa(force=True)
        matcher = rx.get_match_null()
        results = list(matcher('abq'))
        assert results == [(['ab'], 'q')], results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        
    def test_literal(self):
        rx = Literal('abc')
        rx.config.clear().compile_to_nfa(force=True)
        matcher = rx.get_match_null()
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        results = list(matcher('abcd'))
        assert results == [(['abc'], 'd')], results
        
        rx = Literal('abc') >> (lambda x: x+'e')
        rx.config.clear().compose_transforms().compile_to_nfa(force=True)
        matcher = rx.get_match_null()
        results = list(matcher('abcd'))
        assert results == [(['abce'], 'd')], results
        #print(repr(matcher.matcher))
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        
    def test_dfs(self):
        expected = [(['abcd'], ''), (['abc'], 'd'), (['ab'], 'cd'), 
                    (['a'], 'bcd'), ([], 'abcd')]
        rx = Any()[:, ...]
        # do un-rewritten to check whether [] or [''] is correct
        rx.config.clear()
        matcher = rx.get_match_null()
        results = list(matcher('abcd'))
        assert results == expected, results
        
        rx.config.compile_to_nfa()
        matcher = rx.get_match_null()
        results = list(matcher('abcd'))
        assert results == expected, results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
    
    def test_complex(self):
        #basicConfig(level=DEBUG)
        rx = Literal('foo') | (Literal('ba') + Any('a')[1:,...])
        rx.config.compile_to_nfa().no_full_first_match()
        matcher = rx.get_match_null()
        results = list(matcher('foo'))
        assert results == [(['foo'], '')], results
        results = list(matcher('baaaaax'))
        assert results == [(['baaaaa'], 'x'), (['baaaa'], 'ax'), 
                           (['baaa'], 'aax'), (['baa'], 'aaax')], results
        results = list(matcher('ba'))
        assert results == [], results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher

    def test_integer(self):
        rx = Integer()
        rx.config.compile_to_nfa().no_full_first_match()
        matcher = rx.get_match_null()
        results = list(matcher('12x'))
        assert results == [(['12'], 'x'), (['1'], '2x')], results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        
    def test_float(self):
        rx = Float()
        rx.config.compile_to_nfa().no_full_first_match()
        matcher = rx.get_match_null()
        results = list(matcher('1.2x'))
        assert results == [(['1.2'], 'x'), (['1.'], '2x'), (['1'], '.2x')], results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        
    def test_star(self):
        rx = Add(Star('a')) 
        rx.config.compile_to_nfa().no_full_first_match()
        matcher = rx.get_match_null()
        results = list(matcher('aa'))
        assert results == [(['aa'], ''), (['a'], 'a'), ([], 'aa')], results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        
    def test_word(self):
        #basicConfig(level=DEBUG)
        rx = Word('a')
        rx.config.compile_to_nfa().no_full_first_match()
        matcher = rx.get_match_null()
        results = list(matcher('aa'))
        assert results == [(['aa'], ''), (['a'], 'a')], results
        assert isinstance(matcher.matcher, NfaRegexp), matcher.matcher
        

class CompileTest(TestCase):
    '''
    Test the rewrite routine directly.
    '''
    
    def assert_regexp(self, matcher, regexp):
        compiler = CompileRegexp(use=True)
        matcher = compiler(matcher)
        assert isinstance(matcher, NfaRegexp), matcher.tree()
        assert str(matcher.regexp) == regexp, matcher.regexp
    
    def test_any(self):
        self.assert_regexp(Any(), '.')
        self.assert_regexp(Any('abc'), '[a-c]')
    
    def test_literal(self):
        self.assert_regexp(Literal('foo'), 'foo')

    def test_repeat(self):
        self.assert_regexp(Any()[1:, ...], '.(.)*')
        # ugly, but correct
        self.assert_regexp(Any()[:, ...], '(.(.)*|)')
        self.assert_regexp(Literal('foo')[:, ...], '(foo(foo)*|)')

    def test_and(self):
        self.assert_regexp(Any('ab')[:, ...] + Any('p'), '([a-b]([a-b])*|)p')
        
    def test_or(self):
        self.assert_regexp(Any('ab')[:, ...] | Any('p'), '(([a-b]([a-b])*|)|p)')

    def test_complex(self):
        self.assert_regexp((Any('ab') + Literal('q')) | Literal('z'), '([a-b]q|z)')
        self.assert_regexp((Any('ab') + 'q') | 'z', '([a-b]q|z)')
        