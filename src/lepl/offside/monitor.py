
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
Support the stack-scoped tracking of indent level blocks.
'''


from lepl.core.monitor import ActiveMonitor
from lepl.offside.support import OffsideError
from lepl.support.state import State
from lepl.support.lib import LogMixin, format


class BlockMonitor(ActiveMonitor, LogMixin):
    '''
    This tracks the current indent level (in number of spaces).  It is
    read by `Line` and updated by `Block`.
    '''
    
    def __init__(self, start=0):
        '''
        start is the initial indent (in spaces).
        '''
        super(BlockMonitor, self).__init__()
        self.__stack = [start]
        self.__state = State.singleton()
        
    def push_level(self, level):
        '''
        Add a new indent level.
        '''
        self.__stack.append(level)
        self.__state[BlockMonitor] = level
        self._debug(format('Indent -> {0:d}', level))
        
    def pop_level(self):
        '''
        Drop one level.
        '''
        self.__stack.pop()
        if not self.__stack:
            raise OffsideError('Closed an unopened indent.') 
        self.__state[BlockMonitor] = self.indent
        self._debug(format('Indent <- {0:d}', self.indent))
       
    @property
    def indent(self):
        '''
        The current indent value (number of spaces).
        '''
        return self.__stack[-1]
    

def block_monitor(start=0):
    '''
    Add an extra lambda for the standard monitor interface.
    '''
    return lambda: BlockMonitor(start)
