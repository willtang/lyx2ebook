
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
Tests for the lepl.regexp.unicode module.
'''

from unittest import TestCase

#from logging import basicConfig, DEBUG
from lepl import RegexpError, DEFAULT_STREAM_FACTORY
from lepl.regexp.core import NfaGraph, NfaToDfa, Compiler
from lepl.regexp.unicode import UnicodeAlphabet
from lepl.support.lib import format

# pylint: disable-msg=C0103, C0111, C0301, R0201, R0904
# (dude this is just a test)


UNICODE = UnicodeAlphabet.instance()


def _test_parser(regexp):
    return Compiler.single(UNICODE, regexp, 'label')

def label(text):
    return format('(?P<label>{0!s})', text)
    
class CharactersTest(TestCase):
    
    def test_unicode_dot(self):
        #basicConfig(level=DEBUG)
        c = _test_parser('.')
        assert label('.') == str(c), str(c)
        c = _test_parser('.\\.')
        assert label('.\\.') == str(c), str(c)

    def test_brackets(self):
        #basicConfig(level=DEBUG)
        c = _test_parser('a')
        assert label('a') == str(c), str(c)
        c = _test_parser('[ac]')
        assert label('[ac]') == str(c), str(c)
        c = _test_parser('[a-c]')
        assert label('[a-c]') == str(c), str(c)
        c = _test_parser('[a-cp-q]')
        assert label('[a-cp-q]') == str(c), str(c)
        c = _test_parser(r'\\')
        assert label(r'\\') == str(c), str(c)
        c = _test_parser(r'\-')
        assert label(r'\-') == str(c), str(c)
        c = _test_parser(r'[\\-x]')
        assert label(r'[\\-x]') == str(c), str(c)
        c = _test_parser('[a-bq,]')
        assert label('[,a-bq]') == str(c), str(c)
        c = _test_parser('[a-b,q]')
        assert label('[,a-bq]') == str(c), str(c)
        c = _test_parser('[,a-bq]')
        assert label('[,a-bq]') == str(c), str(c)
        c = _test_parser('[^a]')
        assert r'(?P<label>[\x00-`b-\uffff])' == str(c), str(c)
   
    def test_merge(self):
        c = _test_parser('[a-ce-g]')
        assert label('[a-ce-g]') == str(c), str(c)
        c = _test_parser('[a-cd-f]')
        assert label('[a-f]') == str(c), str(c)
        c = _test_parser('[a-cc-e]')
        assert label('[a-e]') == str(c), str(c)
        c = _test_parser('[a-cb-d]')
        assert label('[a-d]') == str(c), str(c)
        c = _test_parser('[a-ca-c]')
        assert label('[a-c]') == str(c), str(c)
        c = _test_parser('[a-a]')
        assert label('a') == str(c), str(c)
        c = _test_parser('[e-ga-c]')
        assert label('[a-ce-g]') == str(c), str(c)
        c = _test_parser('[d-fa-c]')
        assert label('[a-f]') == str(c), str(c)
        c = _test_parser('[c-ea-c]')
        assert label('[a-e]') == str(c), str(c)
        c = _test_parser('[b-da-c]')
        assert label('[a-d]') == str(c), str(c)
        c = _test_parser('[a-gc-e]')
        assert label('[a-g]') == str(c), str(c)
        c = _test_parser('[c-ea-g]')
        assert label('[a-g]') == str(c), str(c)
        c = _test_parser('[a-eg]')
        assert label('[a-eg]') == str(c), str(c)
        c = _test_parser('[ga-e]')
        assert label('[a-eg]') == str(c), str(c)

    def test_star(self):
        c = _test_parser('a*')
        assert label('a*') == str(c), str(c)
        c = _test_parser('a(bc)*d')
        assert label('a(bc)*d') == str(c), str(c)
        c = _test_parser('a(bc)*d[e-g]*')
        assert label('a(bc)*d[e-g]*') == str(c), str(c)
        c = _test_parser('a[a-cx]*')
        assert label('a[a-cx]*') == str(c), str(c)
        
    def test_option(self):
        c = _test_parser('a?')
        assert label('a?') == str(c), str(c)
        c = _test_parser('a(bc)?d')
        assert label('a(bc)?d') == str(c), str(c)
        c = _test_parser('a(bc)?d[e-g]?')
        assert label('a(bc)?d[e-g]?') == str(c), str(c)
        c = _test_parser('ab?c')
        assert label('ab?c') == str(c), str(c)
        
    def test_choice(self):
        #basicConfig(level=DEBUG)
        c = _test_parser('(a*|b|[c-d])')
        assert label('(a*|b|[c-d])') == str(c), str(c)
        c = _test_parser('a(a|b)*')
        assert label('a(a|b)*') == str(c), str(c)
        c = _test_parser('a([a-c]x|axb)*')
        assert label('a([a-c]x|axb)*') == str(c), str(c)
        
    def test_bad_escape(self):
        #basicConfig(level=DEBUG)
        c = _test_parser(r'\+')
        assert label('\\+') == str(c), str(c)
        try:
            c = _test_parser('+')
            assert False, 'Expected error'
        except RegexpError:
            pass


class NfaTest(TestCase):
    
    def assert_matches(self, pattern, text, results):
        r = _test_parser(pattern)
        m = r.nfa().match
        s = list(m(DEFAULT_STREAM_FACTORY.from_string(text)))
        assert len(s) == len(results), s
        for (a, b) in zip(s, results):
            assert a[1] == b, a[1] + ' != ' + b
    
    def test_simple(self):
        #basicConfig(level=DEBUG)
        self.assert_matches('ab', 'abc', ['ab'])
    
    def test_star(self):
        self.assert_matches('a*b', 'aaabc', ['aaab'])
    
    def test_plus(self):
        self.assert_matches('[a-z]+', 'abc', ['abc', 'ab', 'a'])

    def test_choice(self):
        self.assert_matches('(a|b)', 'ac', ['a'])
    
    def test_star_choice(self):
        self.assert_matches('(a|b)*', 'aababbac', 
                            ['aababba', 'aababb', 'aabab', 'aaba', 'aab', 'aa', 'a', ''])
    
    def test_multiple_choice(self):
        #basicConfig(level=DEBUG)
        self.assert_matches('(a|ab)b', 'abb', ['ab', 'abb'])

    def test_range(self):
        self.assert_matches('[abc]*', 'bbcx', ['bbc', 'bb', 'b', ''])
        self.assert_matches('[A-Z][a-z]*', 'Abc', ['Abc', 'Ab', 'A'])
        
    def test_range_overlap(self):
        '''
        Matches with 'b' are duplicated, since it appears in both ranges.
        '''
        self.assert_matches('([ab]|[bc])*', 'abc', 
                            ['abc', 'ab', 'abc', 'ab', 'a', ''])

    def test_complex(self):
        #basicConfig(level=DEBUG)
        self.assert_matches('a([x-z]|a(g|b))*(u|v)p',
                            'ayagxabvp', ['ayagxabvp'])


class DfaGraphTest(TestCase):
    
    def assert_dfa_graph(self, regexp, desc):
        r = _test_parser(regexp)
        nfa = NfaGraph(UNICODE)
        r.expression.build(nfa, nfa.new_node(), nfa.new_node())
        dfa = NfaToDfa(nfa, UNICODE).dfa
        assert str(dfa) == desc, str(dfa)

    def test_dfa_no_empty(self):
        self.assert_dfa_graph('abc',
            '0: [0] a->1; 1: [3] b->2; 2: [4] c->3; 3(label): [1, 2]') 
        
    def test_dfa_simple_repeat(self):
        self.assert_dfa_graph('ab*c',
            '0: [0] a->1; 1: [3, 4, 5] c->2,b->3; 2(label): [1, 2]; 3: [4, 5] c->2,b->3')
        
    def test_dfa_simple_choice(self):
        self.assert_dfa_graph('a(b|c)', 
            '0: [0] a->1; 1: [3, 4] [b-c]->2; 2(label): [1, 2]')
        
    def test_dfa_repeated_choice(self):
        self.assert_dfa_graph('a(b|cd)*e', 
            '0: [0] a->1; 1: [3, 4, 5, 6] e->2,c->3,b->4; 2(label): [1, 2]; 3: [7] d->4; 4: [4, 5, 6] e->2,c->3,b->4')
        
    def test_dfa_overlapping_choice(self):
        self.assert_dfa_graph('a(bcd|bce)', 
            '0: [0] a->1; 1: [3, 6] b->2; 2: [4, 7] c->3; 3: [8, 5] [d-e]->4; 4(label): [1, 2]')

    def test_dfa_conflicting_choice(self):
        self.assert_dfa_graph('a(bc|b*d)', 
            '0: [0] a->1; 1: [3, 5, 6, 7] d->2,b->3; 2(label): [1, 2]; 3: [4, 6, 7] [c-d]->2,b->4; 4: [6, 7] d->2,b->4')
        
    def test_dfa_conflicting_choice_2(self):
        self.assert_dfa_graph('a(bb|b*c)', 
            '0: [0] a->1; 1: [3, 5, 6, 7] c->2,b->3; 2(label): [1, 2]; 3: [4, 6, 7] c->2,b->4; 4(label): [1, 2, 6, 7] c->2,b->5; 5: [6, 7] c->2,b->5')

    def test_dfa_dot_option(self):
        '''
        This one's nice - the 'a' completely disappears.
        '''
        #basicConfig(level=DEBUG)
        self.assert_dfa_graph('.*a?b', 
            r'0: [0, 3, 4, 5] [\x00-ac-\uffff]->1,b->2; 1: [3, 4, 5] [\x00-ac-\uffff]->1,b->2; 2(label): [1, 2, 3, 4, 5] [\x00-ac-\uffff]->1,b->2')

class DfaTest(TestCase):
    
    def assert_dfa(self, regexp, text, results):
        r = _test_parser(regexp).dfa().match(text)
        assert r[1] == results, r
        
    def test_simple(self):
        self.assert_dfa('abc', 'abcd', 'abc')
        
    def test_dot_option(self):
        self.assert_dfa('.*a?b', 'aaabc', 'aaab')
        
    def test_empty(self):
        self.assert_dfa('a*', 'bc', '')
        self.assert_dfa('a*', '', '')
        
    def test_conflicting_choice(self):
        self.assert_dfa('a(bc|b*d)', 'abde', 'abd') 
        self.assert_dfa('a(bc|b*d)', 'abce', 'abc') 
    
    def test_space_star(self):
        self.assert_dfa(' *', '  a', '  ')
