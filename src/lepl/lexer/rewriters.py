
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
Rewrite a matcher graph to include lexing.
'''

from collections import deque

from lepl.core.rewriters import Rewriter
from lepl.lexer.matchers import BaseToken, Lexer, LexerError, NonToken
from lepl.matchers.matcher import Matcher, is_child
from lepl.regexp.unicode import UnicodeAlphabet
from lepl.support.lib import format


def find_tokens(matcher):
    '''
    Returns a set of Tokens.  Also asserts that children of tokens are
    not themselves Tokens. 
    
    Should we also check that a Token occurs somewhere on every path to a
    leaf node?
    '''
    (tokens, visited, non_tokens) = (set(), set(), set())
    stack = deque([matcher])
    while stack:
        matcher = stack.popleft()
        if matcher not in visited:
            if is_child(matcher, NonToken):
                non_tokens.add(matcher)
            if isinstance(matcher, BaseToken):
                tokens.add(matcher)
                if matcher.content:
                    assert_not_token(matcher.content, visited)
            else:
                for child in matcher:
                    if isinstance(child, Matcher):
                        stack.append(child)
            visited.add(matcher)
    if tokens and non_tokens:
        raise LexerError(
            format('The grammar contains a mix of Tokens and non-Token '
                   'matchers at the top level. If Tokens are used then '
                   'non-token matchers that consume input must only '
                   'appear "inside" Tokens.  The non-Token matchers '
                   'include: {0}.',
                   '; '.join(str(n) for n in non_tokens)))
    return tokens


def assert_not_token(node, visited):
    '''
    Assert that neither this nor any child node is a Token. 
    '''
    if isinstance(node, Matcher) and node not in visited:
        visited.add(node)
        if isinstance(node, BaseToken):
            raise LexerError(format('Nested token: {0}', node))
        else:
            for child in node:
                assert_not_token(child, visited)


class AddLexer(Rewriter):
    '''
    This is required when using Tokens.  It does the following:
    - Find all tokens in the matcher graph
    - Construct a lexer from the tokens
    - Connect the lexer to the matcher
    - Check that all children have a token parent 
      (and optionally add a default token)
    Although possibly not in that order. 
    
    alphabet is the alphabet for which the regular expressions are defined.
    
    discard is a regular expression that is used to match space (typically)
    if no token can be matched (and which is then discarded)
    
    source is the source used to generate the final stream (it is used for
    offside parsing).
    '''

    def __init__(self, alphabet=None, discard=None, source=None):
        if alphabet is None:
            alphabet = UnicodeAlphabet.instance()
        # use '' to have no discard at all
        if discard is None:
            discard = '[ \t\r\n]'
        super(AddLexer, self).__init__(Rewriter.LEXER,
            format('Lexer({0}, {1}, {2})', alphabet, discard, source))
        self.alphabet = alphabet
        self.discard = discard
        self.source = source
        
    def __call__(self, graph):
        tokens = find_tokens(graph)
        if tokens:
            return Lexer(graph, tokens, self.alphabet, self.discard, 
                         source=self.source)
        else:
            self._info('Lexer rewriter used, but no tokens found.')
            return graph
