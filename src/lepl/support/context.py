
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
Allow global per-thread values to be defined within a certain scope in a
way that supports multiple values, temporary changes inside with contexts,
etc.

This is implemented in two layers.  The base layer is a map from keys
to values which isolates different, broad, functionalities.  Despite the name,
a NamespaceMap can map from any key to any value - it's just a thread-local
map.  However, typically is it used with Namespaces because they have support
for some useful idioms.

A Namespace is, as described above, associated with a name in the thread's
NamespaceMap.  It manages state for some functionality, so is another map,
forming the second layer.  The motivating example of a Namespace is the
OperatorNamespace, which maps from operators to matchers.  This uses the
support in Namespace that allows values to be over-ridden within a certain
scope to support overriding matchers for matching spaces.
'''

from collections import deque
#from logging import getLogger
from threading import local

from lepl.support.lib import singleton, format


class ContextError(Exception):
    '''
    Exception raised on problems with context.
    '''
    pass


# pylint: disable-msg=R0903
class NamespaceMap(local):
    '''
    A store for namespaces.
    
    This subclasses threading.local so each thread effectively has its own 
    instance (see test).
    '''
    
    def __init__(self):
        super(NamespaceMap, self).__init__()
        self.__map = {}
        
    def get(self, name, default=None):
        '''
        This gets the namespace associated with the name, creating a new
        namespace from the second argument if necessary.
        '''
        from lepl.matchers.operators import OperatorNamespace
        if default is None:
            default = OperatorNamespace
        if name not in self.__map:
            self.__map[name] = default() 
        return self.__map[name] 


class Namespace(object):
    '''
    A store for global definitions.
    '''
    
    def __init__(self, base=None):
        self.__stack = deque([{} if base is None else base])
        
    def push(self, extra=None):
        '''
        Copy the current state to the stack and modify it.  Values in extra
        that map to None are ignored.
        '''
        self.__stack.append(dict(self.current()))
        extra = {} if extra is None else extra
        for name in extra:
            self.set_if_not_none(name, extra[name])
        
    def pop(self):
        '''
        Return the previous state from the stack.
        '''
        self.__stack.pop()
        
    def __enter__(self):
        '''
        Allow use within a with context by duplicating the current state
        and saving to the stack.  Returns self to allow manipulation via set.
        '''
        self.push()
        return self
       
    def __exit__(self, *_args):
        '''
        Restore the previous state from the stack on leaving the context.
        '''
        self.pop()
        
    def current(self):
        '''
        The current state (a map from names to operator implementations).
        '''
        return self.__stack[-1]
    
    def set(self, name, value):
        '''
        Set a value.
        '''
        self.current()[name] = value
        
    def set_if_not_none(self, name, value):
        '''
        Set a value if it is not None.
        '''
        if value != None:
            self.set(name, value)
            
    def get(self, name, default):
        '''
        Get a value if defined, else the default.
        '''
        return self.current().get(name, default)
    
    
class OnceOnlyNamespace(Namespace):
    '''
    Allow some values to be set only once.
    '''
    
    def __init__(self, base=None, once_only=None):
        super(OnceOnlyNamespace, self).__init__(base)
        self.__once_only = set() if once_only is None else once_only
        
    def once_only(self, name):
        '''
        The given name can be set only once.
        '''
        self.__once_only.add(name)
        
    def set(self, name, value):
        '''
        Set a value (if it has not already been set).
        '''
        if name in self.__once_only and self.get(name, None) is not None:
            raise ContextError(format('{0} can only be set once', name))
        else:
            super(OnceOnlyNamespace, self).set(name, value)
        

# pylint: disable-msg=C0103, W0603
def Global(name, default=None):
    '''
    Global (per-thread) binding from operator name to implementation, by
    namespace.
    '''
    # Delay creation to handle circular dependencies.
    assert name
    namespace_map = singleton(NamespaceMap)
    return namespace_map.get(name, default)


class NamespaceMixin(object):
    '''
    Allow access to global (per-thread) values.
    '''

    def __init__(self, name, namespace):
        super(NamespaceMixin, self).__init__()
        self.__name = name
        self.__namespace = namespace
        
    def _lookup(self, name, default=None):
        '''
        Retrieve the named namespace from the global (per thread) store.
        '''
        return Global(self.__name, self.__namespace).get(name, default)


class Scope(object):
    '''
    Base class supporting dedicated syntax for particular options.
    '''

    def __init__(self, name, namespace, frame):
        self.__name = name
        self.__namespace = namespace
        self.__frame = frame
        
    def __enter__(self):
        '''
        On entering the context, add the new definitions.
        '''
        Global(self.__name, self.__namespace).push(self.__frame)
        
    def __exit__(self, *_args):
        '''
        On leaving the context, return to previous definition.
        '''
        Global(self.__name, self.__namespace).pop()


