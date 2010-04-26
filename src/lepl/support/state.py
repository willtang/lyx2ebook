
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
Encapsulate global (per thread) state.

This is for state that can affect the current parse.  It's probably simplest to
explain an example of what it can be used for.  Memoization records results
for a particular state to avoid repeating matches needlessly.  The state used
to identify when "the same thing is happening" is based on:
- the matcher being called
- the stream passed to the matcher
- this state

So a good shorthand for deciding whether or not this state should be used is
to ask whether the state will affect whether or not memoisation will work
correctly.

For example, with offside parsing, the current indentation level should be
stored here, because a (matcher, stream) combination that has previously failed
may work correctly when it changes. 
'''

from threading import local

from lepl.support.lib import singleton


class State(local):
    '''
    A thread local map from key (typically calling class) to value.  The hash
    attribute is updated on each mutation and cached for rapid access. 
    '''
    
    def __init__(self):
        '''
        Do not call directly - use the singleton.
        '''
        super(State, self).__init__()
        self.__map = {}
        self.hash = self.__hash()
        
    @classmethod
    def singleton(cls):
        '''
        Get a singleton instance.
        '''
        return singleton(cls)
    
    def __hash(self):
        '''
        Calculate the hash for the current dict.
        '''
        value = 0
        for key in self.__map:
            value ^= hash(key) ^ hash(self.__map[key])
        return value
        
    def __getitem__(self, key):
        return self.__map[key]
    
    def get(self, key, default=None):
        '''
        As for dict (lookup with default).
        '''
        return self.__map.get(key, default)
    
    def __setitem__(self, key, value):
        self.__map[key] = value
        self.hash = self.__hash()
    
    def __delitem__(self, key):
        del self.__map[key]
        self.hash = self.__hash()
       
    def __hash__(self):
        return self.hash
