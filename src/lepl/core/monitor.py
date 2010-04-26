
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
Support for classes that monitor the execution process (for example, managing 
resources and tracing program flow).

See `trampoline()`.
'''


class ValueMonitor(object):
    '''
    An interface expected by `trampoline()`, called to track data flow.
    '''
    
    def next_iteration(self, epoch, value, exception, stack):
        '''
        Called at the start of each iteration.
        '''
        pass
    
    def before_next(self, generator):
        '''
        Called before invoking ``next`` on a generator.
        '''
        pass
    
    def after_next(self, value):
        '''
        Called after invoking ``next`` on a generator.
        '''
        pass
    
    def before_throw(self, generator, value):
        '''
        Called before invoking ``throw`` on a generator. 
        '''
        pass
    
    def after_throw(self, value):
        '''
        Called after invoking ``throw`` on a generator. 
        '''
        pass
    
    def before_send(self, generator, value):
        '''
        Called before invoking ``send`` on a generator. 
        '''
        pass
    
    def after_send(self, value):
        '''
        Called after invoking ``send`` on a generator. 
        '''
        pass
    
    def exception(self, value):
        '''
        Called when an exception is caught (instead of any 'after' method).
        '''
        pass
    
    def raise_(self, value):
        '''
        Called before raising an exception to the caller.
        '''
        pass
    
    def yield_(self, value):
        '''
        Called before yielding a value to the caller.
        '''
        pass
    
    
class StackMonitor(object):
    '''
    An interface expected by `trampoline()`, called to track stack growth.
    '''
    
    def push(self, generator):
        '''
        Called before adding a generator to the stack.
        '''
        pass
    
    def pop(self, generator):
        '''
        Called after removing a generator from the stack.
        '''
        pass
    
    
class ActiveMonitor(StackMonitor):
    '''
    A `StackMonitor` implementation that allows matchers that implement the
    interface on_push/on_pop to be called. 
    
    Generators can interact with active monitors if:
    
      1. The monitor extends this class
    
      2. The matcher has a monitor_class attribute whose value is equal to (or a 
         subclass of) the monitor class it will interact with
    '''
    
    def push(self, generator):
        '''
        Called when a generator is pushed onto the trampoline stack.
        '''
        if hasattr(generator.matcher, 'monitor_class') and \
                isinstance(self, generator.matcher.monitor_class):
            generator.matcher.on_push(self)
        
    def pop(self, generator):
        '''
        Called when a generator is popped from the trampoline stack.
        '''
        if hasattr(generator.matcher, 'monitor_class') and \
                isinstance(self, generator.matcher.monitor_class):
            generator.matcher.on_pop(self)
        

class MultipleValueMonitors(ValueMonitor):
    '''
    Combine several value monitors into one.
    '''
    
    def __init__(self, monitors=None):
        super(MultipleValueMonitors, self).__init__()
        self._monitors = [] if monitors is None else monitors
        
    def append(self, monitor):
        '''
        Add another monitor to the chain.
        '''
        self._monitors.append(monitor)
        
    def __len__(self):
        return len(self._monitors)
    
    def next_iteration(self, epoch, value, exception, stack):
        '''
        Called at the start of each iteration.
        '''
        for monitor in self._monitors:
            monitor.next_iteration(epoch, value, exception, stack)
    
    def before_next(self, generator):
        '''
        Called before invoking ``next`` on a generator.
        '''
        for monitor in self._monitors:
            monitor.before_next(generator)
    
    def after_next(self, value):
        '''
        Called after invoking ``next`` on a generator.
        '''
        for monitor in self._monitors:
            monitor.after_next(value)
    
    def before_throw(self, generator, value):
        '''
        Called before invoking ``throw`` on a generator. 
        '''
        for monitor in self._monitors:
            monitor.before_throw(generator, value)
    
    def after_throw(self, value):
        '''
        Called after invoking ``throw`` on a generator. 
        '''
        for monitor in self._monitors:
            monitor.after_throw(value)
    
    def before_send(self, generator, value):
        '''
        Called before invoking ``send`` on a generator. 
        '''
        for monitor in self._monitors:
            monitor.before_send(generator, value)
    
    def after_send(self, value):
        '''
        Called after invoking ``send`` on a generator. 
        '''
        for monitor in self._monitors:
            monitor.after_send(value)
    
    def exception(self, value):
        '''
        Called when an exception is caught (instead of any 'after' method).
        '''
        for monitor in self._monitors:
            monitor.exception(value)
    
    def raise_(self, value):
        '''
        Called before raising an exception to the caller.
        '''
        for monitor in self._monitors:
            monitor.raise_(value)
    
    def yield_(self, value):
        '''
        Called before yielding a value to the caller.
        '''
        for monitor in self._monitors:
            monitor.yield_(value)
    

class MultipleStackMonitors(StackMonitor):
    '''
    Combine several stack monitors into one.
    '''
    
    def __init__(self, monitors=None):
        super(MultipleStackMonitors, self).__init__()
        self._monitors = [] if monitors is None else monitors
        
    def append(self, monitor):
        '''
        Add another monitor to the chain.
        '''
        self._monitors.append(monitor)
        
    def __len__(self):
        return len(self._monitors)
    
    def push(self, value):
        '''
        Called before adding a generator to the stack.
        '''
        for monitor in self._monitors:
            monitor.push(value)
    
    def pop(self, value):
        '''
        Called after removing a generator from the stack.
        '''
        for monitor in self._monitors:
            monitor.pop(value)


def prepare_monitors(monitor_factories):
    '''
    Take a list of monitor factories and return an active and a passive
    monitor (or None, if none given).
    '''
    stack, value = MultipleStackMonitors(), MultipleValueMonitors()
    monitor_factories = [] if monitor_factories is None else monitor_factories
    for monitor_factory in monitor_factories:
        monitor = monitor_factory()
        if isinstance(monitor, StackMonitor):
            stack.append(monitor)
        if isinstance(monitor, ValueMonitor):
            value.append(monitor)
    return (stack if stack else None, value if value else None)
