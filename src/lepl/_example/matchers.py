
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103
# (the code style is for documentation, not "real")
#@PydevCodeAnalysisIgnore

'''
Examples from the documentation.
'''

from lepl import *
from lepl._example.support import Example


class MatcherExample(Example):
    
    # this needs to be completely redone so that the default full match
    # is taken into account
    
#    def test_most(self):
#        self.examples([
#            (lambda: Literal('hello').parse_string('hello world'),
#             "['hello']"),
#
#            (lambda: Any().parse_string('hello world'), 
#             "['h']"),
#            (lambda: Any('abcdefghijklm')[0:].parse_string('hello world'), 
#             "['h', 'e', 'l', 'l']"),
#
#            (lambda: And(Any('h'), Any()).parse_string('hello world'), 
#             "['h', 'e']"),
#            (lambda: And(Any('h'), Any('x')).parse_string('hello world'), 
#             "None"),
#            (lambda: (Any('h') & Any('e')).parse_string('hello world'), 
#             "['h', 'e']"),
#
#            (lambda: Or(Any('x'), Any('h'), Any('z')).parse_string('hello world'), 
#             "['h']"),
#            (lambda: Or(Any('h'), Any()[3]).parse_string('hello world'), 
#             "['h']"),
#
#            (lambda: Repeat(Any(), 3, 3).parse_string('12345'), 
#             "['1', '2', '3']"),
#
#            (lambda: Repeat(Any(), 3).parse_string('12345'), 
#             "['1', '2', '3', '4', '5']"),
#            (lambda: Repeat(Any(), 3).parse_string('12'),
#             "None"),
#
#            (lambda: next(Lookahead(Literal('hello')).match('hello world')), 
#             "([], 'hello world')"),
#            (lambda: Lookahead(Literal('hello')).parse('hello world'), 
#             "[]"),
#            (lambda: Lookahead('hello').parse_string('goodbye cruel world'), 
#             "None"),
#            (lambda: (~Lookahead('hello')).parse_string('hello world'), 
#             "None"),
#            (lambda: (~Lookahead('hello')).parse_string('goodbye cruel world'), 
#             "[]"),
#
#            (lambda: (Drop('hello') / 'world').parse_string('hello world'), 
#             "[' ', 'world']"),
#            (lambda: (~Literal('hello') / 'world').parse_string('hello world'), 
#             "[' ', 'world']"),
#            (lambda: (Lookahead('hello') / 'world').parse_string('hello world'), 
#             "None")])


    def test_multiple_or(self):
        matcher = Or(Any('h'), Any()[3])
        matcher.config.no_full_first_match()
        matcher = matcher.match_null('hello world')
        assert str(next(matcher)) == "(['h'], 'ello world')"
        assert str(next(matcher)) == "(['h', 'e', 'l'], 'lo world')"


    def test_repeat(self):
        matcher = Repeat(Any(), 3)
        matcher = matcher.match_null('12345')
        result = str(next(matcher))
        assert result == "(['1', '2', '3', '4', '5'], '')", result
        assert str(next(matcher)) == "(['1', '2', '3', '4'], '5')"
        assert str(next(matcher)) == "(['1', '2', '3'], '45')"
        
        matcher = Repeat(Any(), 3, None, 'b')
        matcher.config.no_full_first_match()
        matcher = matcher.match_null('12345')
        assert str(next(matcher)) == "(['1', '2', '3'], '45')"
        assert str(next(matcher)) == "(['1', '2', '3', '4'], '5')"
        assert str(next(matcher)) == "(['1', '2', '3', '4', '5'], '')"



    def test_show(self):
        
        def show(results):
            #print('results:', results)
            return results

        self.examples([
            (lambda: Apply(Any()[:,...], show).parse_string('hello world'), 
             "[['hello world']]"),
            (lambda: (Any()[:,...] > show).parse_string('hello world'), 
             "[['hello world']]"),
            (lambda: Apply(Any()[:,...], show, raw=True).parse_string('hello world'),
             "['hello world']"),
            (lambda: (Any()[:,...] >= show).parse_string('hello world'),
             "['hello world']")])


    def test_apply_raw(self):
        
        def format3(a, b, c):
            return 'a: {0}; b: {1}; c: {2}'.format(a, b, c)
        
        self.examples([
            (lambda: Apply(Any()[3], format3, args=True).parse('xyz'),
              "['a: x; b: y; c: z']"),
            (lambda: (Any()[3] > args(format3)).parse('xyz'),
              "['a: x; b: y; c: z']")])
        