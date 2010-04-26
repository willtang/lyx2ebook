
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
Support for managing sets of intervals (not all used).  
An interval is an open range implemented as a tuple pair.  For example (2,5) 
is an interval that represents the integers 2,3,4 and 5.
'''

from bisect import bisect_left
from collections import deque


class Character(object):
    '''
    A set of possible values for a character, described as a collection of 
    intervals.  Each interval is [a, b] (ie a <= x <= b, where x is a character 
    code).  We use open bounds to avoid having to specify an "out of range"
    value, making it easier to work with a variety of alphabets.
    
    The intervals are stored in a list, ordered by a, joining overlapping 
    intervals as necessary.
    '''
    
    # pylint: disable-msg=C0103 
    # (use (a,b) variables consistently)
    
    def __init__(self, intervals, alphabet):
        self.alphabet = alphabet
        self.__intervals = deque()
        for interval in intervals:
            self.__append(interval)
        self.__intervals = list(self.__intervals)
        self.__str = alphabet.fmt_intervals(self.__intervals)
        self.__index = []
        self.state = None
        self.__build_index()
        
    def append(self, interval):
        '''
        Add an interval to the range.
        '''
        self.__append(interval)
        self.__build_index()
        
    def __build_index(self):
        '''
        Pre-construct the index used for bisection.
        '''
        self.__index = [interval[1] for interval in self.__intervals]
        
    def __append(self, interval):
        '''
        Add an interval to the existing intervals.
        
        This maintains self.__intervals in the normalized form described above.
        '''
        (a1, b1) = interval
        if b1 < a1:
            (a1, b1) = (b1, a1)
        intervals = deque()
        done = False
        while self.__intervals:
            # pylint: disable-msg=E1103
            # (pylint fails to infer type)
            (a0, b0) = self.__intervals.popleft()
            if a0 <= a1:
                if b0 < a1 and b0 != self.alphabet.before(a1):
                    # old interval starts and ends before new interval
                    # so keep old interval and continue
                    intervals.append((a0, b0))
                elif b1 <= b0:
                    # old interval starts before and ends after new interval
                    # so keep old interval, discard new interval and slurp
                    intervals.append((a0, b0))
                    done = True
                    break
                else:
                    # old interval starts before new, but partially overlaps
                    # so discard old interval, extend new interval and continue
                    # (since it may overlap more intervals...)
                    (a1, b1) = (a0, b1)
            else:
                if b1 < a0 and b1 != self.alphabet.before(a0):
                    # new interval starts and ends before old, so add both
                    # and slurp
                    intervals.append((a1, b1))
                    intervals.append((a0, b0))
                    done = True
                    break
                elif b0 <= b1:
                    # new interval starts before and ends after old interval
                    # so discard old and continue (since it may overlap...)
                    pass
                else:
                    # new interval starts before old, but partially overlaps,
                    # add extended interval and slurp rest
                    intervals.append((a1, b0))
                    done = True
                    break
        if not done:
            intervals.append((a1, b1))
        intervals.extend(self.__intervals) # slurp remaining
        self.__intervals = intervals
        
    def __str__(self):
        return self.__str
    
    def __repr__(self):
        return self.__str
    
    def len(self):
        '''
        The number of intervals in the range.
        '''
        return len(self.__intervals)
    
    def __getitem__(self, index):
        return self.__intervals[index]
    
    def __iter__(self):
        return iter(self.__intervals)
    
    def __contains__(self, c):
        '''
        Does the value lie within the intervals?
        '''
        if self.__index:
            index = bisect_left(self.__index, c)
            if index < len(self.__intervals):
                (a, b) = self.__intervals[index]
                return a <= c <= b
        return False
    
    def __hash__(self):
        return hash(self.__str)
    
    def __eq__(self, other):
        # pylint: disable-msg=W0212
        # (test for same class)
        return isinstance(other, Character) and self.__str == other.__str
        
    def build(self, graph, src, dest):
        '''
        Insert within an NFA graph (although at this level, it's not clear it's
        NFA).
        '''
        graph.connect(src, dest, self)
    

#class Fragments(object):
#    '''
#    Similar to Character, but each additional interval fragments the list
#    of intervals, instead of creating a new merged interval.  For example,
#    if (3,5) is added to (1,4) and (7,8) then the result will be the
#    intervals (1,2), (3,4), (5,5) and (7,8) - the interval (3,4) is the
#    overlap between (1,4) and (3,5).   
#    
#    Used internally to combine transitions.
#    '''
#    
#    # pylint: disable-msg=C0103 
#    # (use (a,b) variables consistently)
#    
#    def __init__(self, alphabet, characters=None):
#        self.alphabet = alphabet
#        self.__intervals = deque()
#        if characters:
#            for character in characters:
#                self.append(character)
#                
#    def append(self, character):
#        '''
#        Add a character to the intervals.
#        '''
#        assert type(character) is Character
#        for interval in character:
#            self.__append(interval)
#        
#    def __append(self, interval):
#        '''
#        Add an interval to the existing intervals.
#        '''
#        (a1, b1) = interval
#        if b1 < a1:
#            (a1, b1) = (b1, a1)
#        intervals = deque()
#        alphabet = self.alphabet
#        done = False
#        while self.__intervals:
#            (a0, b0) = self.__intervals.popleft()
#            if a0 <= a1:
#                if b0 < a1:
#                    # old interval starts and ends before new interval
#                    # so keep old interval and continue
#                    intervals.append((a0, b0))
#                elif b1 <= b0:
#                    # old interval starts before or with and ends after or with 
#                    # new interval
#                    # so we have one, two or three new intervals
#                    if a0 < a1:
#                         # first part of old
#                        intervals.append((a0, alphabet.before(a1)))
#                    # common to both
#                    intervals.append((a1, b1)) 
#                    if b1 < b0:
#                         # last part of old
#                        intervals.append((alphabet.after(b1), b0))
#                    done = True
#                    break
#                else:
#                    # old interval starts before new, but partially overlaps
#                    # so split old and continue
#                    # (since it may overlap more intervals...)
#                    if a0 < a1:
#                        # first part of old
#                        intervals.append((a0, alphabet.before(a1)))
#                    # common to both 
#                    intervals.append((a1, b0)) 
#                    a1 = alphabet.after(b0)
#            else:
#                if b1 < a0:
#                    # new interval starts and ends before old
#                    intervals.append((a1, b1))
#                    intervals.append((a0, b0))
#                    done = True
#                    break
#                elif b0 <= b1:
#                    # new interval starts before and ends after or with old 
#                    # interval
#                    # so split and continue if extends (since last part may 
#                    # overlap...)
#                    # first part of new
#                    intervals.append((a1, alphabet.before(a0))) 
#                    # overlap
#                    intervals.append((a0, b0)) 
#                    if b1 > b0:
#                        a1 = alphabet.after(b0)
#                    else:
#                        done = True
#                        break
#                else:
#                    # new interval starts before old, but partially overlaps,
#                    # split and slurp rest
#                    # first part of new
#                    intervals.append((a1, alphabet.before(a0))) 
#                    # overlap
#                    intervals.append((a0, b1)) 
#                    # last part of old
#                    intervals.append((alphabet.after(b1), b0)) 
#                    done = True
#                    break
#        if not done:
#            intervals.append((a1, b1))
#        intervals.extend(self.__intervals) # slurp remaining
#        self.__intervals = intervals
#        
#    def len(self):
#        '''
#        The number of intervals contained.
#        '''
#        return len(self.__intervals)
#    
#    def __getitem__(self, index):
#        return self.__intervals[index]
#    
#    def __iter__(self):
#        return iter(self.__intervals)
    
    
class IntervalMap(dict):
    '''
    Map from intervals to values.
    
    Note - this is for open intervals!  This means it will not work as
    expected for continuous variables (which will overlap when two intervals
    share a single boundary value).  In other words, you cannot store 
    (1,2) and (2,3) together because both contain 2.
    '''
    
    # pylint: disable-msg=C0103 
    # (use (a,b) variables consistently)
    
    def __init__(self):
        super(IntervalMap, self).__init__()
        self.__intervals = []
        # None is used as a flag to indicate that a new index is needed
        self.__index = None
        
    def index(self):
        '''
        Build the internal indices.  Called automatically when necessary.
        '''
        second = lambda x: x[1]
        self.__intervals = list(sorted(self.keys(), key=second))
        # pylint: disable-msg=W0141
        self.__index = list(map(second, self.__intervals))
    
    def __setitem__(self, interval, value):
        # these are rather inefficient, but perhaps useful during development
#        assert None == self[interval[0]], 'Overlap'
#        assert None == self[interval[1]], 'Overlap'
        self.__index = None
        super(IntervalMap, self).__setitem__(interval, value)
        
    def __getitem__(self, point):
        '''
        The argument here is a single value, not an interval.
        '''
        if self.__index is None:
            self.index()
        if self.__index:
            try:
                index = bisect_left(self.__index, point)
            except TypeError as e:
                from lepl.regexp.core import RegexpError
                raise RegexpError(
"""Input characters are inconsistent with the given alphabet.
This error is often triggered by using the default configuration with non-text input; disable with matcher.config.no_compile_to_regexp().
Alternatively, configure with a suitable alphabet.""")
            if index < len(self.__index):
                # keep interval for identity on retrieval, just in case
                (a, b) = interval = self.__intervals[index]
                if a <= point <= b:
                    return super(IntervalMap, self).__getitem__(interval)
        return None
    
    def __delitem__(self, interval):
        self.__index = None
        super(IntervalMap, self).__delitem__(interval)

    def __contains__(self, interval):
        (a, b) = interval
        return self[a] is not None or self[b] is not None
    

class TaggedFragments(object):
    '''
    Similar to Fragments, but associates a value with each initial interval;
    on retrieval returns a list of all values associated with fragment. 
    '''
    
    # pylint: disable-msg=C0103 
    # (use (a,b) variables consistently)
    
    def __init__(self, alphabet):
        self.alphabet = alphabet
        self.__intervals = deque()
                
    def append(self, character, value):
        '''
        Add a range and tag.
        '''
        assert type(character) is Character
        for interval in character:
            self.__append(interval, [value])
        
    def __append(self, interval, v1):
        '''
        Add an interval to the existing intervals.
        '''
        (a1, b1) = interval
        if b1 < a1:
            (a1, b1) = (b1, a1)
        intervals = deque()
        alphabet = self.alphabet
        done = False
        while self.__intervals:
            ((a0, b0), v0) = self.__intervals.popleft()
            if a0 <= a1:
                if b0 < a1:
                    # old interval starts and ends before new interval
                    # so keep old interval and continue
                    intervals.append(((a0, b0), v0))
                elif b1 <= b0:
                    # old interval starts before or with and ends after or with 
                    # new interval
                    # so we have one, two or three new intervals
                    if a0 < a1:
                        # first part of old
                        intervals.append(((a0, alphabet.before(a1)), v0))
                    # common to both
                    intervals.append(((a1, b1), v0+v1)) 
                    if b1 < b0:
                        # last part of old 
                        intervals.append(((alphabet.after(b1), b0), v0)) 
                    done = True
                    break
                else:
                    # old interval starts before new, but partially overlaps
                    # so split old and continue
                    # (since new may overlap more intervals...)
                    if a0 < a1:
                        # first part of old
                        intervals.append(((a0, alphabet.before(a1)), v0))
                    # common to both 
                    intervals.append(((a1, b0), v0+v1)) 
                    a1 = alphabet.after(b0)
            else:
                if b1 < a0:
                    # new interval starts and ends before old
                    intervals.append(((a1, b1), v1))
                    intervals.append(((a0, b0), v0))
                    done = True
                    break
                elif b0 <= b1:
                    # new interval starts before and ends after or with old 
                    # interval
                    # so split and continue if extends (since last part may 
                    # overlap...)
                    # first part of new
                    intervals.append(((a1, alphabet.before(a0)), v1))
                    # old 
                    intervals.append(((a0, b0), v0+v1)) 
                    if b1 > b0:
                        a1 = alphabet.after(b0)
                    else:
                        done = True
                        break
                else:
                    # new interval starts before old, but partially overlaps,
                    # split and slurp rest
                    # first part of new
                    intervals.append(((a1, alphabet.before(a0)), v1))
                    # overlap 
                    intervals.append(((a0, b1), v0+v1)) 
                    # last part of old
                    intervals.append(((alphabet.after(b1), b0), v0)) 
                    done = True
                    break
        if not done:
            intervals.append(((a1, b1), v1))
        intervals.extend(self.__intervals) # slurp remaining
        self.__intervals = intervals
        
    def len(self):
        '''
        The number of intervals contained.
        '''
        return len(self.__intervals)
    
    def __getitem__(self, index):
        return self.__intervals[index]
    
    def __iter__(self):
        return iter(self.__intervals)
    
    
