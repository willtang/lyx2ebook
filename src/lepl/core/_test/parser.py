
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
Tests for the lepl.core.parser module.
'''

from traceback import format_exc
from types import MethodType
from unittest import TestCase

from lepl import Literal, Any, function_matcher


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, C0102, E1101
# (dude this is just a test)

    
class InstanceMethodTest(TestCase):
    
    class Foo(object):
        class_attribute = 1
        def __init__(self):
            self.instance_attribute = 2
        def bar(self):
            return (self.class_attribute,
                    self.instance_attribute,
                    hasattr(self, 'baz'))

    def test_method(self):
        foo = self.Foo()
        assert foo.bar() == (1, 2, False)
        def my_baz(myself):
            return (myself.class_attribute,
                    myself.instance_attribute,
                    hasattr(myself, 'baz'))
        # pylint: disable-msg=W0201
        foo.baz = MethodType(my_baz, foo)
        assert foo.baz() == (1, 2, True)
        assert foo.bar() == (1, 2, True)


    
class FlattenTest(TestCase):
    def test_flatten(self):
        matcher = Literal('a') & Literal('b') & Literal('c')
        assert str(matcher) == "And(And, Literal)", str(matcher)
        matcher.config.clear().flatten()
        parser = matcher.get_parse_string()
        assert str(parser.matcher) == "And(Literal, Literal, Literal)", str(parser.matcher)


class RepeatTest(TestCase):
    
    def test_depth(self):
        matcher = Any()[:,...]
        matcher.config.full_first_match(False)
        matcher = matcher.get_match_string()
        #print(repr(matcher.matcher))
        results = [m for (m, _s) in matcher('abc')]
        assert results == [['abc'], ['ab'], ['a'], []], results

    def test_breadth(self):
        matcher = Any()[::'b',...]
        matcher.config.full_first_match(False)
        matcher = matcher.get_match_string()
        results = [m for (m, _s) in matcher('abc')]
        assert results == [[], ['a'], ['ab'], ['abc']], results


class ErrorTest(TestCase):
    
    def test_error(self):
        class TestException(Exception): pass
        @function_matcher
        def Error(supprt, stream):
            raise TestException('here')
        matcher = Error()
        try:
            matcher.parse('a')
        except TestException:
            trace = format_exc()
            assert "TestException('here')" in trace, trace
            