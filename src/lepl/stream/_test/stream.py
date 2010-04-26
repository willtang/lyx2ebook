
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
Tests for the lepl.stream.stream module.
'''

from random import choice
from unittest import TestCase

from lepl.stream.stream import SimpleStream, DEFAULT_STREAM_FACTORY


# pylint: disable-msg=C0103, C0111, C0301, W0702, C0324, R0904, R0201
# (dude this is just a test)

    
def repr26(value):
    '''
    Convert to string with crude hack for 2.6 Unicode
    '''
    string = repr(value)
    return string.replace("u'", "'")


class StreamTest(TestCase):
    
    def test_single_line(self):
        s1 = DEFAULT_STREAM_FACTORY.from_string('abc')
        assert s1[0] == 'a', s1[0]
        assert s1[0:3] == 'abc', s1[0:3]
        assert s1[2] == 'c' , s1[2]
        s2 = s1[1:]
        assert s2[0] == 'b', s2[0]

    def test_multiple_lines(self):
        s1 = DEFAULT_STREAM_FACTORY.from_string('abc\npqr\nxyz')
        assert s1[0:3] == 'abc', repr(s1[0:3])
        assert s1[0:4] == 'abc\n', s1[0:4]
        assert s1[0:5] == 'abc\np', s1[0:5]
        assert s1[0:11] == 'abc\npqr\nxyz'
        assert s1[5] == 'q', s1[5]
        s2 = s1[5:]
        assert s2[0] == 'q', s2[0]
        assert repr26(s2) == "'pqr\\n'[1:]", repr26(s2)
        s3 = s2[3:]
        assert repr26(s3) == "'xyz'[0:]", repr26(s3)
        
    def test_eof(self):
        s1 = DEFAULT_STREAM_FACTORY.from_string('abc\npqs')
        assert s1[6] == 's', s1[6]
        try:
            # pylint: disable-msg=W0104
            s1[7]
            assert False, 'expected error'
        except IndexError:
            pass
        
    def test_string(self):
        s1 = DEFAULT_STREAM_FACTORY.from_string('12')
        assert '1' == s1[0:1]
        assert '12' == s1[0:2]
        s2 = s1[1:]
        assert '2' == s2[0:1]
        
    def test_read(self):
        s1 = DEFAULT_STREAM_FACTORY.from_string('12\n123\n')
        assert '12\n' == s1.text


class SimpleStreamTester(object):
    '''
    Support for testing simple streams.
    '''
    
    def __init__(self, values, make_stream, make_ref=list):
        '''
        values is a list of values, from which we pick a random selection.
        
        make_stream is then given the randomized list and constructs a stream,
        while male_ref constructs a built-in sequence (usually a list) that
        should be equivalent.
        '''
        self.__values = values
        self.__make_stream = make_stream
        self.__make_ref = make_ref
        
    def build(self, n):
        x = [choice(self.__values) for _i in range(n)]
        s = self.__make_stream(x)
        l = self.__make_ref(x)
        assert isinstance(s, SimpleStream)
        return (l, s)
    
    def test_single_index(self, n=3):
        (l, s) = self.build(n)
        for i in range(len(l)):
            assert l[i] == s[i], '%r %r' % (l[i], s[i])
    
    def test_range(self, n=10, with_len=True):
        (l, s) = self.build(n)
        for i in range(len(l)):
            for j in range(i, len(l)):
                (lr, sr) = (l[i:j], s[i:j])
                if with_len: 
                    assert len(lr) == len(sr), '%r %d %r %d  %d %d' % (lr, len(lr), sr, len(sr), i, j)
                for k in range(j-i):
                    assert lr[k] == sr[k], str(i) + ':' + str(j) + ': ' + repr(lr) + '/' + repr(sr)
                if with_len: 
                    for k in range(len(lr)):
                        assert lr[k] == sr[k]
        try:
            s[len(l)]
            assert False, 'expected index error: %r %d' % (s, len(l))
        except IndexError:
            pass
            
                    
    def test_offset(self, n=10, with_len=True):
        (l, s) = self.build(n)
        for i in range(len(l)):
            (lo, so) = (l[i:], s[i:])
            while lo:
                if with_len:
                    assert len(lo) == len(so), '%d/%d' % (len(lo), len(so))
                assert lo[0] == so[0]
                (lo, so) = (lo[1:], so[1:])
            assert not so
            

class RawStringTest(TestCase):
    
    def test_type(self):
        assert issubclass(str, SimpleStream)
        assert isinstance('abc', SimpleStream)
    
    def get_tester(self):
        return SimpleStreamTester(['a', 'b', 'c'], ''.join)
    
    def test_single_index(self):
        self.get_tester().test_single_index()
        
    def test_range(self):
        self.get_tester().test_range(with_len=False)
        self.get_tester().test_range(with_len=True)
        
    def test_offset(self):
        self.get_tester().test_offset(with_len=False)
        self.get_tester().test_offset(with_len=True)
        
        
class RawListTest(TestCase):
    
    def test_type(self):
        assert issubclass(list, SimpleStream)
        assert isinstance([1,2,3], SimpleStream)
    
    def get_tester(self):
        return SimpleStreamTester([1,2,3], list)
    
    def test_single_index(self):
        self.get_tester().test_single_index()
        
    def test_range(self):
        self.get_tester().test_range(with_len=False)
        self.get_tester().test_range(with_len=True)
        
    def test_offset(self):
        self.get_tester().test_offset(with_len=False)
        self.get_tester().test_offset(with_len=True)
        
        
class FromListTest(TestCase):
    
    def get_tester(self):
        return SimpleStreamTester([1, "two", [3]], 
            lambda l: DEFAULT_STREAM_FACTORY.from_items(l, sub_list=False))
    
    def test_single_index(self):
        self.get_tester().test_single_index()
        
    def test_range(self):
        self.get_tester().test_range(with_len=False)
        self.get_tester().test_range(with_len=True)
        
    def test_offset(self):
        self.get_tester().test_offset(with_len=False)
        self.get_tester().test_offset(with_len=True)
        

class FromStringTest(TestCase):
    
    def get_tester(self):
        return SimpleStreamTester(list('a\nbc\ndef\n'), 
                    lambda l: DEFAULT_STREAM_FACTORY.from_string(''.join(l)))
    
    def test_single_index(self):
        self.get_tester().test_single_index()
        
    def test_range(self):
        self.get_tester().test_range(with_len=False)
        self.get_tester().test_range(with_len=True)
        
    def test_offset(self):
        self.get_tester().test_offset(with_len=False)
        self.get_tester().test_offset(with_len=True)
        

class FromLinesTest(TestCase):
    
    def get_tester(self):
        return SimpleStreamTester(['a\n', 'bc\n', 'def\n'], 
                    lambda l: DEFAULT_STREAM_FACTORY.from_lines(iter(l)),
                    ''.join)
    
    def test_single_index(self):
        self.get_tester().test_single_index()
        
    def test_range(self):
        self.get_tester().test_range(with_len=False)
        self.get_tester().test_range(with_len=True)
        
    def test_offset(self):
        self.get_tester().test_offset(with_len=False)
        self.get_tester().test_offset(with_len=True)
