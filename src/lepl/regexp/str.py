
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
Some intermediate classes that support parsers for objects that can be
converted to strings using str().
'''

from lepl.regexp.core import Alphabet, Character, Sequence, Choice, Repeat, \
    Option, _Choice
from lepl.support.lib import format, str, LogMixin


class StrParser(LogMixin):
    '''
    Construct a parser for string based expressions.
    
    We need a clear policy on backslashes.  To be as backwards compatible as
    possible I am going with:
    
      0. "Escaping" means prefixing with \.

      1. These characters are special: {, }, [, ], -, \, (, ), *, ?, ., +, 
         ^, $, |.

      2. Special characters (ie literal, or unescaped special characters) may 
         not have a meaning currently, or may only have a meaning in certain 
         contexts.

      3. To use a special character literally, it must be escaped.

      4. If a special character is used without an escape, in a context
         where it doesn't have a meaning, then it is an error.

      5. If a non-special character is escaped, that is also an error.
    
    This is not the same as the Python convention, but I believe it makes
    automatic escaping of given text easier.
    '''
    
    def __init__(self, alphabet):
        super(StrParser, self).__init__()
        self.alphabet = alphabet
        
    def dup(self, x):
        '''
        Create an interval from a single character.
        '''
        return (self.alphabet.from_char(x), self.alphabet.from_char(x))
    
    def tup(self, x):
        '''
        Create an interval from a tuple.
        '''
        return (self.alphabet.from_char(x[0]), self.alphabet.from_char(x[1]))
    
    def dot(self, _):
        '''
        Create a "complete" interval.
        '''
        return (self.alphabet.min, self.alphabet.max)
    
    def invert(self, x):
        '''
        Invert an interval.
        '''
        # Character needed here to ensure intervals passed to invert are ordered 
        return self.alphabet.invert(Character(x, self.alphabet))
    
    def sequence(self, x):
        '''
        Create a sequence.
        '''
        return Sequence(x, self.alphabet)
    
    def star(self, x):
        '''
        Repeat a sub-expression.
        '''
        return Repeat(x, self.alphabet)
    
    def plus(self, x):
        '''
        Repeat a sub-expression.
        '''
        return self.sequence([self.sequence(x), self.star(x)])
    
    def option(self, x):
        '''
        Make a sub-expression optional.
        '''
        return Option(x, self.alphabet)
    
    def choice(self, x):
        '''
        Construct a choice from a list of sub-expressions.
        '''
        return Choice(x, self.alphabet)
    
    def char(self, x):
        '''
        Construct a character from an interval (pair).
        '''
        return Character(x, self.alphabet)
    
    def extend(self, x):
        '''
        Delegate a character extension to the alphabet.
        '''
        return self.alphabet.extension(x)
    
    def build(self):
        '''
        Construct the parser.
        '''
        
        # Avoid dependency loops
        from lepl.matchers.derived import Drop, Eos, AnyBut, Upper
        from lepl.matchers.core import Any, Lookahead, Literal, Delayed
    
        # these two definitions enforce the conditions above, providing only
        # special characters appear as literals in the grammar
        escaped  = Drop(self.alphabet.escape) + Any(self.alphabet.escaped)
        raw      = ~Lookahead(self.alphabet.escape) + \
                        AnyBut(self.alphabet.escaped)
        
        single   = escaped | raw
        
        any_     = Literal('.')                                  >> self.dot
        letter   = single                                        >> self.dup
        pair     = single & Drop('-') & single                   > self.tup
        extend   = (Drop('(*') & Upper()[1:,...] & Drop(')'))    >> self.extend
        
        interval = pair | letter | extend
        brackets = Drop('[') & interval[1:] & Drop(']')
        inverted = Drop('[^') & interval[1:] & Drop(']')         >= self.invert      
        char     = inverted | brackets | letter | any_ | extend  > self.char
    
        item     = Delayed()
        
        seq      = (char | item)[0:]                             > self.sequence
        group    = Drop('(') & seq & Drop(')')
        alts     = Drop('(') & seq[2:, Drop('|')] & Drop(')')    > self.choice
        star     = (alts | group | char) & Drop('*')             > self.star
        plus     = (alts | group | char) & Drop('+')             > self.plus
        opt      = (alts | group | char) & Drop('?')             > self.option
        
        item    += alts | group | star | plus | opt
        
        expr     = (char | item)[:] & Drop(Eos())
    
        # Empty config here avoids loops if the default config includes
        # references to alphabets
        expr.config.clear()
        return expr.parse_string


def make_str_parser(alphabet):
    '''
    Create a parser.
    '''
    return StrParser(alphabet).build()


class StrAlphabet(Alphabet):
    '''
    Support for alphabets.
    '''
    
    # pylint: disable-msg=E1002
    # (pylint bug?  this chains back to a new style abc)
    def __init__(self, min_, max_, escape='\\', escaped='{}[]*()-?.+\\^$|',
                 parser_factory=make_str_parser):
        super(StrAlphabet, self).__init__(min_, max_)
        self.__escape = escape
        self.__escaped = escaped
        self._parser = parser_factory(self)
    
    @property
    def escape(self):
        return self.__escape
    
    @property
    def escaped(self):
        return self.__escaped
    
    def _escape_char(self, char):
        '''
        Escape a character if necessary.
        '''
        if self.escape is not None and str(char) in self.escaped:
            return self.escape + str(char)
        else:
            return str(char)
        
    def _no_parens(self, children):
        '''
        Returns True of no parens are needed around this when formatting.
        '''
        return len(children) == 1 and \
            (isinstance(children[0], Character) or
             len(children[0]) == 1 and isinstance(children[0][0], _Choice))
    
    def fmt_intervals(self, intervals):
        '''
        This must fully describe the data in the intervals (it is used to
        hash the data).
        '''
        def pretty(c):
            x = self._escape_char(c)
            if len(x) > 1 or str(' ') <= str(x) <= str('~'):
                return str(x)
            else:
                return repr(c)[1:-1]
        ranges = []
        if len(intervals) == 1:
            if intervals[0][0] == intervals[0][1]:
                return self._escape_char(intervals[0][0])
            elif intervals[0][0] == self.min and intervals[0][1] == self.max:
                return '.'
        # pylint: disable-msg=C0103
        # (sorry. but i use this (a, b) convention throughout the regexp lib) 
        for (a, b) in intervals:
            if a == b:
                ranges.append(self._escape_char(a))
            else:
                ranges.append(format('{0!s}-{1!s}', pretty(a), pretty(b)))
        return format('[{0}]', self.join(ranges))
    
    def fmt_sequence(self, children):
        '''
        Generate a string representation of a sequence.
        
        This must fully describe the data in the children (it is used to
        hash the data).
        '''
        return self.join(str(c) for c in children)
    
    def fmt_repeat(self, children):
        '''
        Generate a string representation of a repetition.
        
        This must fully describe the data in the children (it is used to
        hash the data).
        '''
        string = self.fmt_sequence(children)
        if self._no_parens(children):
            return string + '*'
        else:
            return format('({0})*', string)

    def fmt_choice(self, children):
        '''
        Generate a string representation of a choice.
        
        This must fully describe the data in the children (it is used to
        hash the data).
        '''
        return format('({0})', '|'.join(str(child) for child in children))

    def fmt_option(self, children):
        '''
        Generate a string representation of an option.
        
        This must fully describe the data in the children (it is used to
        hash the data).
        '''
        string = self.fmt_sequence(children)
        if self._no_parens(children):
            return string + '?'
        else:
            return format('({0})?', string)
        
    def fmt_label(self, label, child):
        '''
        Generate a string representation of labelled options.
        
        This must fully describe the data in the children (it is used to
        hash the data).
        '''
        return format('(?P<{0}>{1})', label, child)
        
    def join(self, chars):
        '''
        Join characters together.
        '''
        return ''.join(chars)
    
    def from_char(self, char):
        '''
        This must convert a single character.
        '''
        return char
    
    def parse(self, regexp):
        '''
        Generate a Sequence from the given text.
        '''
        return self._parser(regexp)

