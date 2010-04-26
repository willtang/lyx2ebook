
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
A stream that adds tokens at the start and end of lines.
'''

from io import StringIO

from lepl.lexer.stream import TokenSource
from lepl.offside.lexer import START
from lepl.offside.support import LineAwareError, OffsideError
from lepl.stream.stream import DefaultStreamFactory, LineSource, sample
from lepl.support.lib import str


class LineAwareStreamFactory(DefaultStreamFactory):
    '''
    Generate line-aware streams for various input types.
    '''
    
    def __init__(self, alphabet):
        self.alphabet = alphabet

    def from_path(self, path):
        '''
        Generate a stream from a file at a given path.
        '''
        return self(LineAwareSource(self.alphabet, 
                                    open(path, 'rt', buffering=1),
                                    path))
    
    def from_string(self, text):
        '''
        Generate a stream from a string.
        '''
        return self(LineAwareSource(self.alphabet, StringIO(text), 
                                    sample('str: ', repr(text))))
    
    def from_lines(self, lines, source=None, join_=''.join):
        '''
        Generate a stream from a set of lines.
        '''
        if source is None:
            source = sample('lines: ', repr(lines))
        return self(LineAwareSource(self.alphabet, lines, source, join_))
    
    def from_items(self, items, source=None, line_length=80):
        '''
        Lists of items are not supported.
        '''
        raise LineAwareError('Only line-based sources are supported')
    
    def from_file(self, file_):
        '''
        Generate a stream from a file.
        '''
        return self(LineAwareSource(self.alphabet, file_, 
                                    getattr(file_, 'name', '<file>')) )

    @staticmethod
    def from_null(stream):
        '''
        Reject simple streams.
        '''
        raise LineAwareError('Only line-based sources are supported')


def top_and_tail(alphabet, lines):
    '''
    Create a sequence of lines that add SOL and EOL markers to the original
    text.
    '''
    def extend(line):
        '''
        Add the markers.
        '''
        return [alphabet.min] + list(line) + [alphabet.max]
    # pylint: disable-msg=W0141
    return map(extend, lines)
        
        
# pylint: disable-msg=E1002
# pylint can't find ABCs
class LineAwareSource(LineSource):
    '''
    A source to generate `LocationStream` instances from text that contains
    SOL and EOL tokens.
    '''
    
    def __init__(self, alphabet, lines, description=None, join_=None):
        if not join_:
            join_ = lambda lines: \
                ''.join([alphabet.join(line) for line in lines])
        super(LineAwareSource, self).__init__(
                        top_and_tail(alphabet, lines),
                        repr(lines) if description is None else description,
                        join_)
    
    def location(self, offset, line, location_state):
        '''
        Correct the location for the initial SOL character.
        '''
        (character_count, line_count) = location_state
        return (line_count, offset - 1, character_count + offset - 1, 
                line, str(self))
        
    def text(self, offset, line):
        '''
        Join characters together as a line of text.
        '''
        if line:
            # remember - join joins *lines*
            return self.join([line[offset:]])
        else:
            return self.join([])


class LineAwareTokenSource(TokenSource):
    '''
    Adapt `TokenSource` to replace tabs with spaces, if needed.
    '''
    
    def __init__(self, tokens, stream, tabsize):
        super(LineAwareTokenSource, self).__init__(tokens, stream)
        if tabsize:
            self.__tab = ''.join([' '] * tabsize)
        else:
            self.__tab = None
    
    def __next__(self):
        '''
        Provide (terminals, text) values (used by matchers) along with
        the original stream as location_state.
        
        Note that this is infinite - it is the StreamView that detects when
        the Line is empty and terminates any processing by the user.
        '''
        try:
            ([(terminals, text)], stream) = \
                    super(LineAwareTokenSource, self).__next__()
            if terminals and START in terminals:
                if not len(terminals) == 1:
                    raise OffsideError('More than one token matching ^')
                elif '\t' in text and self.__tab:
                    text = ''.join([char if char == ' ' else self.__tab
                                    for char in text])
            return ([(terminals, text)], stream)
        except TypeError:
            return (None, None)
        
    @staticmethod
    def factory(tabsize):
        '''
        Return a "constructor" that matches `TokenSource`.
        '''
        return lambda tokens, stream: \
            LineAwareTokenSource(tokens, stream, tabsize)

