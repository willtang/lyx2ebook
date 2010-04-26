
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
Tests for the lepl.matchers.separators module.
'''

#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import And, Optional, Space, Separator, SmartSeparator1, \
    SmartSeparator2, Eos


#basicConfig(level=DEBUG)
PRINT = False


STREAMS_3 = ['a b c ',
           'a b c',
           ' b c',
           'b c',
           'ab c',
           'a c',
           'a  c',
           'c',
           ' c',
           '  c']

STREAMS_2 = ['a b ',
             'a b',
             'ab',
             ' b',
             'b',
             'a ',
             'a',
             '',
             ' ']


class AbcSeparatorTest(TestCase):
    
    def _assert(self, separator, expecteds, streams=STREAMS_3):
        self._assert_null(separator, expecteds, streams)
        self._assert_string(separator, expecteds, streams)        
    
    def _assert_null(self, separator, expecteds, streams=STREAMS_3):
        with separator:
            parser = And(Optional('a') & Optional('b') & 'c', Eos())
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def _assert_string(self, separator, expecteds, streams=STREAMS_3):
        with separator:
            parser = And(Optional('a') & Optional('b') & 'c', Eos())
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse_string(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def test_separator(self):
        if PRINT:
            print("\nSeparator(Space())")
        self._assert(Separator(Space()), 
                     [False, True, True, False, False, False, True, False, False, True])
        if PRINT:
            print("\nSeparator(Space()[:])")
        self._assert(Separator(Space()[:]), 
                     [False, True, True, True, True, True, True, True, True, True])
        
    def test_separator1(self):
        if PRINT:
            print("\nSmartSeparator1(Space())")
        self._assert(SmartSeparator1(Space()), 
                     [False, True, False, True, False, True, False, True, False, False])
        if PRINT:
            print("\nSmartSeparator1(Space()[:])")
        self._assert(SmartSeparator1(Space()[:]), 
                     [False, True, False, True, True, True, True, True, False, False])
        
    def test_separator2(self):
        if PRINT:
            print("\nSmartSeparator2(Space())")
        self._assert(SmartSeparator2(Space()), 
                     [False, True, False, True, False, True, False, True, False, False])
        if PRINT:
            print("\nSmartSeparator2(Space()[:])")
        self._assert(SmartSeparator2(Space()[:]), 
                     [False, True, False, True, True, True, True, True, False, False])
        
            
class AbSeparatorTest(TestCase):
    
    def _assert(self, separator, expecteds, streams=STREAMS_2):
        self._assert_null(separator, expecteds, streams)
        self._assert_string(separator, expecteds, streams)
        
    def _assert_null(self, separator, expecteds, streams=STREAMS_2):
        with separator:
            parser = And(Optional('a') & Optional('b'), Eos())
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def _assert_string(self, separator, expecteds, streams=STREAMS_2):
        with separator:
            parser = And(Optional('a') & Optional('b'), Eos())
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse_string(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def test_separator(self):
        if PRINT:
            print("\nSeparator(Space())")
        self._assert(Separator(Space()), 
                     [False, True, False, True, False, True, False, False, True])
        if PRINT:
            print("\nSeparator(Space()[:])")
        self._assert(Separator(Space()[:]), 
                     [False, True, True, True, True, True, True, True, True])
        
    def test_separator1(self):
        if PRINT:
            print("\nSmartSeparator1(Space())")
        self._assert(SmartSeparator1(Space()), 
                     [False, True, False, False, True, False, True, True, False])
        if PRINT:
            print("\nSmartSeparator1(Space()[:])")
        self._assert(SmartSeparator1(Space()[:]), 
                     [False, True, True, False, True, False, True, True, False])
        
    def test_separator2(self):
        if PRINT:
            print("\nSmartSeparator2(Space())")
        self._assert(SmartSeparator2(Space()), 
                     [False, True, False, False, True, False, True, True, False])
        if PRINT:
            print("\nSmartSeparator2(Space()[:])")
        self._assert(SmartSeparator2(Space()[:]), 
                     [False, True, True, False, True, False, True, True, False])
        
        
class AbcEosSeparatorTest(TestCase):
    
    def _assert(self, separator, expecteds, streams=STREAMS_3):
        self._assert_null(separator, expecteds, streams)
        self._assert_string(separator, expecteds, streams)

    def _assert_null(self, separator, expecteds, streams=STREAMS_3):
        with separator:
            parser = Optional('a') & Optional('b') & 'c' & Eos()
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def _assert_string(self, separator, expecteds, streams=STREAMS_3):
        with separator:
            parser = Optional('a') & Optional('b') & 'c' & Eos()
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse_string(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def test_separator(self):
        if PRINT:
            print("\nSeparator(Space())")
        self._assert(Separator(Space()), 
                     [True, False, False, False, False, False, False, False, False, False])
        if PRINT:
            print("\nSeparator(Space()[:])")
        self._assert(Separator(Space()[:]), 
                     [True, True, True, True, True, True, True, True, True, True])
        
    def test_separator1(self):
        if PRINT:
            print("\nSmartSeparator1(Space())")
        self._assert(SmartSeparator1(Space()), 
                     [False, True, False, True, False, True, False, True, False, False])
        if PRINT:
            print("\nSmartSeparator1(Space()[:])")
        self._assert(SmartSeparator1(Space()[:]), 
                     [False, True, False, True, True, True, True, True, False, False])
        
    def test_separator2(self):
        if PRINT:
            print("\nSmartSeparator2(Space())")
        self._assert(SmartSeparator2(Space()), 
                     [True, False, False, False, False, False, False, False, False, False])
        if PRINT:
            print("\nSmartSeparator2(Space()[:])")
        self._assert(SmartSeparator2(Space()[:]), 
                     [True, True, False, True, True, True, True, True, False, False])
        
            
class AbEosSeparatorTest(TestCase):
    
    def _assert(self, separator, expecteds, streams=STREAMS_2):
        self._assert_null(separator, expecteds, streams)
        self._assert_string(separator, expecteds, streams)
        
    def _assert_null(self, separator, expecteds, streams=STREAMS_2):
        with separator:
            parser = Optional('a') & Optional('b') & Eos()
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def _assert_string(self, separator, expecteds, streams=STREAMS_2):
        with separator:
            parser = Optional('a') & Optional('b') & Eos()
        ok = True
        parser.config.no_full_first_match()
        for (stream, expected) in zip(streams, expecteds):
            parsed = parser.parse(stream) is not None
            if PRINT:
                print('{0!r:9} : {1!r:5} {2!r:5}'
                      .format(stream, parsed, parsed == expected))
            ok = ok and (parsed == expected)
        assert ok
        
    def test_separator(self):
        if PRINT:
            print("\nSeparator(Space())")
        self._assert(Separator(Space()), 
                     [True, False, False, False, False, False, False, False, False])
        if PRINT:
            print("\nSeparator(Space()[:])")
        self._assert(Separator(Space()[:]), 
                     [True, True, True, True, True, True, True, True, True])
        
    def test_separator1(self):
        if PRINT:
            print("\nSmartSeparator1(Space())")
        self._assert(SmartSeparator1(Space()), 
                     [False, True, False, False, True, False, True, True, False])
        if PRINT:
            print("\nSmartSeparator1(Space()[:])")
        self._assert(SmartSeparator1(Space()[:]), 
                     [False, True, True, False, True, False, True, True, False])
        
    def test_separator2(self):
        if PRINT:
            print("\nSmartSeparator2(Space())")
        self._assert(SmartSeparator2(Space()), 
                     [True, False, False, False, False, True, False, True, False])
        if PRINT:
            print("\nSmartSeparator2(Space()[:])")
        self._assert(SmartSeparator2(Space()[:]), 
                     [True, True, True, False, True, True, True, True, False])
        
            
        
