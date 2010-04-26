
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
Tests for the lepl.core.config module.
'''

#from logging import basicConfig, DEBUG
from sys import version
from unittest import TestCase

from lepl import *
from lepl._test.base import assert_str


class ParseTest(TestCase):
    
    def run_test(self, name, text, parse, match2, match3, error, 
                 config=lambda x: None, **kargs):
        matcher = Any()[:, ...]
        config(matcher)
        parser = getattr(matcher, 'parse' + name)
        result = str(parser(text, **kargs))
        assert_str(result, parse)
        matcher = Any()[2, ...]
        matcher.config.no_full_first_match()
        config(matcher)
        parser = getattr(matcher, 'match' + name)
        result = str(list(parser(text, **kargs)))
        assert_str(result, match2)
        matcher = Any()[3, ...]
        matcher.config.no_full_first_match()
        config(matcher)
        parser = getattr(matcher, 'match' + name)
        result = str(list(parser(text, **kargs)))
        assert_str(result, match3)
        matcher = Any()
        config(matcher)
        parser = getattr(matcher, 'parse' + name)
        try:
            parser(text)
        except FullFirstMatchException as e:
            assert_str(e, error)
            
    def test_string(self):
        self.run_test('_string', 'abc', 
                      "['abc']", 
                      "[(['ab'], 'abc'[2:])]", 
                      "[(['abc'], ''[0:])]", 
                      """The match failed at 'bc',
Line 1, character 1 of str: 'abc'.""")
        self.run_test('', 'abc', 
                      "['abc']", 
                      "[(['ab'], 'abc'[2:])]", 
                      "[(['abc'], ''[0:])]",
                      """The match failed at 'bc',
Line 1, character 1 of str: 'abc'.""")
        self.run_test('_null', 'abc', 
                      "['abc']", 
                      "[(['ab'], 'c')]", 
                      "[(['abc'], '')]",
                      """The match failed at 'bc'.""")

    def test_string_list(self):
        self.run_test('_items', ['a', 'b', 'c'], 
                      "['abc']", 
                      "[(['ab'], ['a', 'b', 'c'][2:])]", 
                      "[(['abc'], [][0:])]",
                      """The match failed at '['a', 'b', 'c'][1:]',
Index 1 of items: ['a', 'b', 'c'].""", 
config=lambda m: m.config.no_compile_to_regexp(), sub_list=False)
        self.run_test('_items', ['a', 'b', 'c'], 
                      "[['a', 'b', 'c']]", 
                      "[([['a', 'b']], ['a', 'b', 'c'][2:])]", 
                      "[([['a', 'b', 'c']], [][0:])]",
                      """The match failed at '['a', 'b', 'c'][1:]',
Index 1 of items: ['a', 'b', 'c'].""", 
config=lambda m: m.config.no_compile_to_regexp(), sub_list=True)
        
    def test_int_list(self):
        #basicConfig(level=DEBUG)
        try:
            # this fails for python2 because it relies on 
            # comparison between types failing
            self.run_test('_items', [1, 2, 3], [], [], [], """""")
        except RegexpError as e:
            assert 'no_compile_to_regexp' in str(e), str(e)
        self.run_test('_items', [1, 2, 3], 
                      "[[1, 2, 3]]", 
                      "[([[1, 2]], [1, 2, 3][2:])]", 
                      "[([[1, 2, 3]], [][0:])]",
                      """The match failed at '[1, 2, 3][1:]',
Index 1 of items: [1, 2, 3].""",
config=lambda m: m.config.no_compile_to_regexp(), sub_list=True)


class BugTest(TestCase):
    
    def test_bug(self):
        matcher = Any('a')
        matcher.config.clear()
        result = list(matcher.match_items(['b']))
        assert result == [], result
