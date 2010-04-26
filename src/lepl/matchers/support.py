
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
Support classes for matchers.
'''

from inspect import getargspec

from lepl.core.config import ParserMixin
from lepl.core.parser import GeneratorWrapper, tagged
from lepl.support.graph import ArgAsAttributeMixin, PostorderWalkerMixin, \
    GraphStr
from lepl.matchers.matcher import Matcher, FactoryMatcher, add_child, is_child
from lepl.matchers.operators import OperatorMixin, OPERATORS, \
    OperatorNamespace
from lepl.support.lib import LogMixin, basestring, format, document, identity

# pylint: disable-msg=C0103,W0212
# (consistent interfaces)
# pylint: disable-msg=E1101
# (_args create attributes)
# pylint: disable-msg=R0901, R0904, W0142
# lepl conventions


class BaseMatcher(ArgAsAttributeMixin, PostorderWalkerMixin, 
                    LogMixin, Matcher):
    '''
    A base class that provides support to all matchers.
    '''
    
    def __repr__(self):
        return self._indented_repr(0, set())
                      
    def _fmt_repr(self, indent, value, visited, key=None):
        prefix = (' ' * indent) + (key + '=' if key else '')
        if is_child(value, Matcher, fail=False):
            if value in visited:
                return prefix + '[' + value._small_str + ']'
            else:
                return value._indented_repr(indent, visited, key)
        else:
            return prefix + repr(value)
        
    def _format_repr(self, indent, key, contents):
        return format('{0}{1}{2}({3}{4})', 
                      ' ' * indent,
                      key + '=' if key else '',
                      self._small_str,
                      '' if self._fmt_compact else '\n',
                      ',\n'.join(contents))
        
    def _indented_repr(self, indent0, visited, key=None):
        visited = set(visited) # copy so only block parents
        visited.add(self)
        (args, kargs) = self._constructor_args()
        indent1 = 0 if self._fmt_compact else indent0 + 1 
        contents = [self._fmt_repr(indent1, arg, visited) for arg in args] + \
            [self._fmt_repr(indent1, kargs[key], visited, key) for key in kargs]
        return self._format_repr(indent0, key, contents)
        
    @property
    def _fmt_compact(self):
        (args, kargs) = self._constructor_args()
        if len(args) + len(kargs) > 1:
            return False
        for arg in args:
            try:
                if not arg._fmt_compact:
                    return False
            except AttributeError:
                pass
        for arg in kargs:
            try:
                if not arg._fmt_compact:
                    return False
            except AttributeError:
                pass
        return True
        
    def _fmt_str(self, value, key=None):
        return (key + '=' if key else '') + \
            value._small_str if isinstance(value, Matcher) else repr(value)
    
    def __str__(self):
        (args, kargs) = self._constructor_args()
        contents = [self._fmt_str(arg) for arg in args] + \
            [self._fmt_str(kargs[key], key) for key in kargs]
        return format('{0}({1})', self._small_str,
                      ', '.join(contents))
    
    @property
    def kargs(self):
        (_, kargs) = self._constructor_args()
        return kargs
    
    def tree(self):
        '''
        An ASCII tree for display.
        '''
        visitor = GraphStr()
        return self.postorder(visitor, Matcher)
    

class OperatorMatcher(OperatorMixin, ParserMixin, BaseMatcher):
    '''
    A base class that provides support to all matchers with operators.
    '''
    
    def __init__(self, name=OPERATORS, namespace=OperatorNamespace):
        super(OperatorMatcher, self).__init__(name=name, namespace=namespace)


class Transformable(OperatorMatcher):
    '''
    All subclasses must expose and apply wrapper, and implement compose.
    
    This allows `Transform` instances to be merged directly.
    '''

    def __init__(self, function=None):
        from lepl.matchers.transform import TransformationWrapper
        super(Transformable, self).__init__()
        if not isinstance(function, TransformationWrapper):
            function = TransformationWrapper(function)
        self.wrapper = function

    def compose(self, wrapper):
        '''
        Combine with a transformation wrapper, returning a new instance.
        
        We must return a new instance because the same Transformable may 
        occur more than once in a graph and we don't want to include the
        transformation in other cases.
        '''
        raise NotImplementedError()

    def _format_repr(self, indent, key, contents):
        return format('{0}{1}{2}:{3}({4}{5})', 
                      ' ' * indent,
                      key + '=' if key else '',
                      self._small_str,
                      self.wrapper,
                      '' if self._fmt_compact else '\n',
                      ',\n'.join(contents))
        

class BaseFactoryMatcher(FactoryMatcher):
    '''
    This must be used as a mixin with something that inherits from 
    ArgsAsAttribute (ie the usual matcher classes).
    '''
    
    def __init__(self, *args, **kargs):
        super(FactoryMatcher, self).__init__()
        self.__args = args
        self.__kargs = kargs
        self.__factory = None
        self.__small_str = None
        self.__cached_matcher = None
        
    def __args_as_attributes(self):
        '''
        Validate the arguments passed to the constructor against the spec for 
        the factory (necessary because we use *args and so the user doesn't
        get the feedback they will expect if they make a mistake).  As a side
        effect we also associated arguments with names and expand defaults
        so that attributes are more predictable.
        '''
        try:
            # function wrapper, so we have two levels, and we must construct
            # a new, empty function
            def empty(): return
            document(empty, self.factory.factory)
            spec = getargspec(empty)
        except:
            spec = getargspec(self.factory)
        names = list(spec.args)
        defaults = dict(zip(names[::-1], spec.defaults[::-1] if spec.defaults else []))
        for name in names:
            if name in self.__kargs:
                self._karg(**{name: self.__kargs[name]})
                del self.__kargs[name]
            elif self.__args:
                self._arg(**{name: self.__args[0]})
                self.__args = self.__args[1:]
            elif name in defaults:
                self._karg(**{name: defaults[name]})
            else:
                raise TypeError(format("No value for argument '{0}' in "
                                       "{1}(...)", 
                                       name, self._small_str))
        if self.__args:
            if spec.varargs:
                self._args(**{spec.varargs: self.__args})
            else:
                raise TypeError(format("No parameter matches the argument "
                                       "{0!r} in {1}(...)", 
                                       self.__args[0], self._small_str))
        if self.__kargs:
            if spec.keywords:
                self.__kargs(**{spec.keywords: self.__kargs})
            else:
                name = list(self.__kargs.keys())[0]
                value = self.__kargs[name]
                raise TypeError(format("No parameter matches the argument "
                                       "{0}={1!r} in {2}(...)", 
                                       name, value, self._small_str))
        
    @property
    def factory(self):
        return self.__factory
    
    @factory.setter
    def factory(self, factory):
        if not self.__factory:
            assert factory
            self.__factory = factory
            self._small_str = self.__small_str if self.__small_str \
                                               else factory.__name__
            self.__args_as_attributes()

    def _format_repr(self, indent, key, contents):
        return format('{0}{1}{2}<{3}>({4}{5})', 
                      ' ' * indent, 
                      key + '=' if key else '',
                      self.__class__.__name__,
                      self._small_str,
                      '' if self._fmt_compact else '\n',
                      ',\n'.join(contents))
        
    @property
    def _cached_matcher(self):
        if not self.__cached_matcher:
            (args, kargs) = self._constructor_args()
            self.__cached_matcher = self.factory(*args, **kargs)
        return self.__cached_matcher
        
        
class TrampolineWrapper(BaseFactoryMatcher, OperatorMatcher):
    '''
    A wrapper for sources of generators that evaluate other matchers via
    the trampoline (ie for generators that evaluate matchers via yield).
    
    Typically only used for advanced matchers.
    '''
    
    @tagged
    def _match(self, stream):
        generator = GeneratorWrapper(self._cached_matcher(self, stream), 
                                     self, stream)
        while True:
            yield (yield generator)
    

class TransformableWrapper(BaseFactoryMatcher, Transformable):
    '''
    Like `TrampolineWrapper`, but transformable.  Used as a common support
    class for various wrappers.
    '''
    
    def compose(self, wrapper):
        (args, kargs) = self._constructor_args()
        copy = type(self)(*args, **kargs)
        copy.factory = self.factory
        copy.wrapper = self.wrapper.compose(wrapper)
        return copy
    
    def _format_repr(self, indent, key, contents):
        return format('{0}{1}{2}<{3}:{4}>({5}{6})', 
                      ' ' * indent, 
                      key + '=' if key else '',
                      self.__class__.__name__,
                      self._small_str,
                      self.wrapper,
                      '' if self._fmt_compact else '\n',
                      ',\n'.join(contents))
        

class TransformableTrampolineWrapper(TransformableWrapper):
    '''
    A wrapper for source of generators that evaluate other matchers via
    the trampoline (ie for generators that evaluate matchers via yield).
    
    Typically only used for advanced matchers.
    '''
    
    @tagged
    def _match(self, stream_in):
        from lepl.matchers.transform import raise_
        function = self.wrapper.function
        generator = GeneratorWrapper(self._cached_matcher(self, stream_in), 
                                     self, stream_in)
        while True:
            try:
                value = yield generator
                yield function(stream_in, lambda: value) \
                    if function else value
            except StopIteration as e:
                if function:
                    yield function(stream_in, lambda: raise_(StopIteration))
                else:
                    raise e
                
    
class NoTrampolineTransformableWrapper(TransformableWrapper):
    '''
    A wrapper for source of generators that do not evaluate other matchers via
    the trampoline.
    
    Subclasses can be used without trampolining via `_untagged_match`.
    '''
    
    #@abstractmethod
    def _untagged_match(self, stream):
        '''
        This should work like `_match()`, but without any tagged wrapper.
        
        It would be nice if both could be generated dynamically, but
        cut + paste appears to be faster, and this is an optimisation. 
        '''


class SequenceWrapper(NoTrampolineTransformableWrapper):
    '''
    A wrapper for simple generator factories, where the final matcher is a
    function that yields a series of matches without evaluating other matchers
    via the trampoline.
    '''
    
    @tagged
    def _match(self, stream_in):
        from lepl.matchers.transform import raise_
        function = self.wrapper.function
        for results in self._cached_matcher(self, stream_in):
            yield function(stream_in, lambda: results) if function else results
        while function:
            yield function(stream_in, lambda: raise_(StopIteration))
 
    def _untagged_match(self, stream_in):
        from lepl.matchers.transform import raise_
        function = self.wrapper.function
        for results in self._cached_matcher(self, stream_in):
            yield function(stream_in, lambda: results) if function else results
        while function:
            yield function(stream_in, lambda: raise_(StopIteration))
 

class FunctionWrapper(NoTrampolineTransformableWrapper):
    '''
    A wrapper for simple function factories, where the final matcher is a
    function that returns a single match or None.
    '''
    
    @tagged
    def _match(self, stream_in):
        from lepl.matchers.transform import raise_
        function = self.wrapper.function
        results = self._cached_matcher(self, stream_in)
        if results is not None:
            yield function(stream_in, lambda: results) \
                if function else results
        while function:
            yield function(stream_in, lambda: raise_(StopIteration))
        
    def _untagged_match(self, stream_in):
        from lepl.matchers.transform import raise_
        function = self.wrapper.function
        results = self._cached_matcher(self, stream_in)
        if results is not None:
            yield function(stream_in, lambda: results) \
                if function else results
        while function:
            yield function(stream_in, lambda: raise_(StopIteration))


def check_matcher(matcher):
    '''
    Check that the signature takes support + stream.
    '''
    check_args(matcher)
    spec = getargspec(matcher)
    if len(spec.args) != 2:
        raise TypeError(format(
'''The function {0} cannot be used as a matcher because it does not have
exactly two parameters.

A typical definition will look like:

def {0}(support, stream):
    ...

where 'support' is a BaseMatcher instance (support for logging, etc) and 
'stream' is a SimpleStream instance (which supports access via stream[i]
and truncation via stream[i:]).''', matcher.__name__))
        
        
def check_args(func):
    '''
    Check that the factory doesn't use any of those modern haifalutin 
    extensions...
    '''
    try:
        getargspec(func)
    except Exception as e:
        raise TypeError(format(
'''The function {0} uses Python 3 style parameters (keyword only, etc).
These are not supported by LEPL factory wrappers currently.  If you really
need this functionality, subclass BaseMatcher.''', func.__name__))
 

def check_modifiers(func, modifiers):
    '''
    Check that any modifiers match the function declaration.
    '''
    argspec = getargspec(func)
    for name in modifiers:
        if name not in argspec.args:
            raise TypeError(
                format("A modifier was specified for argument {'0}' "
                       "in {1}(), but is not declared.", name, func.__name__))
            
            
def apply_modifiers(func, args, kargs, modifiers, margs, mkargs):
    '''
    Modify values in args and kargs.
    '''
    spec = getargspec(func)
    names = list(spec.args)
    defaults = dict(zip(names[::-1], spec.defaults[::-1] if spec.defaults else []))
    newargs = []
    newkargs = {}
    for name in names:
        if name in kargs:
            value = kargs[name]
            if name in modifiers:
                value = modifiers[name](value)
            newkargs[name] = value
            del kargs[name]
        elif args:
            (value, args) = (args[0], args[1:])
            if name in modifiers:
                value = modifiers[name](value)
            newargs.append(value)
        elif name in defaults:
            value = defaults[name]
            if name in modifiers:
                value = modifiers[name](value)
            newkargs[name] = value
        else:
            raise TypeError(format("No value for argument '{0}' in "
                                   "{1}(...)", name, func.__name__))
    # copy across varags
    if spec.varargs:
        newargs.extend(map(margs, args))
    elif args:
        raise TypeError(format("Unexpected argument {0!r} for {1}(...)", 
                               args[0], func.__name__))
    if spec.keywords:
        for name in kargs:
            newkargs[name] = mkargs(kargs[name])
    elif kargs:
        for name in kargs:
            raise TypeError(format("Unexpected argument {0}={1!r} for {2}(...)", 
                                   name, kargs[name], func.__name__))
    return (newargs, newkargs)
                

def make_wrapper_factory(wrapper, factory, modifiers, 
                         margs=identity, mkargs=identity, memo=True):
    '''
    A helper function that assembles a matcher from a wrapper class and 
    a factory function that contains the logic.
    
    `wrapper` is the class that will be constructed, and which will contain
    the functionality defined in `factory`.
    
    `modifiers` is a map of functions applied to arguments of the given name.
    Similarly, `margs` and `mkargs` apply to varargs.
    
    `memo` should be set to False for matchers that do not want memoisation.
    '''
    from lepl.matchers.memo import NoMemo
    check_args(factory)
    check_modifiers(factory, modifiers)
    def wrapper_factory(*args, **kargs):
        (args, kargs) = \
            apply_modifiers(factory, args, kargs, modifiers, margs, mkargs)
        made = wrapper(*args, **kargs)
        made.factory = factory
        return made
    wrapper_factory.factory = factory
    add_child(Matcher, wrapper_factory)
    if not memo:
        add_child(NoMemo, wrapper_factory)
    return wrapper_factory


def make_factory(maker, matcher):
    '''
    A helper function that assembles a matcher from a wrapper class and 
    a function that contains the logic.
    
    This works by generating a dummy factory and delegating to 
    `make_wrapper_factory`.
    '''
    def factory(*args, **kargs):
        if args or kargs:
            raise TypeError(format('{0}() takes no arguments', 
                                   matcher.__name__))
        return matcher
    document(factory, matcher)
    factory.factory = matcher
    return maker(factory)


def trampoline_matcher_factory(transformable_=True, 
                               args_=identity, kargs_=identity, **kargs):
    '''
    Decorator that allows matchers to be defined using a nested pair
    of functions.  The outer function acts like a constructor; the inner
    function implements the matcher logic.
    
    The matcher code can evaluate sub-matchers by yielding the generator
    created by `matcher._match()` to the trampoline.  Matches should also
    be yielded. 
    
    `transformable_` indicates whether the final matcher should be a subclass
    of `Transformable`.
    
    Other keyword arguments should match factory arguments and identify 
    functions of one argument that are applied to the arguments when the
    matcher is created as part of a grammar (eg coercion).  Similarly,
   `args_` and `kargs_` are applied to varargs.
    '''
    if not isinstance(transformable_, bool):
        raise ValueError(
            'trampoline_matcher_factory must be used as a function:'
            '\n  @trampoline_matcher_factory(transformable=True)'
            '\n  def MyMatcherFactory(...):'
            '\n      ....')
    def wrapper(factory):
        if transformable_:
            return make_wrapper_factory(TransformableTrampolineWrapper, 
                                        factory, kargs, args_, kargs_)
        else:
            return make_wrapper_factory(TrampolineWrapper, factory, kargs)
    return wrapper

def trampoline_matcher(transformable=True):
    '''
    Decorator that allows matchers to be defined using a single function 
    to implement the matcher logic.
    
    The matcher code can evaluate sub-matchers by yielding the generator
    created by `matcher._match()` to the trampoline.  Matches should also
    be yielded. 
    '''
    if not isinstance(transformable, bool):
        raise ValueError(
            'trampoline_matcher must be used as a function:'
            '\n  @trampoline_matcher()'
            '\n  def MyMatcherFactory(...):'
            '\n      ....')
    def wrapper(matcher):
        check_matcher(matcher)
        return make_factory(trampoline_matcher_factory(transformable), matcher)
    return wrapper

def sequence_matcher_factory(gatekeeper_=None, 
                               args_=identity, kargs_=identity, **kargs):
    '''
    Decorator that allows matchers to be defined using a nested pair
    of functions.  The outer function acts like a constructor; the inner
    function implements the matcher logic.
    
    The matcher must yield matches (multiple times if required).  It 
    *cannot* evaluate sub-matchers.
    
    `args_`, `kargs_` and named arguments define modifiers, which are applied
    to the corresponding arguments when the matcher is first used in a grammar
    (eg to coerce strings to `Literal` instances).
    '''
    if gatekeeper_:
        raise ValueError(
            'sequence_matcher_factory must be used as a function:'
            '\n  @sequence_matcher_factory()'
            '\n  def MyMatcherFactory(...):'
            '\n      ....')
    def wrapper(factory):
        return make_wrapper_factory(SequenceWrapper, factory, 
                                    kargs, args_, kargs_, memo=False)
    return wrapper

def sequence_matcher(matcher):
    '''
    Decorator that allows matchers to be defined using a single function 
    to implement the matcher logic.
    
    The matcher must yield matches (multiple times if required).  It 
    *cannot* evaluate sub-matchers.
    '''
    check_matcher(matcher)
    return make_factory(sequence_matcher_factory(), matcher)

def function_matcher_factory(gatekeeper_=None,
                             args_=identity, kargs_=identity, **kargs):
    '''
    Decorator that allows matchers to be defined using a nested pair
    of functions.  The outer function acts like a constructor; the inner
    function implements the matcher logic.
    
    The matcher must return a single match.  It *cannot* evaluate sub-matchers.
    
    `args_`, `kargs_` and named arguments define modifiers, which are applied
    to the corresponding arguments when the matcher is first used in a grammar
    (eg to coerce strings to `Literal` instances).
    '''
    if gatekeeper_:
        raise ValueError(
            'function_matcher_factory must be used as a function:'
            '\n  @function_matcher_factory()'
            '\n  def MyMatcherFactory(...):'
            '\n      ....')
    def wrapper(factory):
        return make_wrapper_factory(FunctionWrapper, factory, 
                                    kargs, args_, kargs_, memo=False)
    return wrapper

def function_matcher(matcher):
    '''
    Decorator that allows matchers to be defined using a single function 
    to implement the matcher logic.
    
    The matcher must return a single match.  It *cannot* evaluate sub-matchers.
    '''
    check_matcher(matcher)
    return make_factory(function_matcher_factory(), matcher)


def coerce_(arg, function=None):
    '''
    Many arguments can take a string which is implicitly converted (via this
    function) to a literal (or similar).
    '''
    if function is None:
        from lepl.matchers.core import Literal
        function = Literal
    return function(arg) if isinstance(arg, basestring) else arg


def to(function):
    '''
    Generate a coercion for later application.
    '''
    return lambda matcher: coerce_(matcher, function)
