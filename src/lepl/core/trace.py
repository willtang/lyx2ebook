
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
Tools for logging and tracing.
'''

# we abuse conventions to give a consistent interface 
# pylint: disable-msg=C0103

from lepl.core.monitor import ActiveMonitor, ValueMonitor, StackMonitor
from lepl.support.lib import CircularFifo, LogMixin, sample, format, str


def TraceResults(enabled=False):
    '''
    A basic logger (implemented as a monitor - `MonitorInterface`)
    that records the flow of control during parsing.  It can be controlled by 
    `Trace()`.

    This is a factory that "escapes" the main class via a function to simplify 
    configuration.
    '''
    return lambda: _TraceResults(enabled)


class _TraceResults(ActiveMonitor, ValueMonitor, LogMixin):
    '''
    A basic logger (implemented as a monitor - `MonitorInterface`)
    that records the flow of control during parsing.  It can be controlled by 
    `Trace()`.
    '''
    
    def __init__(self, enabled=False):
        super(_TraceResults, self).__init__()
        self.generator = None
        self.depth = -1
        self.action = None
        self.enabled = 1 if enabled else 0
        self.epoch = 0
    
    def next_iteration(self, epoch, value, exception, stack):
        '''
        Store epoch and stack size.
        '''
        self.epoch = epoch
        self.depth = len(stack)
    
    def before_next(self, generator):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            self.generator = generator
            self.action = format('next({0})', generator)
    
    def after_next(self, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            self._log_result(value, self.fmt_result(value))
    
    def before_throw(self, generator, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            self.generator = generator
            if type(value) is StopIteration:
                self.action = format('stop  ->  {0}', generator)
            else:
                self.action = format('{1!r}  ->  {0}', generator, value)
    
    def after_throw(self, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            self._log_result(value, self.fmt_result(value))
    
    def before_send(self, generator, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            self.generator = generator
            self.action = format('{1!r}  ->  {0}', generator, value)
    
    def after_send(self, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            self._log_result(value, self.fmt_result(value))
    
    def exception(self, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            if type(value) is StopIteration:
                self._log_done(self.fmt_done())
            else:
                self._log_error(self.fmt_result(value))
        
    def fmt_result(self, value):
        '''
        Provide a standard format for the results.
        '''
        (stream, depth, locn) = self.fmt_stream() 
        return format('{0:05d} {1!r:11s} {2} ({3:04d}) {4:03d} '
                      '{5:s}  ->  {6!r}',
                      self.epoch, 
                      stream,
                      locn,
                      depth,
                      self.depth,
                      self.action,
                      value)
                
    def fmt_done(self):
        '''
        Provide a standard format for failure.
        '''
        (stream, depth, locn) = self.fmt_stream() 
        return format('{0:05d} {1!r:11s} {2} ({3:04d}) {4:03d} '
                      '{5:s}  ->  stop',
                      self.epoch, 
                      stream,
                      locn,
                      depth,
                      self.depth,
                      self.action)
                
    def fmt_stream(self):
        '''
        Provide a standard format for location.
        '''
        try:
            (lineno, offset, depth, _text, _source) = \
                    self.generator.stream.location
            if not isinstance(lineno, int):
                locn = format('{0:<3d}', offset)
            elif lineno < 0:
                locn = '  eof  '
            else:
                locn = format('{0:3d}.{1:<3d}', lineno, offset)
        except AttributeError: # no .location above
            depth = -len(self.generator.stream)
            locn = '<unknown>'
        stream = sample('', str(self.generator.stream), 9)
        return (stream, depth, locn)
        
    def yield_(self, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            self._info(self.fmt_final_result(value))
        
    def raise_(self, value):
        '''
        Log when enabled.
        '''
        if self.enabled > 0:
            if type(value) is StopIteration:
                self._info(self.fmt_final_result(format('raise {0!r}', value)))
            else:
                self._warn(self.fmt_final_result(format('raise {0!r}', value)))
        
    def fmt_final_result(self, value):
        '''
        Provide a standard format for the result.
        '''
        return format('{0:05d}                            {1:03d} {2} {3}',
                      self.epoch,
                      self.depth,
                      ' ' * 63,
                      value)

    def _log_result(self, value, text):
        '''
        Record a result.
        '''
        (self._info if type(value) is tuple else self._debug)(text)    

    def _log_error(self, text):
        '''
        Record an error.
        '''
        self._warn(text)    

    def _log_done(self, text):
        '''
        Record a "stop".
        '''
        self._debug(text)
        
    def switch(self, increment):
        '''
        Called by the `Trace` matcher to turn this on and off.
        '''
        self.enabled += increment
    

def RecordDeepest(n_before=6, n_results_after=2, n_done_after=2):
    '''
    A logger (implemented as a monitor - `MonitorInterface`)
    that records the deepest match found during a parse.

    This is a helper function that "escapes" the main class via a function
    to simplify configuration.
    '''
    return lambda: _RecordDeepest(n_before, n_results_after, n_done_after)


class _RecordDeepest(_TraceResults):
    '''
    A logger (implemented as a monitor - `MonitorInterface`)
    that records the deepest match found during a parse.
    '''
    
    def __init__(self, n_before=6, n_results_after=2, n_done_after=2):
        super(_RecordDeepest, self).__init__(enabled=True)
        self.n_before = n_before
        self.n_results_after = n_results_after
        self.n_done_after = n_done_after
        self._limited = CircularFifo(n_before)
        self._before = []
        self._results_after = []
        self._done_after = []
        self._deepest = -1e99
        self._countdown_result = 0
        self._countdown_done = 0
        
    def _log_result(self, value, text):
        '''
        Modify `TraceResults` to record the data.
        '''
        if type(value) is tuple:
            self.record(True, text)

    def _log_error(self, text):
        '''
        Modify `TraceResults` to record the data.
        '''
        self.record(True, text)

    def _log_done(self, text):
        '''
        Modify `TraceResults` to record the data.
        '''
        self.record(False, text)

    def record(self, is_result, text):
        '''
        Record the data.
        '''
        stream = self.generator.stream
        try:
            depth = stream.depth()
        except AttributeError: # no .depth()
            depth = -len(stream)
        if depth >= self._deepest and is_result:
            self._deepest = depth
            self._countdown_result = self.n_results_after
            self._countdown_done = self.n_done_after
            self._before = list(self._limited)
            self._results_after = []
            self._done_after = []
        elif is_result and self._countdown_result:
            self._countdown_result -= 1
            self._results_after.append(text)
        elif not is_result and self._countdown_done:
            self._countdown_done -= 1
            self._done_after.append(text)
        self._limited.append(text)
        
    def yield_(self, value):
        '''
        Display the result.
        
        (As I document this code later, it is no longer clear why this does so)
        '''
        self._deepest = 0
        self._limited.clear()
        self.__display()
        
    def raise_(self, value):
        '''
        Display the result.
        
        (As I document this code later, it is no longer clear why this does so)
        '''
        self._deepest = 0
        self._limited.clear()
        self.__display()
        
    def __display(self):
        '''
        Display the result.
        '''
        self._info(self.__format())
        
    def __format(self):
        '''
        Format the result.
        '''
        return format(
            '\nUp to {0} matches before and including longest match:\n{1}\n'
            'Up to {2} failures following longest match:\n{3}\n'
            'Up to {4} successful matches following longest match:\n{5}\n',
            self.n_before, '\n'.join(self._before),
            self.n_done_after, '\n'.join(self._done_after),
            self.n_results_after, '\n'.join(self._results_after))


class StreamMonitor(StackMonitor):
    '''
    This prints (not logs) data about streams.  It is intended for debugging,
    not normal use.
    '''
    
    def __init__(self):
        self._streams = {}
    
    def push(self, generator):
        '''
        Called before adding a generator to the stack.
        '''
        stream = generator.stream
        type_ = type(stream)
        new = False
        if type_ not in self._streams:
            print(format('Found new stream type: {0}', type_))
            self._streams[type_] = set()
        streams = self._streams[type_]
        if stream not in streams:
            streams.add(stream)
            if stream in streams:
                new = True
        if new:
            print(format('Found new stream: {2} {0} ({1})', 
                         stream, type_, hash(stream)))
            print(format(' source {1} ({0})', 
                         stream.source, type(stream.source)))
            
    