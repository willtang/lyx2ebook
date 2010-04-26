
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
Tests for the lepl.core.rewriters module.
'''

#from logging import basicConfig, DEBUG
from re import sub
from unittest import TestCase

from lepl import Any, Or, Delayed, Optional, Node, Drop, And, Join, Digit
from lepl.support.graph import preorder
from lepl.matchers.matcher import Matcher, is_child
from lepl.matchers.support import TransformableWrapper
from lepl.core.rewriters import DelayedClone


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0321
# (dude this is just a test)

    
def str26(value):
    '''
    Hack 2.6 string conversion
    '''
    string = str(value)
    return string.replace("u'", "'")


class DelayedCloneTest(TestCase):
    
    def assert_clone(self, matcher):
        copy = matcher.postorder(DelayedClone(), Matcher)
    
    def _assert_clone(self, matcher, copy):
        original = preorder(matcher, Matcher)
        duplicate = preorder(copy, Matcher)
        try:
            while True:
                o = next(original)
                d = next(duplicate)
                assert type(o) == type(d), (str(o), str(d), o, d)
                if isinstance(o, Matcher):
                    assert o is not d, (str(o), str(d), o, d)
                else:
                    assert o is d, (str(o), str(d), o, d)
        except StopIteration:
            self.assert_empty(original, 'original')
            self.assert_empty(duplicate, 'duplicate')
    
    def assert_relative(self, matcher):
        copy = matcher.postorder(DelayedClone(), Matcher)
        def pairs(matcher):
            for a in preorder(matcher, Matcher):
                for b in preorder(matcher, Matcher):
                    yield (a, b)
        for ((a,b), (c,d)) in zip(pairs(matcher), pairs(copy)):
            if a is b:
                assert c is d
            else:
                assert c is not d
            if type(a) is type(b):
                assert type(c) is type(d)
            else:
                assert type(c) is not type(d)
            
    def assert_empty(self, generator, name):
        try:
            next(generator)
            assert False, name + ' not empty'
        except StopIteration:
            pass
            
    def test_no_delayed(self):
        matcher = Any('a') | Any('b')[1:2,...]
        self.assert_clone(matcher)
        self.assert_relative(matcher)
        
    def test_simple_loop(self):
        delayed = Delayed()
        matcher = Any('a') | Any('b')[1:2,...] | delayed
        self.assert_clone(matcher)
        self.assert_relative(matcher)
       
    def test_complex_loop(self):
        delayed1 = Delayed()
        delayed2 = Delayed()
        line1 = Any('a') | Any('b')[1:2,...] | delayed1
        line2 = delayed1 & delayed2
        matcher = line1 | line2 | delayed1 | delayed2 > 'foo'
        self.assert_clone(matcher)
        self.assert_relative(matcher)

    def test_common_child(self):
        a = Any('a')
        b = a | Any('b')
        c = a | b | Any('c')
        matcher = a | b | c
        self.assert_clone(matcher)
        self.assert_relative(matcher)
        
    def test_full_config_loop(self):
        matcher = Delayed()
        matcher += Any() & matcher
        matcher.config.no_full_first_match()
        copy = matcher.get_parse_string().matcher
        self._assert_clone(matcher, copy)
                
    def test_transformed_etc(self):
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

        self.assert_clone(expression)
        self.assert_relative(expression)
        expression.config.no_full_first_match().no_compile_to_regexp()
        expression.config.no_compose_transforms().no_direct_eval()
        expression.config.no_flatten()
        copy = expression.get_parse_string().matcher
        self._assert_clone(expression, copy)
                

def append(x):
    return lambda l: l[0] + x

class ComposeTransformsTest(TestCase):
    
    def test_null(self):
        matcher = Any() > append('x')
        matcher.config.clear()
        parser = matcher.get_parse()
        result = parser('a')[0]
        assert result == 'ax', result
        
    def test_simple(self):
        matcher = Any() > append('x')
        matcher.config.clear().compose_transforms()
        parser = matcher.get_parse()
        result = parser('a')[0]
        assert result == 'ax', result
        
    def test_double(self):
        matcher = (Any() > append('x')) > append('y')
        matcher.config.clear().compose_transforms()
        parser = matcher.get_parse()
        result = parser('a')[0]
        assert result == 'axy', result
        # TODO - better test
        assert isinstance(parser.matcher, TransformableWrapper)
    
    def test_and(self):
        matcher = (Any() & Optional(Any())) > append('x')
        matcher.config.clear().compose_transforms()
        parser = matcher.get_parse()
        result = parser('a')[0]
        assert result == 'ax', result
        assert is_child(parser.matcher, And), type(parser.matcher)
    
    def test_loop(self):
        matcher = Delayed()
        matcher += (Any() | matcher) > append('x')
        matcher.config.clear().compose_transforms()
        parser = matcher.get_parse()
        result = parser('a')[0]
        assert result == 'ax', result
        assert isinstance(parser.matcher, Delayed)
        
    def test_node(self):
        
        class Term(Node): pass

        number      = Any('1')                             > 'number'
        term        = number                               > Term
        factor      = term | Drop(Optional(term))
        
        factor.config.clear().compose_transforms()
        p = factor.get_parse_string()
        ast = p('1')[0]
        assert type(ast) == Term, type(ast)
        assert ast[0] == '1', ast[0]
        assert str26(ast) == """Term
 `- number '1'""", ast
        

class OptimizeOrTest(TestCase):
    
    def test_conservative(self):
        matcher = Delayed()
        matcher += matcher | Any()
        assert isinstance(matcher.matcher.matchers[0], Delayed)
        matcher.config.clear().optimize_or(True)
        matcher.get_parse_string()
        # TODO - better test
        assert isinstance(matcher.matcher.matchers[0], 
                          TransformableWrapper)
        
    def test_liberal(self):
        matcher = Delayed()
        matcher += matcher | Any()
        assert isinstance(matcher.matcher.matchers[0], Delayed)
        matcher.config.clear().optimize_or(False)
        matcher.get_parse_string()
        # TODO - better test
        assert isinstance(matcher.matcher.matchers[0], 
                          TransformableWrapper)


class AndNoTrampolineTest(TestCase):
    
    def test_replace(self):
        #basicConfig(level=DEBUG)
        matcher = And('a', 'b')
        matcher.config.clear().direct_eval()
        parser = matcher.get_parse()
        text = str(parser.matcher)
        assert "AndNoTrampoline(Literal, Literal)" == text, text
        result = parser('ab')
        assert result == ['a', 'b'], result
         

class FlattenTest(TestCase):
    
    def test_flatten_and(self):
        matcher = And('a', And('b', 'c'))
        matcher.config.clear().flatten()
        parser = matcher.get_parse()
        text = str(parser.matcher)
        assert text == "And(Literal, Literal, Literal)", text
        result = parser('abcd')
        assert result == ['a', 'b', 'c'], result
        
    def test_no_flatten_and(self):
        matcher = And('a', Join(And('b', 'c')))
        matcher.config.clear().flatten()
        parser = matcher.get_parse()
        text = str(parser.matcher)
        assert text == "And(Literal, Transform)", text
        result = parser('abcd')
        assert result == ['a', 'bc'], result
        
    def test_flatten_and_transform(self):
        matcher = Join(And('a', And('b', 'c')))
        matcher.config.clear().flatten()
        parser = matcher.get_parse()
        text = sub('<.*>', '<>', str(parser.matcher))
        assert text == "Transform(And, TransformationWrapper(<>))", text
        result = parser('abcd')
        assert result == ['abc'], result
        
    def test_flatten_or(self):
        matcher = Or('a', Or('b', 'c'))
        matcher.config.clear().flatten()
        parser = matcher.get_parse()
        text = str(parser.matcher)
        assert text == "Or(Literal, Literal, Literal)", text
        result = parser('abcd')
        assert result == ['a'], result
        
    def test_no_flatten_or(self):
        matcher = Or('a', Join(Or('b', 'c')))
        matcher.config.clear().flatten()
        parser = matcher.get_parse()
        text = str(parser.matcher)
        assert text == "Or(Literal, Transform)", text
        result = parser('abcd')
        assert result == ['a'], result
        
