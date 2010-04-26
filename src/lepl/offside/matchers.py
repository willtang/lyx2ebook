
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
Matchers that are indent aware.
'''

from weakref import WeakKeyDictionary

from lepl.matchers.core import Any
from lepl.matchers.combine import And
from lepl.matchers.support import coerce_, OperatorMatcher
from lepl.core.parser import tagged
from lepl.offside.lexer import Indent, Eol, BIndent
from lepl.offside.monitor import BlockMonitor
from lepl.offside.regexp import SOL as _SOL, EOL as _EOL
from lepl.stream.filters import ExcludeSequence
from lepl.support.lib import format
from lepl.lexer.matchers import Token


# pylint: disable-msg=W0105
# pylint convention

SOL = lambda: ~Any([_SOL])
'''
Allow explicit matching of start of line marker.
'''

EOL = lambda: ~Any([_EOL])
'''
Allow explicit matching of end of line marker.
'''


def constant_indent(n_spaces):
    '''
    Construct a simple policy for `Block` that increments the indent
    by some fixed number of spaces.
    '''
    def policy(current, _indent):
        '''
        Increment current by n_spaces
        '''
        return current + n_spaces
    return policy


def rightmost(_current, indent):
    '''
    Another simple policy that matches whatever indent is used.
    '''
    return len(indent[0])


# pylint: disable-msg=W0105
# epydoc convention
DEFAULT_TABSIZE = 8
'''
The default number of spaces for a tab.
'''

DEFAULT_POLICY = constant_indent(DEFAULT_TABSIZE)
'''
By default, expect an indent equivalent to a tab.
'''

# pylint: disable-msg=E1101, W0212, R0901, R0904
# pylint conventions
class Block(OperatorMatcher):
    '''
    Set a new indent level for the enclosed matchers (typically `BLine` and
    `Block` instances).
    
    In the simplest case, this might increment the global indent by 4, say.
    In a more complex case it might look at the current token, expecting an
    `Indent`, and set the global indent at that amount if it is larger
    than the current value.
    
    A block will always match an `Indent`, but will not consume it
    (it will remain in the stream after the block has finished).
    
    The usual memoization of left recursive calls will not detect problems
    with nested blocks (because the indentation changes), so instead we
    track and block nested calls manually.
    '''
    
    POLICY = 'policy'
    INDENT = 'indent'
    # class-wide default
    __indent = Indent()
    
# Python 2.6 does not support this syntax
#    def __init__(self, *lines, policy=None, indent=None):
    def __init__(self, *lines, **kargs):
        '''
        Lines are invoked in sequence (like `And()`).
        
        The policy is passed the current level and the indent and must 
        return a new level.  Typically it is set globally by rewriting with
        a default in the configuration.  If it is given as an integer then
        `constant_indent` is used to create a policy from that.
        
        indent is the matcher used to match indents, and is exposed for 
        rewriting/extension (in other words, ignore it).
        '''
        super(Block, self).__init__()
        self._args(lines=lines)
        policy = kargs.get(self.POLICY, DEFAULT_POLICY)
        if isinstance(policy, int):
            policy = constant_indent(policy)
        self._karg(policy=policy)
        indent = kargs.get(self.INDENT, self.__indent)
        self._karg(indent=indent)
        self.monitor_class = BlockMonitor
        self.__monitor = None
        self.__streams = set()
        
    def on_push(self, monitor):
        '''
        Store a reference to the monitor which we will update when _match
        is invoked (ie immediately).
        '''
        self.__monitor = monitor
        
    def on_pop(self, monitor):
        '''
        Remove the indent we added.
        '''
        # only if we pushed a value to monitor (see below)
        if not self.__monitor:
            monitor.pop_level()
        
    @tagged
    def _match(self, stream_in):
        '''
        Pull indent and call the policy and update the global value, 
        then evaluate the contents.
        '''
        # detect a nested call
        (_line_no, _line_off, char_off, _desc, _text) = stream_in.location
        if char_off in self.__streams:
            self._debug('Avoided left recursive call to Block.')
            return
        self.__streams.add(char_off)
        try:
            (indent, _stream) = yield self.indent._match(stream_in)
            current = self.__monitor.indent
            self.__monitor.push_level(self.policy(current, indent))
            # this flags we have pushed and need to pop
            self.__monitor = None
            
            generator = And(*self.lines)._match(stream_in)
            while True:
                yield (yield generator)
        finally:
            self.__streams.remove(char_off)


# pylint: disable-msg=C0103
# consistent interface
def Line(matcher):
    '''
    Match the matcher within a line.
    '''
    return ~Indent(compiled=True) & matcher & ~Eol(compiled=True)


def BLine(matcher):
    '''
    Match the matcher within a line with block indent.
    '''
    return ~BIndent(compiled=True) & matcher & ~Eol(compiled=True)


def only_token(token, item):
    '''
    Check whether the item (from a location stream of tokens) contains only
    the token specified.
    '''
    (tokens, _contents) = item
    return len(tokens) == 1 and tokens[0] == token.id_


def any_token(token, item):
    '''
    Check whether the item (from a location stream of tokens) contains at least
    the token specified.
    '''
    (tokens, _contents) = item
    return token.id_ in tokens


def _ContinuedLineFactory(continuation, base):
    '''
    Return the base (line) matcher, modified so that it applies its contents 
    to a stream which continues past line breaks if the given token is present.
    '''
    continuation = coerce_(continuation, Token)
    
    def ContinuedLine(matcher):
        '''
        Like `base`, but continues over multiple lines if the continuation 
        token is found at the end of each line.
        '''
        multiple = ExcludeSequence(any_token, [continuation, Eol(), Indent()])
        return base(multiple(matcher))
    return ContinuedLine


def ContinuedLineFactory(continuation):
    '''
    Construct a matcher like `Line`, but which extends over multiple lines if
    the continuation token ends a line.
    '''
    return _ContinuedLineFactory(continuation, Line)
    

def ContinuedBLineFactory(continuation):
    '''
    Construct a matcher like `BLine`, but which extends over multiple lines if
    the continuation token ends a line.
    '''
    return _ContinuedLineFactory(continuation, BLine)
    

Extend = ExcludeSequence(only_token, 
                         [Eol(compiled=True), Indent(compiled=True)])
'''
Provide a stream to the embedded matcher with `Indent` and `Eol` tokens 
filtered out.  On matching, return the "outer" stream at the appropriate
position (ie just after the last matched token in the filtered stream).
'''
