
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
The main configuration object and various standard configurations.
'''

from lepl.core.parser import make_raw_parser, make_single, make_multiple
from lepl.stream.stream import DEFAULT_STREAM_FACTORY

# A major driver for this being separate is that it decouples dependency loops


class ConfigurationError(Exception):
    pass



class Configuration(object):
    '''
    Encapsulate various parameters that describe how the matchers are
    rewritten and evaluated.
    '''
    
    def __init__(self, rewriters=None, monitors=None, stream_factory=None):
        '''
        `rewriters` are functions that take and return a matcher tree.  They
        can add memoisation, restructure the tree, etc.
        
        `monitors` are factories that return implementations of `ActiveMonitor`
        or `PassiveMonitor` and will be invoked by `trampoline()`. 
        
        `stream_factory` constructs a stream from the given input.
        '''
        if rewriters is None:
            rewriters = set()
        self.__rewriters = rewriters
        self.monitors = monitors
        if stream_factory is None:
            stream_factory = DEFAULT_STREAM_FACTORY
        self.stream_factory = stream_factory
        
    @property
    def rewriters(self):
        rewriters = list(self.__rewriters)
        rewriters.sort()
        #print([str(m) for m in rewriters])
        return rewriters
        

class ConfigBuilder(object):
    
    def __init__(self):
        # we need to delay startup, to avoid loops
        self.__started = False
        # this is set whenever any config is changed.  it is cleared when
        # the configuration is read.  so if is is false then the configuration
        # is the same as previously read
        self.__changed = True
        self.__rewriters = set()
        self.__monitors = []
        self.__stream_factory = DEFAULT_STREAM_FACTORY
        self.__alphabet = None
        
    def __start(self):
        '''
        Set default values on demand to avoid dependency loop.
        '''
        if not self.__started:
            self.__started = True
            self.default()
        
    # raw access to basic components
        
    def add_rewriter(self, rewriter):
        '''
        Add a rewriter that will be applied to the matcher graph when the
        parser is generated.
        '''
        self.__start()
        self.clear_cache()
        # we need to remove before adding to ensure last added is the one
        # used (exclusive rewriters are equal)
        if rewriter in self.__rewriters:
            self.__rewriters.remove(rewriter)
        self.__rewriters.add(rewriter)
        return self
    
    def remove_rewriter(self, rewriter):
        '''
        Remove a rewriter from the current configuration.
        '''
        self.__start()
        self.clear_cache()
        self.__rewriters = set(r for r in self.__rewriters 
                               if r is not rewriter)
        return self

    def remove_all_rewriters(self, type_=None):
        '''
        Remove all rewriters of a given type from the current configuration.
        '''
        self.__start()
        self.clear_cache()
        if type_:
            self.__rewriters = set(r for r in self.__rewriters 
                                   if not isinstance(r, type_))
        else:
            self.__rewriters = set()
        return self

    def add_monitor(self, monitor):
        '''
        Add a monitor to the current configuration.  Monitors are called
        from within the trampolining process and can be used to track 
        evaluation, control resource use, etc.
        '''
        self.__start()
        self.clear_cache()
        self.__monitors.append(monitor)
        return self
    
    def remove_all_monitors(self):
        '''
        Remove all monitors from the current configuration.
        '''
        self.__start()
        self.clear_cache()
        self.__monitors = []
        return self
    
    def stream_factory(self, stream_factory=DEFAULT_STREAM_FACTORY):
        '''
        Specify the stream factory.  This is used to generate the input stream
        for the parser.
        '''
        self.__start()
        self.clear_cache()
        self.__stream_factory = stream_factory
        return self

    @property
    def configuration(self):
        '''
        The current configuration.
        
        Adding or removing a rewriter means that the default configuration 
        will be cleared (if no rewriters are added, the default configuration 
        is used, but as soon as one rewriter is given explicitly the default 
        is discarded, and only the rewriters explicitly added are used).
        '''
        self.__start()
        self.__changed = False
        return Configuration(self.__rewriters, self.__monitors, 
                             self.__stream_factory)
    
    @configuration.setter
    def configuration(self, configuration):
        '''
        Allow the configuration to be specified from a `Configuration`
        instance.  No longer recommended - use the other methods here instead.
        '''
        self.__rewriters = list(configuration.raw_rewriters)
        self.__monitors = list(configuration.monitors)
        self.__stream_factory = configuration.stream_factory
        self.__started = True
        self.clear_cache()
    
    def __get_alphabet(self):
        '''
        Get the alphabet used.
        
        Typically this is Unicode, which is the default.  It is needed for
        the generation of regular expressions. 
        '''
        from lepl.regexp.unicode import UnicodeAlphabet
        if not self.__alphabet:
            self.__alphabet = UnicodeAlphabet.instance()
        return self.__alphabet
    
    def alphabet(self, alphabet):
        '''
        Set the alphabet used.  It is needed for the generation of regular 
        expressions, for example (but the default, for Unicode, is usually
        sufficient).
        '''
        if alphabet:
            if self.__alphabet:
                if self.__alphabet != alphabet:
                    raise ConfigurationError(
                        'Alphabet has changed during configuration '
                        '(perhaps the default was already used?)')
            else:
                self.__alphabet = alphabet
                self.__start()
                self.clear_cache()
                
    @property
    def changed(self):
        '''
        Has the config been changed by the user since it was last returned
        via `configuration`?  if not, any previously generated parser can be
        reused.
        '''
        return self.__changed
    
    def clear_cache(self):
        '''
        Force calculation of a new parser.
        '''
        self.__changed = True
    
    # rewriters
    
    def set_arguments(self, type_, **kargs):
        '''
        Set the given keyword arguments on all matchers of the given `type_`
        (ie class) in the grammar.
        '''
        from lepl.core.rewriters import SetArguments
        return self.add_rewriter(SetArguments(type_, **kargs))
    
    def no_set_arguments(self):
        '''
        Remove all rewriters that set arguments.
        '''
        from lepl.core.rewriters import SetArguments
        return self.remove_all_rewriters(SetArguments)
        
    def set_alphabet_arg(self, alphabet=None):
        '''
        Set `alphabet` on various matchers.  This is useful when using an 
        unusual alphabet (most often when using line-aware parsing), as
        it saves having to specify it on each matcher when creating the
        grammar.
        
        Although this option is often required for line aware parsing,
        you normally do not need to call this because it is called by 
        `default_line_aware` (and `line_aware`).
        '''
        from lepl.regexp.matchers import BaseRegexp
        from lepl.lexer.matchers import BaseToken
        if alphabet:
            self.alphabet(alphabet)
        else:
            alphabet = self.__get_alphabet()
        if not alphabet:
            raise ValueError('An alphabet must be provided or already set')
        self.set_arguments(BaseRegexp, alphabet=alphabet)
        self.set_arguments(BaseToken, alphabet=alphabet)
        return self

    def set_block_policy_arg(self, block_policy):
        '''
        Set the block policy on all `Block` instances.
        
        Although this option is required for "offside rule" parsing,
        you normally do not need to call this because it is called by 
        `default_line_aware` (and `line_aware`) if either `block_policy` 
        or `block_start` is specified.
        '''
        from lepl.offside.matchers import Block
        return self.set_arguments(Block, policy=block_policy)
    
    def full_first_match(self, eos=True):
        '''
        Raise an error if the first match fails.  If `eos` is True then this
        requires that the entire input is matched, otherwise it only requires
        that the matcher succeed.  The exception includes information about
        the deepest read to the stream (which is a good indication of where
        any error occurs).
        
        This is part of the default configuration.  It can be removed with
        `no_full_first_match()`.
        '''
        from lepl.core.rewriters import FullFirstMatch
        return self.add_rewriter(FullFirstMatch(eos))
        
    def no_full_first_match(self):
        '''
        Disable the automatic generation of an error if the first match fails.
        '''
        from lepl.core.rewriters import FullFirstMatch
        return self.remove_all_rewriters(FullFirstMatch)
    
    def flatten(self):
        '''
        Combined nested `And()` and `Or()` matchers.  This does not change
        the parser semantics, but improves efficiency.
        
        This is part of the default configuration.  It can be removed with
        `no_flatten`.
        '''
        from lepl.core.rewriters import Flatten
        return self.add_rewriter(Flatten())
    
    def no_flatten(self):
        '''
        Disable the combination of nested `And()` and `Or()` matchers.
        '''
        from lepl.core.rewriters import Flatten
        return self.remove_all_rewriters(Flatten)
        
    def compile_to_dfa(self, force=False, alphabet=None):
        '''
        Compile simple matchers to DFA regular expressions.  This improves
        efficiency but may change the parser semantics slightly (DFA regular
        expressions do not provide backtracking / alternative matches).
        '''
        from lepl.regexp.matchers import DfaRegexp
        from lepl.regexp.rewriters import CompileRegexp
        self.alphabet(alphabet)
        return self.add_rewriter(
                    CompileRegexp(self.__get_alphabet(), force, DfaRegexp))
    
    def compile_to_nfa(self, force=False, alphabet=None):
        '''
        Compile simple matchers to NFA regular expressions.  This improves
        efficiency and should not change the parser semantics.
        
        This is part of the default configuration.  It can be removed with
        `no_compile_regexp`.
        '''
        from lepl.regexp.matchers import NfaRegexp
        from lepl.regexp.rewriters import CompileRegexp
        self.alphabet(alphabet)
        return self.add_rewriter(
                    CompileRegexp(self.__get_alphabet(), force, NfaRegexp))

    def no_compile_to_regexp(self):
        '''
        Disable compilation of simple matchers to regular expressions.
        '''
        from lepl.regexp.rewriters import CompileRegexp
        return self.remove_all_rewriters(CompileRegexp)
    
    def optimize_or(self, conservative=False):
        '''
        Rearrange arguments to `Or()` so that left-recursive matchers are
        tested last.  This improves efficiency, but may alter the parser
        semantics (the ordering of multiple results with ambiguous grammars 
        may change).
        
        `conservative` refers to the algorithm used to detect loops; False
        may classify some left--recursive loops as right--recursive.

        This is part of the default configuration.  It can be removed with
        `no_optimize_or`.        
        '''
        from lepl.core.rewriters import OptimizeOr
        return self.add_rewriter(OptimizeOr(conservative))
    
    def no_optimize_or(self):
        '''
        Disable the re-ordering of some `Or()` arguments.
        '''
        from lepl.core.rewriters import OptimizeOr
        return self.remove_all_rewriters(OptimizeOr)
        
    def lexer(self, alphabet=None, discard=None, source=None):
        '''
        Detect the use of `Token()` and modify the parser to use the lexer.
        If tokens are not used, this has no effect on parsing.
        
        This is part of the default configuration.  It can be disabled with
        `no_lexer`.
        '''
        from lepl.lexer.rewriters import AddLexer
        self.alphabet(alphabet)
        return self.add_rewriter(
            AddLexer(alphabet=self.__get_alphabet(), discard=discard, 
                     source=source))
        
    def no_lexer(self):
        '''
        Disable support for the lexer.
        '''
        from lepl.lexer.rewriters import AddLexer
        self.remove_all_rewriters(AddLexer)
    
    def direct_eval(self, spec=None):
        '''
        Combine simple matchers so that they are evaluated without 
        trampolining.  This improves efficiency (particularly because it
        reduces the number of matchers that can be memoized).
        
        This is part of the default configuration.  It can be removed with
        `no_direct_eval`.
        '''
        from lepl.core.rewriters import DirectEvaluation
        return self.add_rewriter(DirectEvaluation(spec))
    
    def no_direct_eval(self):
        '''
        Disable direct evaluation.
        '''
        from lepl.core.rewriters import DirectEvaluation
        return self.remove_all_rewriters(DirectEvaluation)
    
    def compose_transforms(self):
        '''
        Combine transforms (functions applied to results) with matchers.
        This may improve efficiency.
        
        This is part of the default configuration.  It can be removed with
        `no_compose_transforms`.
        '''
        from lepl.core.rewriters import ComposeTransforms
        return self.add_rewriter(ComposeTransforms())
    
    def no_compose_transforms(self):
        '''
        Disable the composition of transforms.
        '''
        from lepl.core.rewriters import ComposeTransforms
        return self.remove_all_rewriters(ComposeTransforms)
        
    def auto_memoize(self, conservative=False, full=False):
        '''
        LEPL can add memoization so that (1) complex matching is more 
        efficient and (2) left recursive grammars do not loop indefinitely.  
        However, in many common cases memoization decreases performance.
        This matcher therefore, by default, only adds memoization if it
        appears necessary for stability (case 2 above, when left recursion
        is possible).
        
        The ``conservative`` parameter controls how left-recursive loops are
        detected.  If False (default) then matchers are assumed to "consume"
        input.  This may be incorrect, in which case some left-recursive loops
        may be missed.  If True then all loops are considered left-recursive.
        This is safer, but results in much more expensive (slower) memoisation. 
        
        The `full` parameter can be used (set to True) to add memoization
        for case (1) above, in addition to case (2).  In other words, when
        True, all nodes are memozied; when False (the default) only 
        left-recursive nodes are memoized.
        
        This is part of the default configuration.
        
        See also `no_memoize()`.
        '''
        from lepl.core.rewriters import AutoMemoize
        from lepl.matchers.memo import LMemo, RMemo
        self.no_memoize()
        return self.add_rewriter(AutoMemoize(conservative, LMemo,
                                             RMemo if full else None))
    
    def left_memoize(self):
        '''
        Add memoization that can detect and stabilise left-recursion.  This
        makes the parser more robust (so it can handle more grammars) but
        also significantly slower.
        '''
        from lepl.core.rewriters import Memoize
        from lepl.matchers.memo import LMemo
        self.no_memoize()
        return self.add_rewriter(Memoize(LMemo))
    
    def right_memoize(self):
        '''
        Add memoization that can make some complex parsers (with a lot of
        backtracking) more efficient.  In most cases, however, it makes
        the parser slower.
        '''      
        from lepl.core.rewriters import Memoize
        from lepl.matchers.memo import RMemo
        self.no_memoize()
        return self.add_rewriter(Memoize(RMemo))
    
    def no_memoize(self):
        '''
        Remove memoization.  To use the default configuration without
        memoization, specify `config.no_memoize()`.
        '''
        from lepl.core.rewriters import AutoMemoize, Memoize
        self.remove_all_rewriters(Memoize)
        return self.remove_all_rewriters(AutoMemoize)
        
    def blocks(self, block_policy=None, block_start=None):
        '''
        Set the given `block_policy` on all block elements and add a 
        `block_monitor` with the given `block_start`.  If either is
        not given, default values are used.
        
        Although these options are required for "offside rule" parsing,
        you normally do not need to call this because it is called by 
        `default_line_aware`  if either `block_policy` or 
        `block_start` is specified.
        '''
        from lepl.offside.matchers import DEFAULT_POLICY 
        from lepl.offside.monitor import block_monitor
        if block_policy is None:
            block_policy = DEFAULT_POLICY
        if block_start is None:
            block_start = 0
        self.add_monitor(block_monitor(block_start))
        self.set_block_policy_arg(block_policy)
        return self
    
    def line_aware(self, alphabet=None, parser_factory=None,
                   discard=None, tabsize=-1, 
                   block_policy=None, block_start=None):
        '''
        Configure the parser for line aware behaviour.  This clears the
        current setting and sets many different options.
        
        Although these options are required for "line aware" parsing,
        you normally do not need to call this because it is called by 
        `default_line_aware` .
        
        `alphabet` is the alphabet used; by default it is assumed to be Unicode
        and it will be extended to include start and end of line markers.
        
        `parser_factory` is used to generate a regexp parser.  If this is unset
        then the parser used depends on whether blocks are being used.  If so,
        then the HideSolEolParser is used (so that you can specify tokens 
        without worrying about SOL and EOL); otherwise a normal parser is
        used.
        
        `discard` is a regular expression which is matched against the stream
        if lexing otherwise fails.  A successful match is discarded.  If None
        then the usual token defaut is used (whitespace).  To disable, use
        an empty string.
        
        `tabsize`, if not None, should be the number of spaces used to replace
        tabs.
        
        `block_policy` should be the number of spaces in an indent, if blocks 
        are used (or an appropriate function).  By default (ie if `block_start`
        is given) it is taken to be DEFAULT_POLICY.
        
        `block_start` is the initial indentation, if blocks are used.  By 
        default (ie if `block_policy` is given) 0 is used.
        
        To enable blocks ("offside rule" parsing), at least one of 
        `block_policy` and `block_start` must be given.
        `
        '''
        from lepl.offside.matchers import DEFAULT_TABSIZE
        from lepl.offside.regexp import LineAwareAlphabet, \
            make_hide_sol_eol_parser
        from lepl.offside.stream import LineAwareStreamFactory, \
            LineAwareTokenSource
        from lepl.regexp.str import make_str_parser
        from lepl.regexp.unicode import UnicodeAlphabet
        
        self.clear()
        
        use_blocks = block_policy is not None or block_start is not None
        if use_blocks:
            self.blocks(block_policy, block_start)
            
        if tabsize and tabsize < 0:
            tabsize = DEFAULT_TABSIZE
        if alphabet is None:
            alphabet = UnicodeAlphabet.instance()
        if not parser_factory:
            if use_blocks:
                parser_factory = make_hide_sol_eol_parser
            else:
                parser_factory = make_str_parser
        self.alphabet(LineAwareAlphabet(alphabet, parser_factory))

        self.set_alphabet_arg()
        if use_blocks:
            self.set_block_policy_arg(block_policy)
        self.lexer(alphabet=self.__get_alphabet(), discard=discard, 
                   source=LineAwareTokenSource.factory(tabsize))
        self.stream_factory(LineAwareStreamFactory(self.__get_alphabet()))
        
        return self
        
    # monitors
    
    def trace(self, enabled=False):
        '''
        Add a monitor to trace results.  See `TraceResults()`.
        '''
        from lepl.core.trace import TraceResults
        return self.add_monitor(TraceResults(enabled))
    
    def manage(self, queue_len=0):
        '''
        Add a monitor to manage resources.  See `GeneratorManager()`.
        '''
        from lepl.core.manager import GeneratorManager
        return self.add_monitor(GeneratorManager(queue_len))
    
    def record_deepest(self, n_before=6, n_results_after=2, n_done_after=2):
        '''
        Add a monitor to record deepest match.  See `RecordDeepest()`.
        '''
        from lepl.core.trace import RecordDeepest
        return self.add_monitor(
                RecordDeepest(n_before, n_results_after, n_done_after))
    
    # packages
    
    def default_line_aware(self, alphabet=None, parser_factory=None,
                           discard=None, tabsize=-1, 
                           block_policy=None, block_start=None):
        '''
        Configure the parser for line aware behaviour.  This sets many 
        different options and is intended to be the "normal" way to enable
        line aware parsing (including "offside rule" support).
        
        Compared to `line_aware`, this also adds various "standard" options.
        
        Normally calling this method is all that is needed for configuration.
        If you do need to "fine tune" the configuration for parsing should
        consult the source for this method and then call other methods
        as needed.
        
        `alphabet` is the alphabet used; by default it is assumed to be Unicode
        and it will be extended to include start and end of line markers.
        
        `parser_factory` is used to generate a regexp parser.  If this is unset
        then the parser used depends on whether blocks are being used.  If so,
        then the HideSolEolParser is used (so that you can specify tokens 
        without worrying about SOL and EOL); otherwise a normal parser is
        used.
        
        `discard` is a regular expression which is matched against the stream
        if lexing otherwise fails.  A successful match is discarded.  If None
        then the usual token defaut is used (whitespace).  To disable, use
        an empty string.
        
        `tabsize`, if not None, should be the number of spaces used to replace
        tabs.
        
        `block_policy` should be the number of spaces in an indent, if blocks 
        are used (or an appropriate function).  By default (ie if `block_start`
        is given) it is taken to be DEFAULT_POLICY.
        
        `block_start` is the initial indentation, if blocks are used.  By 
        default (ie if `block_policy` is given) 0 is used.
        
        To enable blocks ("offside rule" parsing), at least one of 
        `block_policy` and `block_start` must be given.
        `
        '''
        self.line_aware(alphabet, parser_factory, discard, tabsize, 
                        block_policy, block_start)
        self.flatten()
        self.compose_transforms()
        self.auto_memoize()
        self.optimize_or()
        self.direct_eval()
        self.compile_to_nfa()
        self.full_first_match()
        return self
    
    def clear(self):
        '''
        Delete any earlier configuration and disable the default (so no
        rewriters or monitors are used).
        '''
        self.__started = True
        self.clear_cache()
        self.__rewriters = set()
        self.__monitors = []
        self.__stream_factory = DEFAULT_STREAM_FACTORY
        self.__alphabet = None
        return self

    def default(self):
        '''
        Provide the default configuration (deleting what may have been
        configured previously).  This is equivalent to the initial 
        configuration.  It provides a moderately efficient, stable parser.
        '''
        self.clear()
        self.flatten()
        self.compose_transforms()
        self.lexer()
        self.auto_memoize()
        self.direct_eval()
        self.compile_to_nfa()
        self.full_first_match()
        return self


class ParserMixin(object):
    '''
    Methods to configure and generate a parser or matcher.
    '''
    
    def __init__(self, *args, **kargs):
        super(ParserMixin, self).__init__(*args, **kargs)
        self.config = ConfigBuilder()
        self.__raw_parser_cache = None
        self.__from = None

    def _raw_parser(self, from_=None):
        if self.config.changed or self.__raw_parser_cache is None \
                or self.__from != from_:
            config = self.config.configuration
            self.__from = from_
            if from_:
                stream_factory = getattr(config.stream_factory, 'from_' + from_)
            else:
                stream_factory = config.stream_factory.auto
            self.__raw_parser_cache = \
                make_raw_parser(self, stream_factory, config)
        return self.__raw_parser_cache
    
    
    def get_match_file(self):
        '''
        Get a function that will parse the contents of a file, 
        returning a sequence of (results, stream) pairs and using a 
        stream internally.
        '''
        return self._raw_parser('file')
        
    def get_match_items(self):
        '''
        Get a function that will parse the contents of a sequence of items 
        (an item is something that would be matched by `Any`), returning a 
        sequence of (results, stream) pairs and using a stream internally.
        '''
        return self._raw_parser('items')
        
    def get_match_path(self):
        '''
        Get a function that will parse the contents of a file, 
        returning a sequence of (results, stream) pairs and using a 
        stream internally.
        '''
        return self._raw_parser('path')
        
    def get_match_string(self,):
        '''
        Get a function that will parse the contents of a string, 
        returning a sequence of (results, stream) pairs and using a 
        stream internally.
        '''
        return self._raw_parser('string')
    
    def get_match_null(self):
        '''
        Get a function that will parse the contents of a string or list, 
        returning a sequence of (results, stream) pairs 
        (this does not use streams).
        '''
        return self._raw_parser('null')
    
    def get_match(self):
        '''
        Get a function that will parse input, returning a sequence of 
        (results, stream) pairs and using a stream internally.  
        The type of stream is inferred from the input to the parser.
        '''
        return self._raw_parser()
    
    
    def match_file(self, file_, **kargs):
        '''
        Parse the contents of a file, returning a sequence of 
        (results, stream) pairs and using a stream internally.
        '''
        return self.get_match_file()(file_, **kargs)
        
    def match_items(self, list_, **kargs):
        '''
        Parse the contents of a sequence of items (an item is something
        that would be matched by `Any`), returning a sequence of 
        (results, stream) pairs and using a stream internally.
        '''
        return self.get_match_items()(list_, **kargs)
        
    def match_path(self, path, **kargs):
        '''
        Parse the contents of a file, returning a sequence of 
        (results, stream) pairs and using a stream internally.
        '''
        return self.get_match_path()(path, **kargs)
        
    def match_string(self, string, **kargs):
        '''
        Parse the contents of a string, returning a sequence of 
        (results, stream) pairs and using a stream internally.
        '''
        return self.get_match_string()(string, **kargs)
    
    def match_null(self, stream, **kargs):
        '''
        Parse the contents of a string or list, returning a sequence of 
        (results, stream) pairs (this does not use streams).
        '''
        return self.get_match_null()(stream, **kargs)
    
    def match(self, stream, **kargs):
        '''
        Parse the input, returning a sequence of 
        (results, stream) pairs and using a stream internally.  
        The type of stream is inferred from the input to the parser.
        '''
        return self.get_match()(stream, **kargs)
    
    
    def get_parse_file(self):
        '''
        Get a function that will parse the contents of a file, 
        returning a single match and using a stream internally.
        '''
        return make_single(self.get_match_file())
        
    def get_parse_items(self):
        '''
        Get a function that will parse the contents of a sequence of items 
        (an item is something that would be matched by `Any`), 
        returning a single match and using a stream internally.
        '''
        return make_single(self.get_match_items())
        
    def get_parse_path(self):
        '''
        Get a function that will parse the contents of a file, 
        returning a single match and using a stream internally.
        '''
        return make_single(self.get_match_path())
        
    def get_parse_string(self):
        '''
        Get a function that will parse the contents of a string, 
        returning a single match and using a stream internally.
        '''
        return make_single(self.get_match_string())
    
    def get_parse_null(self):
        '''
        Get a function that will parse the contents of a string or list, 
        returning a single match (this does not use streams).
        '''
        return make_single(self.get_match_null())
    
    def get_parse(self):
        '''
        Get a function that will parse the input, 
        returning a single match and using a stream internally.
        The type of stream is inferred from the input to the parser.
        '''
        return make_single(self.get_match())
    
    
    def parse_file(self, file_, **kargs):
        '''
        Parse the contents of a file, returning a single match and using a
        stream internally.
        '''
        return self.get_parse_file()(file_, **kargs)
        
    def parse_items(self, list_, **kargs):
        '''
        Parse the contents of a sequence of items (an item is something
        that would be matched by `Any`), returning a single match and using a
        stream internally.
        '''
        return self.get_parse_items()(list_, **kargs)
        
    def parse_path(self, path, **kargs):
        '''
        Parse the contents of a file, returning a single match and using a
        stream internally.
        '''
        return self.get_parse_path()(path, **kargs)
        
    def parse_string(self, string, **kargs):
        '''
        Parse the contents of a string, returning a single match and using a
        stream internally.
        '''
        return self.get_parse_string()(string, **kargs)
    
    def parse_null(self, stream, **kargs):
        '''
        Parse the contents of a string or list, returning a single match (this
        does not use streams).
        '''
        return self.get_parse_null()(stream, **kargs)
    
    def parse(self, stream, **kargs):
        '''
        Parse the input, returning a single match and using a stream internally.
        The type of stream is inferred from the input to the parser.
        '''
        return self.get_parse()(stream, **kargs)
    
    
    def get_parse_file_all(self):
        '''
        Get a function that will parse the contents of a file, 
        returning a sequence of matches and using a stream internally.
        '''
        return make_multiple(self.get_match_file())
        
    def get_parse_items_all(self):
        '''
        Get a function that will parse a sequence of items 
        (an item is something that would be matched by `Any`), 
        returning a sequence of matches and using a stream internally.
        '''
        return make_multiple(self.get_match_items())
        
    def get_parse_path_all(self):
        '''
        Get a function that will parse a file, returning a 
        sequence of matches and using a stream internally.
        '''
        return make_multiple(self.get_match_path())
        
    def get_parse_string_all(self):
        '''
        Get a function that will parse a string, returning a 
        sequence of matches and using a stream internally.
        '''
        return make_multiple(self.get_match_string())

    def get_parse_null_all(self):
        '''
        Get a function that will parse a string or list, returning a 
        sequence of matches (this does not use streams).
        '''
        return make_multiple(self.get_match_null())

    def get_parse_all(self):
        '''
        Get a function that will parse the input, returning a 
        sequence of matches and using a stream internally.
        The type of stream is inferred from the input to the parser.
        '''
        return make_multiple(self.get_match())

    
    def parse_file_all(self, file_, **kargs):
        '''
        Parse the contents of a file, returning a sequence of matches and using 
        a stream internally.
        '''
        return self.get_parse_file_all()(file_, **kargs)
        
    def parse_items_all(self, list_, **kargs):
        '''
        Parse a sequence of items (an item is something that would be matched
        by `Any`), returning a sequence of matches and using a
        stream internally.
        '''
        return self.get_parse_items_all()(list_, **kargs)
        
    def parse_path_all(self, path, **kargs):
        '''
        Parse a file, returning a sequence of matches and using a
        stream internally.
        '''
        return self.get_parse_path_all()(path, **kargs)
        
    def parse_string_all(self, string, **kargs):
        '''
        Parse a string, returning a sequence of matches and using a
        stream internally.
        '''
        return self.get_parse_string_all()(string, **kargs)

    def parse_null_all(self, stream, **kargs):
        '''
        Parse a string or list, returning a sequence of matches 
        (this does not use streams).
        '''
        return self.get_parse_null_all()(stream, **kargs)

    def parse_all(self, stream, **kargs):
        '''
        Parse the input, returning a sequence of matches and using a 
        stream internally. 
        The type of stream is inferred from the input to the parser.
        '''
        return self.get_parse_all()(stream, **kargs)
