
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103,W0621,R0904
#@PydevCodeAnalysisIgnore
# (the code style is for documentation, not "real")

'''
Examples from the documentation.
'''

from logging import basicConfig, DEBUG

from lepl import *
from lepl._example.support import Example


class PhoneExample(Example):
    
    def test_fragment1(self):
        
        matcher = Word()
        matcher.config.no_full_first_match()
        self.examples([
(lambda: next(matcher.match('hello world')),
"""(['hello'], 'hello world'[5:])"""),
(lambda: next( And(Word(), Space(), Integer()).match('hello 123') ),
"""(['hello', ' ', '123'], ''[0:])"""),
(lambda: next( (Word() & Space() & Integer()).match('hello 123') ),
"""(['hello', ' ', '123'], ''[0:])"""),
(lambda: next( (Word() / Integer()).match('hello 123') ),
"""(['hello', ' ', '123'], ''[0:])"""),
])
    
    def test_fragment2(self):
        
        name    = Word()              > 'name'
        phone   = Integer()           > 'phone'
        matcher = name / ',' / phone
        matcher.config.no_full_first_match()
        parser = matcher.get_parse_string()
        self.examples([(lambda: parser('andrew, 3333253'),
                        "[('name', 'andrew'), ',', ' ', ('phone', '3333253')]")])
    
    def test_fragment3(self):
        
        name    = Word()              > 'name'
        matcher = name                > make_dict
        matcher.config.no_full_first_match()
        parser = matcher.get_parse_string()
        self.examples([(lambda: parser('andrew, 3333253'),
                        "[{'name': 'andrew,'}]")])
    
    def test_fragment4(self):
        
        #basicConfig(level=DEBUG)
        
        name    = Word()              > 'name'
        matcher = name / ','          > make_dict
        matcher.config.clear().flatten()
        parser = matcher.get_parse_string()
        #print(repr(parser.matcher))
        matcher.config.clear().flatten().compose_transforms().trace(True)
        parser = matcher.get_parse_string()
        #print(repr(parser.matcher))
        self.examples([(lambda: parser('andrew, 3333253'),
                        "[{'name': 'andrew'}]")])
    
    def test_basic_parser(self):
        
        #basicConfig(level=DEBUG)

        name    = Word()              > 'name'
        phone   = Integer()           > 'phone'
        matcher = name / ',' / phone  > make_dict
        
#        matcher.config.clear()
#        print()
#        print(repr(matcher.get_parse_string().matcher))
#        matcher.config.clear().flatten()
#        print(repr(matcher.get_parse_string().matcher))
#        matcher.config.clear().flatten().compose_transforms()
#        print(repr(matcher.get_parse_string().matcher))
        parser = matcher.get_parse()

        self.examples([(lambda: parser('andrew, 3333253'),
                        "[{'phone': '3333253', 'name': 'andrew'}]"),
                       (lambda: matcher.parse('andrew, 3333253')[0],
                        "{'phone': '3333253', 'name': 'andrew'}"),
(lambda: next( (name / ',' / phone).match('andrew, 3333253') ),
"""([('name', 'andrew'), ',', ' ', ('phone', '3333253')], ''[0:])"""),
])


    def test_components(self):
        
        self.examples([(lambda: next( (Word() > 'name').match('andrew') ),
                        "([('name', 'andrew')], ''[0:])"),
                       (lambda: next( (Integer() > 'phone').match('3333253') ),
                        "([('phone', '3333253')], ''[0:])"),
                       (lambda: dict([('name', 'andrew'), ('phone', '3333253')]),
                        "{'phone': '3333253', 'name': 'andrew'}")])


    def test_repetition(self):
        
        spaces  = Space()[0:]
        name    = Word()              > 'name'
        phone   = Integer()           > 'phone'
        line    = name / ',' / phone  > make_dict
        newline = spaces & Newline() & spaces
        matcher = line[0:,~newline]
        
        self.examples([(lambda: matcher.parse('andrew, 3333253\n bob, 12345'),
                        "[{'phone': '3333253', 'name': 'andrew'}, {'phone': '12345', 'name': 'bob'}]")])
        
        
    def test_combine(self):
        
        def combine(results):
            all = {}
            for result in results:
                all[result['name']] = result['phone']
            return all
        
        spaces  = Space()[0:]
        name    = Word()              > 'name'
        phone   = Integer()           > 'phone'
        line    = name / ',' / phone  > make_dict
        newline = spaces & Newline() & spaces
        matcher = line[0:,~newline]   > combine
        
        self.examples([(lambda: matcher.parse('andrew, 3333253\n bob, 12345'),
                        "[{'bob': '12345', 'andrew': '3333253'}]")])

    