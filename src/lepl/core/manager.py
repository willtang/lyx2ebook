
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
Manage resources.

We can attempt to control resource consumption by closing generators - the
problem is which generators to close?

At first it seems that the answer is going to be connected to tree traversal,
but after some thought it's not so clear exactly what tree is being traversed,
and how that identifies what generators should be closed.  In particular, an 
"imperative" implementation with generators does not have the same meaning of 
"depth" as a recursive functional implementation (but see the related 
discussion in the `manual <../advanced.html#search-and-backtracking>`_).

A better approach seems to be to discard those that have not been used "for a
long time".  A variation on this - keep a maximum number of the youngest 
generators - is practical.  But care is needed to both in identifying what is 
used, and when it starts being unused, and in implementing that efficiently.

Here all generators are stored in a priority queue using weak references.  The 
"real" priority is given by the "last used date" (epoch), but the priority in 
the queue is frozen when inserted.  So on removing from the queue the priority 
must be checked to ensure it has not changed (and, if so, it must be updated
with the real value and replaced).

Note that the main aim here is to restrict resource consumption without 
damaging performance too much.  The aim is not to control parse results by 
excluding certain matches.  For efficiency, the queue length is increased 
(doubled) whenever the queue is filled by active generators.

For the control of parse results see the `Commit()` matcher.
'''

from heapq import heappushpop, heappop, heappush
from weakref import ref, WeakKeyDictionary

from lepl.core.monitor import StackMonitor, ValueMonitor
from lepl.support.lib import LogMixin, format, str


# pylint: disable-msg=C0103
def GeneratorManager(queue_len):
    '''
    A 'Monitor' (implements `MonitorInterface`, can be supplied
    to `Configuration`) that tracks (and can limit the number of)
    generators.

    This is a helper function that "escapes" the main class via a function
    to simplify configuration.
    '''
    return lambda: _GeneratorManager(queue_len)


class _GeneratorManager(StackMonitor, ValueMonitor, LogMixin):
    '''
    A 'Monitor' (implements `MonitorInterface`, can be supplied
    to `Configuration`) that tracks (and can limit the number of)
    generators.
    '''
    
    def __init__(self, queue_len):
        '''
        `queue_len` is the number of generators that can exist.  When the
        number is exceeded the oldest generators are closed, unless currently
        active (in which case the queue size is extended).  If zero then no
        limit is applied (although generators are still tracked and can be
        removed using `Commit()`.
        '''
        super(_GeneratorManager, self).__init__()
        self.__queue = []
        self.__queue_len = queue_len
        self.__known = WeakKeyDictionary() # map from generator to ref
        self.epoch = 0
        
    def next_iteration(self, epoch, value, exception, stack):
        '''
        Store the current epoch.
        '''
        self.epoch = epoch
        
    def push(self, generator):
        '''
        Add a generator if it is not already known, or increment it's ref count.
        '''
        if generator not in self.__known:
            self.__add(generator)
        else:
            self.__known[generator].push()
            
    def pop(self, generator):
        '''
        Decrement a ref's count and update the epoch.
        '''
        self.__known[generator].pop(self.epoch)
            
    def __add(self, generator):
        '''
        Add a generator, trying to keep the number of active generators to
        that given in the constructor.
        '''
        reference = GeneratorRef(generator, self.epoch)
        self.__known[generator] = reference
        self._debug(format('Queue size: {0}/{1}',
                           len(self.__queue), self.__queue_len))
        # if we have space, simply save with no expiry
        if self.__queue_len == 0 or len(self.__queue) < self.__queue_len:
            self.__add_unlimited(reference)
        else:
            self.__add_limited(reference)
            
    def __add_unlimited(self, reference):
        '''
        Add the new reference and discard any GCed candidates that happen
        to be on the top of the heap.
        '''
        self._debug(format('Free space, so add {0}', reference))
        candidate = heappushpop(self.__queue, reference)
        while candidate:
            candidate.deletable(self.epoch)
            if candidate.gced:
                candidate = heappop(self.__queue)
            else:
                heappush(self.__queue, candidate)
                break
            
    def __add_limited(self, reference):
        '''
        Add the new reference, discarding an old entry if possible.
        '''
        while reference:
            candidate = heappushpop(self.__queue, reference)
            self._debug(format('Exchanged {0} for {1}', reference, candidate))
            if candidate.order_epoch == self.epoch:
                # even the oldest generator is current
                break
            elif candidate.deletable(self.epoch):
                self._debug(format('Closing {0}', candidate))
                candidate.close()
                return
            else:
                # try again (candidate has been updated)
                reference = candidate
        # if we are here, queue is too small
        heappush(self.__queue, candidate)
        # this is currently 1 too small, and zero means unlimited, so
        # doubling should always be sufficient.
        self.__queue_len = self.__queue_len * 2
        self._warn(format('Queue is too small - extending to {0}',
                          self.__queue_len))
            
    def commit(self):
        '''
        Delete all non-active generators.
        '''
        if self.__queue:
            for _retry in range(len(self.__queue)):
                reference = heappop(self.__queue)
                if reference.active():
                    reference.update(self.epoch) # forces epoch update
                    heappush(self.__queue, reference)
                else:
                    reference.close()
            

class GeneratorRef(object):
    '''
    This contains the weak reference to the GeneratorWrapper and is stored
    in the GC priority queue.
    '''
    
    def __init__(self, generator, epoch):
        self.__hash = hash(generator)
        self.__wrapper = ref(generator)
        self.__last_known_epoch = epoch
        self.order_epoch = epoch # readable externally
        self.__count = 1 # add with 1 as we test for discard immediately after
        self.gced = False
        self.__describe = str(generator)
        
    def __lt__(self, other):
        assert isinstance(other, GeneratorRef)
        return self.order_epoch < other.order_epoch
    
    def __eq__(self, other):
        return self is other
    
    def __hash__(self):
        return self.__hash
    
    def pop(self, epoch):
        '''
        When no longer used, safe epoch and decrement count.
        '''
        self.__last_known_epoch = epoch
        self.__count -= 1
        
    def push(self):
        '''
        Added to stack, so increment count.
        '''
        self.__count += 1
        
    def reusable(self, generator):
        '''
        Check we can re-use the wrapper.
        '''
        wrapped = self.__wrapper()
        if not wrapped:
            assert self.__count == 0, \
                format('GCed but still on stack?! {0}', self.__describe)
            return False
        else:
            assert wrapped is generator, \
                format('Hash collision? {0}/{1}', generator, wrapped)
            return True
    
    def deletable(self, epoch):
        '''
        Check we can delete the wrapper.
        '''
        if not self.__wrapper():
            assert self.__count == 0, \
                format('GCed but still on stack?! {0}', self.__describe)
            # already disposed by system
            self.gced = True
            return True
        else:
            # not on stack and ordering in queue was correct
            if self.__count == 0 \
                    and self.order_epoch == self.__last_known_epoch:
                return True
            # still on stack, or ordering was incorrect
            else:
                if self.__count:
                    self.__last_known_epoch = epoch
                self.order_epoch = self.__last_known_epoch
                return False
            
    def close(self):
        '''
        This terminates the enclosed generator.
        '''
        generator = self.__wrapper()
        if generator:
            generator.generator.close()
            
    def __str__(self):
        generator = self.__wrapper()
        if generator:
            return format('{0} ({1:d}/{2:d})',
                          self.__describe, self.order_epoch, 
                          self.__last_known_epoch)
        else:
            return format('Empty ref to {0}', self.__describe)
    
    def __repr__(self):
        return str(self)
