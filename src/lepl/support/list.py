
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
Support for S-expression ASTs using subclasses of Python's list class.

The general support works with any nested iterables (except strings).
'''

from functools import reduce

from lepl.support.lib import format, basestring
from lepl.support.node import Node


class List(list):
    '''
    Extend a list for use in ASTs.
    
    Note that the argument is treated in exactly the same way as list().  That
    means it takes a single list or generator as an argument, so to use
    literally you might type List([1,2,3]) - note the "extra" list.
    '''
    
    def __repr__(self):
        return self.__class__.__name__ + '(...)'
    
    def __str__(self):
        return sexpr_to_tree(self)
    

def clone_iterable(type_, items):
    '''
    Clone a class that wraps data in an AST.
    '''
    if issubclass(type_, Node):
        return type_(*list(items))
    else:
        return type_(items)
    

def sexpr_fold(per_list=None, per_item=None, 
               exclude=lambda x: isinstance(x, basestring)):
    '''
    We need some kind of fold-like procedure for generalising operations on
    arbitrarily nested iterables.  We can't use a normal fold because Python
    doesn't have the equivalent of cons, etc; this tries to be more Pythonic
    (see comments later).
    
    We divide everything into iterables ("lists") and atomic values ("items").
    per_list is called with a generator over the (transformed) top-most list, 
    in order.  Items (ie atomic values) in that list, when requested from the 
    generator, will be processed by per_item; iterables will be processed by a 
    separate call to per_list (ie recursively).
    
    So this is more like a recursive map than a fold, but with Python's 
    mutable state and lack of typing it appears to be equally powerful.
    Note that per_list is passed the previous type, which can be used for
    dispatching operations.
    '''
    if per_list is None:
        per_list = clone_iterable
    if per_item is None:
        per_item = lambda x: x
    def items(iterable):
        for item in iterable:
            try:
                if not exclude(item):
                    yield per_list(type(item), items(iter(item)))
                    continue
            except TypeError:
                pass
            yield per_item(item)
    return lambda list_: per_list(type(list_), items(list_))


clone_sexpr = sexpr_fold()
'''
Clone a set of listed iterables.
'''

count_sexpr = sexpr_fold(per_list=lambda type_, items: sum(items), 
                         per_item=lambda item: 1)
'''
Count the number of value nodes in an AST.

(Note that size(List) gives the number of entries in that list, counting each
sublist as "1", while this descends embedded lists, counting their non-iterable
contents.  
'''

join = lambda items: reduce(lambda x, y: x+y, items, [])
'''
Flatten a list of lists by one level, so [[1],[2, [3]]] becomes [1,2,[3]].

Note: this will *only* work correctly if all entries are lists.
'''

sexpr_flatten = sexpr_fold(per_list=lambda type_, items: join(items),
                           per_item=lambda item: [item])
'''
Flatten a list completely, so [[1],[2, [3]]] becomes [1,2,3]
'''

_FORMAT={}
_FORMAT[list] = '[{1}]'
_FORMAT[tuple] = '({1})'

sexpr_to_str = sexpr_fold(per_list=lambda type_, items: 
                            format(_FORMAT.get(type_, '{0}([{1}])'),
                                    type_.__name__, ','.join(items)), 
                          per_item=lambda item: repr(item))
'''
A flat representation of nested lists (a set of constructors).
'''

def sexpr_to_tree(list_):
    '''
    Generate a tree using the same "trick" as `GraphStr`.
    
    The initial fold returns a function (str, str) -> list(str) at each
    level.
    '''
    def per_item(item):
        def fun(first, _rest):
            return [first + repr(item)]
        return fun
    def per_list(type_, list_):
        def fun(first, rest):
            yield [first + str(type_.__name__)]
            force = list(list_) # need to access last item explicitly
            for item in force[:-1]:
                yield item(rest + ' +- ', rest + ' |  ')
            yield force[-1](rest + ' `- ', rest + '    ')
        return lambda first, rest: join(list(fun(first, rest)))
    fold = sexpr_fold(per_list, per_item)
    return '\n'.join(fold(list_)('', ''))


def sexpr_throw(node):
    '''
    Raise an error, if one exists in the results (AST trees are traversed).
    Otherwise, the results are returned (invoke with ``>>``).
    '''
    def throw_or_copy(type_, items):
        clone = clone_iterable(type_, items)
        if isinstance(clone, Exception):
            raise clone
        else:
            return clone
    return sexpr_fold(per_list=throw_or_copy)(node)
