
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
Tests for the lepl.stream.filters module.
'''

#from logging import basicConfig, DEBUG
from operator import eq
from unittest import TestCase

from lepl.stream.filters import Filter, FilteredSource, Exclude, \
    ExcludeSequence, FilterException
from lepl.matchers.core import Any, Literal
from lepl.stream.stream import  DEFAULT_STREAM_FACTORY


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, R0904, R0201
# (dude this is just a test)


class FilterTest(TestCase):
    
    def test_filter(self):
        def consonant(s):
            return s[0] not in 'aeiou'
        stream1 = DEFAULT_STREAM_FACTORY.from_string('abcdef\nghijklm\n')
        stream2 = FilteredSource.filtered_stream(consonant, stream1)
        assert stream2[0:2] == 'bc', stream2[0:2]
        assert stream2[0:].line_number == 1, stream2[0:].line_number
        assert stream2[0:].line_offset == 1, stream2[0:].line_offset
        assert stream2[0:12] == 'bcdf\nghjklm\n'
        assert stream2[5:].line_number == 2, stream2[5:].line_number
        assert stream2[5:].line_offset == 0, stream2[5:].line_offset
        assert len(stream2) == 12
        
        
class CachedFilterTest(TestCase):
    
    def test_cached_filter(self):
        def consonant(x):
            return x not in 'aeiou'
        stream1 = DEFAULT_STREAM_FACTORY.from_string('abcdef\nghijklm\n')
        filter_ = Filter(consonant, stream1)
        stream2 = filter_.stream
        assert stream2[0:2] == 'bc', stream2[0:2]
        assert stream2[0:].line_number == 1, stream2[0:].line_number
        assert stream2[0:].line_offset == 1, stream2[0:].line_offset
        assert stream2[0:12] == 'bcdf\nghjklm\n'
        assert filter_.locate(stream2[0:])[0] == 'a', \
                filter_.locate(stream2[0:])[0]
        assert filter_.locate(stream2[1:])[0] == 'c', \
                filter_.locate(stream2[1:])[0]
        assert stream2[5:].line_number == 2, stream2[5:].line_number
        assert stream2[5:].line_offset == 0, stream2[5:].line_offset
        assert len(stream2) == 12, len(stream2)
        

class ExcludeTest(TestCase):
    
    def test_exclude(self):
        #basicConfig(level=DEBUG)
        def vowel(x):
            return x in 'aeiou'
        def parser(matcher):
            matcher.config.no_full_first_match()
            return matcher.get_match_string()
        stream1 = 'abcdef\nghijklm\n'
        (match, _stream) = next(parser(Exclude(vowel)(Any()[:]))('abcdef\nghijklm\n'))
        assert match[0:2] == ['b', 'c'], match[0:2]
        (_result, stream) = next(parser(Exclude(vowel)(Any()[0]))(stream1))
        assert stream[0] == 'a', stream[0]
        (_result, stream) = next(parser(Exclude(vowel)(Any()))(stream1))
        assert stream[0] == 'c', stream[0]
        (_result, stream) = next(parser(Exclude(vowel)(Any()[5]))(stream1))
        assert stream.line_number == 2, stream.line_number == 2
        assert stream.line_offset == 0, stream.line_offset == 0
        assert len(match) == 12, len(match)

    def test_example(self):
        factory = Exclude(lambda x: x == 'a')
        matcher = factory(Literal('b')[:, ...]) + Literal('c')[:, ...]
        result = matcher.parse_string('abababccc')
        assert result == ['bbbccc'], result  


class ExcludeSequenceTest(TestCase):
    
    def test_exclude_sequence(self):
        #basicConfig(level=DEBUG)
        stream = 'ababcdababcabcdbcd'
        matcher = ExcludeSequence(eq, 'abc')
        try:
            matcher(Any()[:, ...]).parse_null(stream)
            assert False, 'expected error'
        except FilterException as error:
            assert str(error) == 'Can only filter LocationStream instances.'
        result = matcher(Any()[:, ...]).parse_string(stream)
        assert result == ['abdabdbcd'], result
