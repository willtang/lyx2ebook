
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
Tests for the regexp extensions.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import UnicodeAlphabet
from lepl._test.base import assert_str
from lepl.offside.regexp import LineAwareAlphabet, make_hide_sol_eol_parser
from lepl.offside.stream import LineAwareStreamFactory
from lepl.regexp.core import Compiler
from lepl.regexp.str import make_str_parser
#from lepl.support.lib import format


# pylint: disable-msg=C0103, C0111, C0301
# (dude this is just a test)


class CompilerTest(TestCase):
    
    def test_explicit(self):
        #basicConfig(level=DEBUG)
        self.do_test('(*SOL)', 'a', 
                     (['label'], '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]"), 
                     [('label', '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]")],
                     make_str_parser)
        self.do_test('.', 'a', 
                     (['label'], '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]"), 
                     [('label', '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]")],
                     make_str_parser)
        self.do_test('[^a]', 'a', 
                     (['label'], '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]"), 
                     [('label', '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]")],
                     make_str_parser)
        
    def test_implicit(self):
        #basicConfig(level=DEBUG)
        self.do_test('(*SOL)', 'a', 
                     (['label'], '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]"), 
                     [('label', '', "[Marker('(*SOL)',False), 'a', Marker('(*EOL)',True)][1:]")],
                     make_hide_sol_eol_parser)
        self.do_test('.', 'a', 
                     None, 
                     [],
                     make_hide_sol_eol_parser)
        self.do_test('[^a]', 'a', 
                     None, 
                     [],
                     make_hide_sol_eol_parser)
        
        
    def do_test(self, pattern, target, dfa_result, nfa_result, parser_factory):
        alphabet = LineAwareAlphabet(UnicodeAlphabet.instance(), parser_factory)
        compiler = Compiler.single(alphabet, pattern)
        str(compiler.expression)
#        text = str(compiler.expression)
#        assert text == format('(?P<label>{0!s})', pattern), text
        
        factory = LineAwareStreamFactory(alphabet)
        target = factory.from_string(target)
        
        dfa = compiler.dfa()
        result = dfa.match(target)
        if result:
            (a, b, c) = result
            (p, q, r) = dfa_result
            assert a == p, result
            assert b == q, result
            assert_str(repr(c), r)
        else:
            assert dfa_result == None, dfa_result

        nfa = compiler.nfa()
        result = list(nfa.match(target))
        assert len(result) == len(nfa_result), result
        for ((a,b,c), (p,q,r)) in zip(result, nfa_result):
            assert a == p, result
            assert b == q, result
            assert_str(repr(c), r)
        
