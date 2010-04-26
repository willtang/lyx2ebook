
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
Tokens for indents.
'''


from lepl.lexer.matchers import BaseToken
from lepl.offside.monitor import BlockMonitor
from lepl.offside.regexp import START, END
from lepl.offside.support import OffsideError
from lepl.core.parser import tagged
from lepl.support.lib import format


# pylint: disable-msg=R0901, R0904, R0913, E1101
# lepl conventions
class Indent(BaseToken):
    '''
    Match an indent (start of line marker plus spaces and tabs).
    '''
    
    def __init__(self, content=None, id_=None, alphabet=None, complete=True, 
                 compiled=False):
        if id_ is None:
            id_ = START
        super(Indent, self).__init__(content=content, id_=id_, 
                                     alphabet=alphabet, complete=complete, 
                                     compiled=compiled)
        self.regexp = '(*SOL)[ \t]*'
                
        
class Eol(BaseToken):
    '''
    Match the end of line marker.
    '''
    
    def __init__(self, content=None, id_=None, alphabet=None, complete=True, 
                 compiled=False):
        if id_ is None:
            id_ = END
        super(Eol, self).__init__(content=content, id_=id_, 
                                  alphabet=alphabet, complete=complete, 
                                  compiled=compiled)
        self.regexp = '(*EOL)'


class BIndent(Indent):
    '''
    Extend `Indent` so that it matches the block indent level.
    
    Content is supported, but checking of matched length happens after
    matching content, so it's probably not that helpful.
    '''
    
    def __init__(self, content=None, id_=None, alphabet=None, complete=True, 
                 compiled=False):
        super(BIndent, self).__init__(content=content, id_=id_, 
                                      alphabet=alphabet, complete=complete, 
                                      compiled=compiled)
        self.monitor_class = BlockMonitor
        self.__current_indent = None
        
    def on_push(self, monitor):
        '''
        Read the global indentation level.
        '''
        self.__current_indent = monitor.indent
        
    def on_pop(self, monitor):
        '''
        Unused
        '''
    
    @tagged
    def _match(self, stream_in):
        '''
        Check that we match the current level
        '''
        if self.__current_indent is None:
            raise OffsideError('No initial indentation has been set. '
                               'You probably have not specified one of '
                               'block_policy or block_start in the '
                               'configuration')
        try:
            generator = super(BIndent, self)._match(stream_in)
            while True:
                (indent, stream) = yield generator
                if len(indent[0]) == self.__current_indent:
                    yield (indent, stream)
                else:
                    self._debug(
                        format('Incorrect indent ({0:d} != len({1!r}), {2:d})',
                               self.__current_indent, indent[0], 
                               len(indent[0])))
        except StopIteration:
            return


