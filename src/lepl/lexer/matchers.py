
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
Generate and match a stream of tokens that are identified by regular 
expressions.
'''

# pylint currently cannot parse this file

from abc import ABCMeta

from lepl.support.context import Namespace, NamespaceMixin
from lepl.matchers.derived import Add, Apply, Drop, KApply, Repeat, Map
from lepl.lexer.stream import lexed_simple_stream, lexed_location_stream, \
    ContentSource, TokenSource
from lepl.matchers.error import raise_error
from lepl.lexer.support import LexerError, RuntimeLexerError
from lepl.matchers.core import OperatorMatcher, Any, Literal, Lookahead, Regexp
from lepl.matchers.combine import And, Or, First
from lepl.matchers.matcher import Matcher, add_children
from lepl.matchers.memo import NoMemo
from lepl.matchers.operators import ADD, AND, OR, APPLY, APPLY_RAW, \
    NOT, KARGS, RAISE, REPEAT, FIRST, MAP
from lepl.matchers.support import BaseMatcher, coerce_
from lepl.core.parser import tagged, GeneratorWrapper
from lepl.regexp.core import Compiler
from lepl.regexp.matchers import BaseRegexp
from lepl.regexp.rewriters import CompileRegexp
from lepl.regexp.unicode import UnicodeAlphabet
from lepl.stream.stream import LocationStream, DEFAULT_STREAM_FACTORY
from lepl.support.lib import format, str


# pylint: disable-msg=W0105
# epydoc convention
TOKENS = 'tokens'
'''
The namespace used for global per-thread data for matchers defined here. 
'''

# pylint: disable-msg=C0103
# it's a class
NonToken = ABCMeta('NonToken', (object, ), {})
'''
ABC used to identify matchers that actually consume from the stream.  These
are the "leaf" matchers that "do the real work" and they cannot be used at
the same level as Tokens, but must be embedded inside them.

This is a purely informative interface used, for example, to generate warnings 
for the user.  Not implementing this interface will not block any 
functionality.
'''

add_children(NonToken, Lookahead, Any, Literal, Regexp)
# don't register Empty() here because it's actually useful as a token(!)


class TokenNamespace(Namespace):
    '''
    A modified version of the usual ``OperatorNamespace`` without handling of
    spaces (since that is handled by the lexer), allowing Tokens and other
    matchers to be configured separately (because they process different 
    types).
    
    At one point this also defined alphabet and discard, used by the rewriter,
    but because those are global values it makes mosre sense to supply them
    directly to the rewriter.
    '''
    
    def __init__(self):
        super(TokenNamespace, self).__init__({
            ADD:       lambda a, b: Add(And(a, b)),
            AND:       And,
            OR:        Or,
            APPLY:     Apply,
            APPLY_RAW: lambda a, b: Apply(a, b, raw=True),
            NOT:       Drop,
            KARGS:     KApply,
            RAISE:     lambda a, b: KApply(a, raise_error(b)),
            REPEAT:    Repeat,
            FIRST:     First,
            MAP:       Map,
        })
        

# pylint: disable-msg=R0901, R0904, R0913, W0201, W0142, E1101
# lepl standards
class BaseToken(OperatorMatcher, NoMemo):
    '''
    Introduce a token that will be recognised by the lexer.  A Token instance
    can be specialised to match particular contents by calling as a function.
    
    This is a base class that provides all the functionality, but doesn't
    set the regexp attribute.  This allows subclasses to provide a fixed
    value, while `Token` uses the constructor.
    '''
    
    __count = 0
    
    def __init__(self, content=None, id_=None, alphabet=None,
                  complete=True, compiled=False):
        '''
        Define a token that will be generated by the lexer.
        
        content is the optional matcher that will be invoked on the value
        of the token.  It is usually set via (), which clones this instance
        so that the same token can be used more than once.
        
        id_ is an optional unique identifier that will be given an integer
        value if left empty.
        
        alphabet is the alphabet associated with the regexp.  It should be
        set by the lexer rewiter, so that all instances share the same
        value (it appears in the constructor so that Tokens can be cloned).
        
        complete indicates whether any sub-matcher must completely exhaust
        the contents when matching.  It can be over-ridden for a particular
        sub-matcher via __call__().
        
        compiled should only be used internally.  It is a flag indicating
        that the Token has been processed by the rewriter (see below).
        
        A Token must be "compiled" --- this completes the configuration
        using a given alphabet and is done by the lexer_rewriter.  Care is 
        taken to allow a Token to be cloned before or after compilation.
        '''
        super(BaseToken, self).__init__(name=TOKENS, namespace=TokenNamespace)
        self._karg(content=content)
        if id_ is None:
            id_ = 'Tk' + str(BaseToken.__count)
            BaseToken.__count += 1
        self._karg(id_=id_)
        self._karg(alphabet=alphabet)
        self._karg(complete=complete)
        self._karg(compiled=compiled)
        
    def compile(self, alphabet=None):
        '''
        Convert the regexp if necessary. 
        '''
        if alphabet is None:
            alphabet = UnicodeAlphabet.instance()
        # pylint: disable-msg=E0203
        # set in constructor via _kargs
        if self.alphabet is None:
            self.alphabet = alphabet
        self.regexp = self.__to_regexp(self.regexp, self.alphabet)
        self.compiled = True
    
    @staticmethod
    def  __to_regexp(regexp, alphabet):
        '''
        The regexp may be a matcher; if so we try to convert it to a regular
        expression and extract the equivalent text.
        '''
        if isinstance(regexp, Matcher):
            rewriter = CompileRegexp(alphabet)
            rewrite = rewriter(regexp)
            if isinstance(rewrite, BaseRegexp):
                regexp = str(rewrite.regexp)
            else:
                raise LexerError(
                    format('A Token was specified with a matcher, '
                           'but the matcher could not be converted to '
                           'a regular expression: {0}', rewrite))
        return regexp
        
    def __call__(self, content, complete=None):
        '''
        If complete is specified as True of False it overrides the value
        set in the constructor.  If True the content matcher must complete 
        match the Token contents.
        '''
        args, kargs = self._constructor_args()
        kargs['complete'] = self.complete if complete is None else complete
        kargs['content'] = coerce_(content)
        return type(self)(*args, **kargs)
    
    @tagged
    def _match(self, stream):
        '''
        On matching we first assert that the token type is correct and then
        delegate to the content.
        '''
        if not self.compiled:
            raise LexerError(
                format('A {0} token has not been compiled. '
                       'You must use the lexer rewriter with Tokens. '
                       'This can be done by using matcher.config.lexer().',
                       self.__class__.__name__))
        if stream:
            (tokens, contents) = stream[0]
            if self.id_ in tokens:
                if self.content is None:
                    # result contains all data
                    yield ([contents], stream[1:])
                else:
                    new_stream = self.__new_stream(contents, stream)
                    generator = self.content._match(new_stream)
                    while True:
                        (result, stream_out) = yield generator
                        if not stream_out or not self.complete:
                            yield (result, stream[1:])
        
    def __str__(self):
        return format('{0}: {1!r}', self.id_, self.regexp)
    
    def __repr__(self):
        return format('<Token({0!s})>', self)
    
    @staticmethod
    def __new_stream(contents, stream):
        '''
        Create a new stream to pass to the content matcher.
        '''
        if isinstance(stream.source, TokenSource):
            return DEFAULT_STREAM_FACTORY(ContentSource(contents, stream))
        else:
            # this branch when the original stream is not a location stream 
            return contents
    
    @classmethod
    def reset_ids(cls):
        '''
        Reset the ID counter.  This should not be needed in normal use.
        '''
        cls.__count = 0
        
        
class  Token(BaseToken):
    '''
    A token with a user-specified regexp.
    '''
    
    def __init__(self, regexp, content=None, id_=None, alphabet=None,
                  complete=True, compiled=False):
        '''
        Define a token that will be generated by the lexer.
        
        regexp is the regular expression that the lexer will use to generate
        appropriate tokens.
        
        content is the optional matcher that will be invoked on the value
        of the token.  It is usually set via (), which clones this instance
        so that the same token can be used more than once.
        
        id_ is an optional unique identifier that will be given an integer
        value if left empty.
        
        alphabet is the alphabet associated with the regexp.  It should be
        set by the lexer rewiter, so that all instances share the same
        value (it appears in the constructor so that Tokens can be cloned).
        
        complete indicates whether any sub-matcher must completely exhaust
        the contents when matching.  It can be over-ridden for a particular
        sub-matcher via __call__().
        
        compiled should only be used internally.  It is a flag indicating
        that the Token has been processed by the rewriter (see below).
        
        A Token must be "compiled" --- this completes the configuration
        using a given alphabet and is done by the lexer_rewriter.  Care is taken
        to allow a Token to be cloned before or after compilation.
        '''
        super(Token, self).__init__(content=content, id_=id_, alphabet=alphabet,
                                    complete=complete, compiled=compiled)
        self._karg(regexp=regexp)
        
        
class Lexer(NamespaceMixin, BaseMatcher):
    '''
    This takes a set of regular expressions and provides a matcher that
    converts a stream into a stream of tokens, passing the new stream to 
    the embedded matcher.
    
    It is added to the matcher graph by the lexer_rewriter; it is not
    specified explicitly by the user.
    '''
    
    def __init__(self, matcher, tokens, alphabet, discard, 
                  t_regexp=None, s_regexp=None, source=None):
        '''
        matcher is the head of the original matcher graph, which will be called
        with a tokenised stream. 
        
        tokens is the set of `Token` instances that define the lexer.
        
        alphabet is the alphabet for which the regexps are defined.
        
        discard is the regular expression for spaces (which are silently
        dropped if not token can be matcher).
        
        t_regexp and s_regexp are internally compiled state, use in cloning,
        and should not be provided by non-cloning callers.
        
        source is the source used to generate the final stream.
        '''
        super(Lexer, self).__init__(TOKENS, TokenNamespace)
        if t_regexp is None:
            unique = {}
            for token in tokens:
                token.compile(alphabet)
                self._debug(format('Token: {0}', token))
                # this just reduces the work for the regexp compiler
                unique[token.id_] = token
            t_regexp = Compiler.multiple(alphabet, 
                            [(t.id_, t.regexp) for t in unique.values()]).dfa()
        if s_regexp is None and discard is not None:
            s_regexp = Compiler.single(alphabet, discard).dfa()
        self._arg(matcher=matcher)
        self._arg(tokens=tokens)
        self._arg(alphabet=alphabet)
        self._arg(discard=discard)
        self._karg(t_regexp=t_regexp)
        self._karg(s_regexp=s_regexp)
        self._karg(source=source)
        
    def token_for_id(self, id_):
        '''
        A utility that checks the known tokens for a given ID.  The ID is used
        internally, but is (by default) an unfriendly integer value.  Note that 
        a lexed stream associates a chunk of input with a list of IDs - more 
        than one regexp may be a maximal match (and this is a feature, not a 
        bug).
        '''
        for token in self.tokens:
            if token.id_ == id_:
                return token
        
    @tagged
    def _match(self, stream):
        '''
        Implement matching - pass token stream to tokens.
        '''
        if isinstance(stream, LocationStream):
            tokens = lexed_location_stream(self.t_regexp, self.s_regexp,
                                           stream, self.source)
        else:
            # might assert simple stream here?
            if self.source:
                raise RuntimeLexerError('Source specified for simple stream')
            tokens = lexed_simple_stream(self.t_regexp, self.s_regexp, stream)
        # pylint: disable-msg=W0212
        # implementation, not public, method
        generator = self.matcher._match(tokens)
        while True:
            (result, stream_out) = yield generator
            yield (result, stream_out)

        