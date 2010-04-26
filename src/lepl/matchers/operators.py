
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
Support for operator syntactic sugar (and operator redefinition).
'''

from lepl.matchers.matcher import Matcher
from lepl.support.context import Namespace, NamespaceMixin, Scope
from lepl.support.lib import open_stop, format, basestring


class OperatorNamespace(Namespace):
    '''
    Define the default operators.
    '''
    
    def __init__(self):
        # Handle circular dependencies
        from lepl.matchers.error import raise_error
        from lepl.matchers.derived import Space, Add, Apply, KApply, Drop, \
            Repeat, Map
        from lepl.matchers.combine import And, Or, First
        super(OperatorNamespace, self).__init__({
            SPACE_OPT: lambda a, b: And(a, Space()[0:,...], b),
            SPACE_REQ: lambda a, b: And(a, Space()[1:,...], b),
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
            MAP:       Map
        })
    

OPERATORS = 'operators'
'''
The name used to retrieve operators definitions.
'''

SPACE_OPT = '/'
'''Name for / operator.'''
SPACE_REQ = '//'
'''Name for // operator.'''
ADD = '+'
'''Name for + operator.'''
AND = '&'
'''Name for & operator.'''
OR = '|'
'''Name for | operator.'''
APPLY = '>'
'''Name for > operator.'''
APPLY_RAW = '>='
'''Name for >= operator.'''
NOT = '~'
'''Name for ~ operator.'''
KARGS = '**'
'''Name for ** operator.'''
RAISE = '^'
'''Name for ^ operator.'''
REPEAT = '[]'
'''Name for [] operator.'''
FIRST = '%'
'''Name for % operator.'''
MAP = '>>'
'''Name for >> operator.'''


class Override(Scope):
    '''
    Allow an operator to be redefined within a with context.  Uses the 
    OPERATORS namespace.
    '''

    def __init__(self, space_opt=None, space_req=None, repeat=None,
                  add=None, and_=None, or_=None, not_=None, 
                  apply_=None, apply_raw=None, kargs=None, 
                  raise_=None, first=None, map_=None):
        super(Override, self).__init__(OPERATORS, OperatorNamespace,
            {SPACE_OPT: space_opt, SPACE_REQ: space_req,
             REPEAT: repeat, ADD: add, AND: and_, OR: or_, 
             NOT: not_, APPLY: apply_, APPLY_RAW: apply_raw,
             KARGS: kargs, RAISE: raise_, FIRST: first, MAP: map_})


class _BaseSeparator(Override):
    '''
    Support class for `Separator` and similar classes.
    
    Uses the OPERATORS namespace.
    '''
    
    def __init__(self, separator):
        '''
        If the separator is a string it is coerced to `Regexp()`; if None
        then any previous defined separator is effectively removed.
        '''
        # Handle circular dependencies
        from lepl.matchers.core import Regexp
        from lepl.matchers.combine import And
        from lepl.matchers.derived import Repeat
        from lepl.matchers.support import coerce_
        if separator is None:
            and_ = And
            repeat = Repeat
        else:
            separator = coerce_(separator, Regexp)
            (and_, repeat) = self._replacements(separator)
        super(_BaseSeparator, self).__init__(and_=and_, repeat=repeat)

    def _replacements(self, _separator):
        '''
        Sub-classes should return (And, Repeat)
        '''
        raise Exception('Unimplemented')
    
    def _repeat(self, separator):
        '''
        A simple Repeat with separator.
        '''
        from lepl.matchers.combine import And
        from lepl.matchers.derived import Repeat
        def repeat(m, st=0, sp=None, d=0, s=None, a=False):
            '''
            Wrap `Repeat` to adapt the separator.
            '''
            if s is None:
                s = separator
            elif not a:
                s = And(separator, s, separator)
            return Repeat(m, st, sp, d, s, a)
        return repeat
    

class Separator(_BaseSeparator):
    '''
    Redefine ``[]`` and ``&`` to include the given matcher as a separator 
    (so it will be used between list items and between matchers separated by the & 
    operator)
    
    Uses the OPERATORS namespace.
    '''
    
    def _replacements(self, separator):
        '''
        Require the separator on each `And`.
        '''
        # Handle circular dependencies
        from lepl.matchers.combine import And
        return (lambda a, b: And(a, separator, b),
                self._repeat(separator))
        
        
class DroppedSpace(Separator):
    '''
    Skip spaces (by default, one or more Space()).  Any argument is dropped.
    '''
    
    def __init__(self, space=None):
        from lepl.matchers.derived import Space, Drop
        if space is None:
            space = Space()[:]
        space = Drop(space)
        super(DroppedSpace, self).__init__(space)
        

class SmartSeparator1(_BaseSeparator):
    '''
    Similar to `Separator`, but tried to be clever about whether the 
    separator is needed.  It replaces `&` with a matcher that only uses 
    the separator if the second sub-matcher consumes some input.
    
    Uses the OPERATORS namespace.
    
    See also `SmartSeparator2`, which is less general, but more efficient.
    '''
    
    def _replacements(self, separator):
        '''
        Require the separator on each `And`.
        '''
        # Handle circular dependencies
        from lepl.matchers.combine import And, Or
        from lepl.matchers.core import Consumer
        def and_(a, b):
            '''
            Add space only in the case when both consume something.
            '''
            return Or(And(Consumer(a), separator, Consumer(b)),
                      And(Consumer(a), Consumer(b, False)),
                      And(Consumer(a, False), Consumer(b)),
                      And(Consumer(a, False), Consumer(b, False)))
        return (and_, self._repeat(separator))
   
        
GREEDY = 'g'
'''Flag (splice increment) for inefficient, guaranteed greedy matching.'''
NON_GREEDY = 'n'
'''Flag (splice increment) for inefficient, guaranteed non-greedy matching.'''
DEPTH_FIRST = 'd'
'''Flag (splice increment) for efficient, quasi-greedy, matching (default).'''
BREADTH_FIRST = 'b'
'''Flag (splice increment) for efficient, quasi-non-greedy, matching.'''


class OperatorMixin(NamespaceMixin):
    '''
    Define the operators used to combine elements in a grammar specification.
    '''

    def __init__(self, name, namespace):
        super(OperatorMixin, self).__init__(name, namespace)
        
    def __add__(self, other):
        '''
        **self + other** - Join strings, merge lists.
        
        Combine adjacent matchers in sequence, merging the result with "+" 
        (so strings are joined, lists merged).
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(ADD, other, True)
        return self._lookup(ADD)(self, other)

    def __radd__(self, other):
        '''
        **other + self** - Join strings, merge lists.
        
        Combine adjacent matchers in sequence, merging the result with "+" 
        (so strings are joined, lists merged).
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(ADD, other, True)
        return self._lookup(ADD)(other, self)

    def __and__(self, other):
        '''
        **self & other** - Append results.
        
        Combine adjacent matchers in sequence.  This is equivalent to 
        `And()`.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(AND, other, True)
        return self._lookup(AND)(self, other) 
        
    def __rand__(self, other):
        '''
        **other & self** - Append results.
        
        Combine adjacent matchers in sequence.  This is equivalent to 
        `And()`.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(AND, other, True)
        return self._lookup(AND)(other, self)
    
    def __div__(self, other):
        '''
        For 2.6
        '''
        return self.__truediv__(other)
    
    def __rdiv__(self, other):
        '''
        For 2.6
        '''
        return self.__rtruediv__(other)
    
    def __truediv__(self, other):
        '''
        **self / other** - Append results, with optional separating space.
        
        Combine adjacent matchers in sequence, with an optional space between
        them.  The space is included in the results.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(SPACE_OPT, other, True)
        return self._lookup(SPACE_OPT)(self, other)
        
    def __rtruediv__(self, other):
        '''
        **other / self** - Append results, with optional separating space.
        
        Combine adjacent matchers in sequence, with an optional space between
        them.  The space is included in the results.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(SPACE_OPT, other, True)
        return self._lookup(SPACE_OPT)(other, self)
        
    def __floordiv__(self, other):
        '''
        **self // other** - Append results, with required separating space.
        
        Combine adjacent matchers in sequence, with a space between them.  
        The space is included in the results.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(SPACE_REQ, other, True)
        return self._lookup(SPACE_REQ)(self, other)
        
    def __rfloordiv__(self, other):
        '''
        **other // self** - Append results, with required separating space.
        
        Combine adjacent matchers in sequence, with a space between them.  
        The space is included in the results.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(SPACE_REQ, other, True)
        return self._lookup(SPACE_REQ)(other, self)
        
    def __or__(self, other):
        '''
        **self | other** - Try alternative matchers.
        
        This introduces backtracking.  Matches are tried from left to right
        and successful results returned (one on each "recall").  This is 
        equivalent to `Or()`.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(OR, other, True)
        return self._lookup(OR)(self, other) 
        
    def __ror__(self, other):
        '''
        **other | self** - Try alternative matchers.
        
        This introduces backtracking.  Matches are tried from left to right
        and successful results returned (one on each "recall").  This is 
        equivalent to `Or()`.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(OR, other, True)
        return self._lookup(OR)(other, self) 
        
    def __mod__(self, other):
        '''
        **self % other** - Take first match (committed choice).
        
        Matches are tried from left to right and the first successful result
        is returned.  This is equivalent to `First()`.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(FIRST, other, True)
        return self._lookup(FIRST)(self, other) 
        
    def __rmod__(self, other):
        '''
        **other % self** - Take first match (committed choice).
        
        Matches are tried from left to right and the first successful result
        is returned.  This is equivalent to `First()`.
        
        :Parameters:
        
          other
            Another matcher or a string that will be converted to a literal
            match.
        '''
        self.__check(FIRST, other, True)
        return self._lookup(FIRST)(other, self) 
        
    def __invert__(self):
        '''
        **~self** - Discard the result.

        This generates a matcher that behaves as the original, but returns
        an empty list. This is equivalent to `Drop()`.
        
        Note that `Lookahead()` overrides this method to have
        different semantics (negative lookahead).
        '''
        return self._lookup(NOT)(self) 
        
    def __getitem__(self, indices):
        '''
        **self[start:stop:algorithm, separator, ...]** - Repetition and lists.
        
        This is a complex statement that modifies the current matcher so
        that it matches several times.  A separator may be specified
        (eg for comma-separated lists) and the results may be combined with
        "+" (so repeated matching of characters would give a word).
        
        start:stop:algorithm
          This controls the number of matches made and the order in which
          different numbers of matches are returned.
          
          [start]
            Repeat exactly *start* times
            
          [start:stop]
            Repeat *start* to *stop* times (starting with as many matches
            as possible, and then decreasing as necessary).
            
          [start:stop:algorithm]
            Direction selects the algorithm for searching.
            
            'b' (BREADTH_FIRST)
              A breadth first search is used, which tends to give shorter
              matches before longer ones.  This tries all possible matches for 
              the sub-matcher first (before repeating calls to consume more 
              of the stream).  If the sub-matcher does not backtrack then this 
              guarantees that the number of matches returned will not decrease 
              (ie will monotonically increase) on backtracking.
              
            'd' (DEPTH_FIRST)
              A depth first search is used, which tends to give longer
              matches before shorter ones.  This tries to repeats matches 
              with the sub-matcher, consuming as much of the stream as 
              possible, before backtracking to find alternative matchers.
              If the sub-matcher does not backtrack then this guarantees
              that the number of matches returned will not increase (ie will
              monotonically decrease) on backtracking.
              
            'g' (GREEDY)
              An exhaustive search is used, which finds all results (by 
              breadth first search) and orders them by length before returning 
              them ordered from longest to shortest.  This guarantees that
              the number of matches returned will not increase (ie will
              monotonically decrease) on backtracking, but can consume a lot 
              of resources.
              
            'n' (NON_GREEDY)
              As for 'g' (GREEDY), but results are ordered shortest to 
              longest.  This guarantees that the number of matches returned 
              will not decrease (ie will monotonically increase) on 
              backtracking, but can consume a lot of resources,
            
          Values may be omitted; the defaults are: *start* = 0, *stop* = 
          infinity, *algorithm* = 'd' (DEPTH_FIRST).

        separator
          If given, this must appear between repeated values.  Matched
          separators are returned as part of the result (unless, of course,
          they are implemented with a matcher that returns nothing).  If 
          *separator* is a string it is converted to a literal match.

        ...
          If ... (an ellipsis) is given then the results are joined together
          with "+".           

        Examples
        --------
        
        Any()[0:3,...] will match 3 or less characters, joining them
        together so that the result is a single string.
        
        Word()[:,','] will match a comma-separated list of words.
        
        value[:] or value[0:] or value[0::'d'] is a "greedy" match that,
        if value does not backtrack, is equivalent to the "*" in a regular
        expression.
        value[::'n'] is the "non-greedy" equivalent (preferring as short a 
        match as possible) and value[::'g'] is greedy even when value does
        provide alternative matches on backtracking.
        '''
        start = 0
        stop = None
        step = DEPTH_FIRST
        separator = None
        add = False
        if not isinstance(indices, tuple):
            indices = [indices]
        for index in indices:
            if isinstance(index, int):
                start = index
                stop = index
                step = DEPTH_FIRST
            elif isinstance(index, slice):
                start = index.start if index.start != None else 0
                stop = index.stop if not open_stop(index) else None
                step = index.step if index.step != None else DEPTH_FIRST
            elif index == Ellipsis:
                add = True
            elif separator is None:
                separator = index
            else:
                raise TypeError(index)
        return self._lookup(REPEAT)(self, start, stop, step, separator, add)
        
    def __gt__(self, function):
        '''
        **self > function** - Process or label the results.
        
        Create a named pair or apply a function to the results.  This is
        equivalent to `Apply()`.
        
        :Parameters:
        
          function
            This can be a string or a function.
            
            If a string is given each result is replaced by a 
            (name, value) pair, where name is the string and value is the
            result.
            
            If a function is given it is called with the results as an
            argument.  The return value is used *within a list* as the new 
            result.  This is equivalent to `Apply()` with raw=False.
        '''
        self.__check(APPLY, function, False)
        return self._lookup(APPLY)(self, function) 
    
    def __ge__(self, function):
        '''
        **self >= function** - Process or label the results.
        
        Apply a function to the results.  
        This is equivalent to `Apply(raw=True)`.
        
        :Parameters:
        
          function
            This is called with the results as an argument.  The return value 
            is used as the new result.  This is equivalent to `Apply()` with 
            raw=True.
        '''
        self.__check(APPLY_RAW, function, False)
        return self._lookup(APPLY_RAW)(self, function) 
    
    def __rshift__(self, function):
        '''
        **self >> function** - Process or label the results (map).
        
        Create a named pair or apply a function to each result in turn.  
        This is equivalent to `Map()`.  It is similar to 
        *self >= function*, except that the function is applied to each 
        result in turn.
        
        :Parameters:
        
          function
            This can be a string or a function.
            
            If a string is given each result is replaced by a 
            (name, value) pair, where name is the string and value is the
            result.
            
            If a function is given it is called with each result in turn.
            The return values are used as the new result.
        '''
        self.__check(MAP, function, False)
        return self._lookup(MAP)(self, function) 
        
    def __pow__(self, function):
        '''
        **self \** function** - Process the results (\**kargs).
        
        Apply a function to keyword arguments
        This is equivalent to `KApply()`.
        
        :Parameters:
        
          function
            A function that is called with the keyword arguments described below.
            The return value is used as the new result.

            Keyword arguments:
            
              stream_in
                The stream passed to the matcher.
    
              stream_out
                The stream returned from the matcher.
                
              results
                A list of the results returned.
        '''
        self.__check(KARGS, function, False)
        return self._lookup(KARGS)(self, function) 
    
    def __xor__(self, message):
        '''
        **self ^ message**
        
        Raise a SytaxError.
        
        :Parameters:
        
          message
            The message for the SyntaxError.
        '''
        return self._lookup(RAISE)(self, message)
                             
    def __check(self, name, other, is_match):
        '''
        Provide some diagnostics if the syntax is completely mixed up.
        '''
        if not isinstance(other, basestring): # can go either way
            if is_match != isinstance(other, Matcher):
                if is_match:
                    msg = 'The operator {0} for {1} was applied to something ' \
                        'that is not a matcher ({2}).'
                else:
                    msg = 'The operator {0} for {1} was applied to a matcher ' \
                        '({2}).'
                msg += ' Check syntax and parentheses.'
                raise SyntaxError(format(msg, name, self, other))

