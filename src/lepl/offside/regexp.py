
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
Extend regular expressions to be aware of additional tokens for line start
and end.
'''

from lepl.offside.support import LineAwareError, OffsideError
from lepl.regexp.core import Character
from lepl.regexp.str import StrAlphabet, StrParser
from lepl.support.lib import format


# pylint: disable-msg=W0105
# epydoc standard
START = 'SOL'
'''
Extension to represent start of line.
'''

END = 'EOL'
'''
Extension to represent end of line.
'''


# pylint: disable-msg=R0903
# using __ methods

class Marker(object):
    '''
    Used like a character, but represents start/end of line.
    '''
    
    def __init__(self, text, high):
        '''
        If high is true this is ordered after other letters, otherwise it is
        ordered before.
        '''
        self.text = text
        self.high = high
    
    def __gt__(self, other):
        return other is not self and self.high

    def __ge__(self, other):
        return other is self or self.high
    
    def __eq__(self, other):
        return other is self

    def __lt__(self, other):
        return other is not self and not self.high

    def __le__(self, other):
        return other is self or not self.high
    
    def __str__(self):
        return self.text
    
    def __hash__(self):
        return hash(repr(self))
    
    def __repr__(self):
        return format('Marker({0!r},{1!r})', self.text, self.high)
    
    def __len__(self):
        return 1
    
    def __radd__(self, other):
        '''
        Allow `stream + self` -> `stream` 
        (so string + EOL = string, for example).
        '''
        return other

def as_extension(x):
    return format('(*{0})', x)


SOL = Marker(as_extension(START), False)
'''
Marker to represent the start of a line.
'''

EOL = Marker(as_extension(END), True)
'''
Marker to represent the end of a line.
'''


# pylint: disable-msg=E1002
# pylint can't find ABCs
class LineAwareAlphabet(StrAlphabet):
    '''
    Extend an alphabet to include SOL and EOL tokens.
    '''
    
    def __init__(self, alphabet, parser_factory):
        if not isinstance(alphabet, StrAlphabet):
            raise LineAwareError(
                format('Only StrAlphabet subclasses supported: {0}/{1}',
                       alphabet, type(alphabet).__name__))
        super(LineAwareAlphabet, self).__init__(SOL, EOL,
                                                parser_factory=parser_factory)
        self.base = alphabet
        self.extensions = {START: SOL, END: EOL}
        
    def before(self, char):
        '''
        Append SOL before the base character set.
        '''
        if char == self.max:
            return self.base.max
        if char > self.base.min:
            return self.base.before(char)
        return self.min
    
    def after(self, char):
        '''
        Append EOL after the base character set.
        '''
        if char == self.min:
            return self.base.min
        if char < self.base.max:
            return self.base.after(char)
        return self.max
    
    def extension(self, text):
        '''
        This is called for extensions for the form (*NAME) where NAME is any
        sequence of capitals.  It should return a character range.  Further
        uses of (*...) are still to be decided.
        '''
        if text in self.extensions:
            extn = self.extensions[text]
            return (extn, extn)
        else:
            return super(LineAwareAlphabet, self).extension(text)
        
    def join(self, chars):
        '''
        Join characters together.
        '''
        return super(LineAwareAlphabet, self).join(
                    filter(lambda x: x not in (SOL, EOL), chars))
            
            
class HideSolEolParser(StrParser):
    '''
    Modify the parser to hide SOL and EOL from users (if you want to avoid
    this, go ahead and use StrParser with the line aware alphabet).
    '''
    
    def __init__(self, alphabet):
        super(HideSolEolParser, self).__init__(alphabet)
    
    def dot(self, _):
        '''
        Create a "complete" interval.
        '''
        return (self.alphabet.base.min, self.alphabet.base.max)
    
    def invert(self, x):
        '''
        Invert an interval.
        '''
        char = Character(x, self.alphabet)
        intervals = list(char)
        # if the interval already includes SOL or EOL then something odd is
        # happening and we just use the usual alphabet
        if intervals[0][0] == self.alphabet.min or \
                intervals[-1][1] == self.alphabet.max:
            raise OffsideError(format('Using {0!s} with explicit markers.\n'
                'Usually this means that you have (*SOL) or (*EOL) in a '
                'regular expression.  This should not be necessary.  If you '
                'do need to match those then you should disable their '
                'automatic management by setting '
                'parser_factory=make_str_parser in LineAwareConfiguration.',
                self.__class__))
            return self.alphabet.invert(char)
        # otherwise, avoid introducing them
        else:
            return self.alphabet.base.invert(char)
    

def make_hide_sol_eol_parser(alphabet):
    '''
    Create a new parser.
    '''
    return HideSolEolParser(alphabet).build()
