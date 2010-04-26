
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
Error handling (generating an error while parsing).

This is not that complete or well thought through; it needs to be revised.
'''

from lepl.support.node import Node
from lepl.support.lib import format


def make_error(msg):
    '''
    Create an error node using a format string.
    
    Invoke as ``** make_error('bad results: {results}')``, for example.
    '''
    def fun(stream_in, stream_out, results):
        '''
        Create the error node when results are available.
        '''
        return Error(*syntax_error_args(msg, stream_in, stream_out, results))
    return fun


STREAM_IN = 'stream_in'
STREAM_OUT = 'stream_out'
RESULTS = 'results'
FILENAME = 'filename'
LINENO = 'lineno'
OFFSET = 'offset'
LINE = 'line'


def syntax_error_args(msg, stream_in, stream_out, results):
    '''
    Helper function for constructing format dictionary.
    '''
    kargs = syntax_error_kargs(stream_in, stream_out, results)
    filename = kargs[FILENAME]
    lineno = kargs[LINENO]
    offset = kargs[OFFSET]
    line = kargs[LINE]
    # pylint: disable-msg=W0142
    return (format(msg, **kargs), (filename, lineno, offset, line))


def syntax_error_kargs(stream_in, stream_out, results):
    '''
    Helper function for constructing format dictionary.
    '''
    try:
        (lineno, offset, _depth, line, filename) = stream_in.location
        offset += 1 # appears to be 1-based?
    except AttributeError:
        filename = '<unknown> - use stream for better error reporting'
        lineno = -1
        offset = -1
        try:
            line = '...' + stream_in
        except TypeError:
            line = ['...'] + stream_in
    kargs = {STREAM_IN: stream_in, STREAM_OUT: stream_out, 
             RESULTS: results, FILENAME: filename, 
             LINENO: lineno, OFFSET:offset, LINE:line}
    return kargs


def raise_error(msg):
    '''
    As `make_error()`, but also raise the result.
    '''
    def fun(stream_in, stream_out, results):
        '''
        Delay raising the error until called in the parser.
        '''
        raise make_error(msg)(stream_in, stream_out, results)
    return fun


class Error(Node, SyntaxError):
    '''
    Subclass `Node` and Python's SyntaxError to provide an AST
    node that can be raised as an error via `node_throw` or `sexpr_throw`.
    
    Create with `make_error()`.
    '''
    
    def __init__(self, msg, location):
        # pylint: disable-msg=W0142
        Node.__init__(self, msg, location)
        SyntaxError.__init__(self, msg, location)
        
    def __str__(self):
        return SyntaxError.__str__(self)

