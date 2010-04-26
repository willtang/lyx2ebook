
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
Matchers that call the regular expression engine.

These are used internally for rewriting; users typically use `Regexp` which
calls the standard Python regular expression library (and so is faster).
'''

from lepl.matchers.support import Transformable
from lepl.matchers.transform import raise_
from lepl.core.parser import tagged
from lepl.regexp.core import Compiler
from lepl.regexp.unicode import UnicodeAlphabet


# pylint: disable-msg=R0904, R0901, E1101
# lepl convention
class BaseRegexp(Transformable):
    '''
    Common code for all matchers.
    '''
    
    # pylint: disable-msg=E1101
    # (using _arg to set attributes)
    def __init__(self, regexp, alphabet=None):
        super(BaseRegexp, self).__init__()
        self._arg(regexp=regexp)
        self._karg(alphabet=alphabet)
        
    def compose(self, wrapper):
        '''
        Implement the Transformable interface.
        '''
        copy = type(self)(self.regexp, self.alphabet)
        copy.wrapper = self.wrapper.compose(wrapper)
        return copy
    
    def precompose(self, wrapper):
        '''
        Like compose, but does the given transformation first.
        '''
        copy = type(self)(self.regexp, self.alphabet)
        copy.wrapper = self.wrapper.precompose(wrapper)
        return copy
    

class NfaRegexp(BaseRegexp):
    '''
    A matcher for NFA-based regular expressions.  This will yield alternative
    matches.
    
    This doesn't suffer from the same limitations as `Regexp` (it can "see"
    all the input data, if necessary), but currently has quite basic syntax 
    and no grouping (the syntax may improve, but grouping will not be added - 
    use LEPL itself for complex problems).
    '''
    
    def __init__(self, regexp, alphabet=None):
        alphabet = UnicodeAlphabet.instance() if alphabet is None else alphabet
        super(NfaRegexp, self).__init__(regexp, alphabet)
        self.__cached_matcher = None
        
    def _compile(self):
        '''
        Compile the matcher.
        '''
        if self.__cached_matcher is None:
            self.__cached_matcher = \
                    Compiler.single(self.alphabet, self.regexp).nfa().match
        return self.__cached_matcher

    @tagged
    def _match(self, stream_in):
        '''
        Actually do the work of matching.
        '''
        function = self.wrapper.function
        matches = self._compile()(stream_in)
        for (_terminal, match, stream_out) in matches:
            yield function(stream_in, lambda: ([match], stream_out)) \
                if function else ([match], stream_out)
        while True:
            yield function(stream_in, lambda: raise_(StopIteration))

        

class DfaRegexp(BaseRegexp):
    '''
    A matcher for DFA-based regular expressions.  This yields a single greedy
    match.
    
    Typically used only in specialised situations (see `Regexp`).
    '''
    
    def __init__(self, regexp, alphabet=None):
        alphabet = UnicodeAlphabet.instance() if alphabet is None else alphabet
        super(DfaRegexp, self).__init__(regexp, alphabet)
        self.__cached_matcher = None

    def _compile(self):
        '''
        Compile the matcher.
        '''
        if self.__cached_matcher is None:
            self.__cached_matcher = \
                    Compiler.single(self.alphabet, self.regexp).dfa().match
        return self.__cached_matcher

    @tagged
    def _match(self, stream_in):
        '''
        Actually do the work of matching.
        '''
        function = self.wrapper.function
        match = self._compile()(stream_in)
        if match is not None:
            (_terminals, match, stream_out) = match
            yield function(stream_in, lambda: ([match], stream_out)) \
                if function else ([match], stream_out)
        while True:
            yield function(stream_in, lambda: raise_(StopIteration))

