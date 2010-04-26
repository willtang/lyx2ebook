
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103,W0621,R0903
# (the code style is for documentation, not "real")
#@PydevCodeAnalysisIgnore

'''
Examples from the documentation.
'''

from logging import basicConfig, DEBUG

from gc import collect
from random import random
from timeit import timeit

from lepl import *
from lepl._example.support import Example
from lepl.support.lib import format

NUMBER = 10
REPEAT = 3

def default():
    '''A simple parser we'll use as an example.'''
    
    class Term(List): pass
    class Factor(List): pass
    class Expression(List): pass
        
    expr   = Delayed()
    number = Float()                                >> float
    
    with DroppedSpace():
        term    = number | '(' & expr & ')'         > Term
        muldiv  = Any('*/')
        factor  = term & (muldiv & term)[:]         > Factor
        addsub  = Any('+-')
        expr   += factor & (addsub & factor)[:]     > Expression
        line    = expr & Eos()
    
    return line


# These create a matcher for the parser above with different configurations

def clear():
    matcher = default()
    matcher.config.clear()
    return matcher

def no_memo():
    matcher = default()
    matcher.config.no_memoize()
    return matcher

def full_memo():
    matcher = default()
    matcher.config.auto_memoize(full=True)
    return matcher

def slow(): 
    matcher = default()
    matcher.config.clear().trace().manage().auto_memoize(full=True)
    return matcher

def nfa_regexp(): 
    matcher = default()
    matcher.config.clear().compile_to_nfa(force=True)
    return matcher

def dfa_regexp(): 
    matcher = default()
    matcher.config.clear().compile_to_dfa(force=True)
    return matcher


# Next, build all the tests, making sure that we pre-compile parsers where
# necessary and (important!) we avoid reusing a parser with a cache

data = [format('{0:4.2f} + {1:4.2f} * ({2:4.2f} + {3:4.2f} - {4:4.2f})',
               random(), random(), random(), random(), random())
        for i in range(NUMBER)]

matchers = [default, clear, no_memo, full_memo, slow, nfa_regexp, dfa_regexp]

def build_cached(factory):
    matcher = factory()
    matcher.config.clear_cache()
    parser = matcher.get_parse()
    def test():
        for line in data:
            parser(line)[0]
    return test
            
def build_uncached(factory):
    matcher = factory()
    def test():
        for line in data:
            matcher.config.clear_cache()
            matcher.parse(line)[0]
    return test

tests = {}

for matcher in matchers:
    tests[matcher] = {True: [], False: []}
    for i in range(REPEAT):
         tests[matcher][True].append(build_cached(matcher))
         tests[matcher][False].append(build_uncached(matcher))


def run(matcher, cached, repeat):
    '''Time the given test.'''
    stmt = 'tests[{0}][{1}][{2}]()'.format(matcher.__name__, cached, repeat)
    setup = 'from __main__ import tests, {0}'.format(matcher.__name__)
    return timeit(stmt, setup, number=1)

def analyse(matcher, t_uncached_base=None, t_cached_base=None):
    '''We do our own repeating so we can GC between attempts.'''
    (t_uncached, t_cached) = ([], [])
    for repeat in range(REPEAT):
        collect()
        t_uncached.append(run(matcher, False, repeat))
        collect()
        t_cached.append(run(matcher, True, repeat))
    (t_uncached, t_cached) = (min(t_uncached), min(t_cached))
    t_uncached = 1000.0 * t_uncached / NUMBER
    t_cached = 1000.0 * t_cached / NUMBER 
    print(format('{0:>20s} {1:5.1f} {2:8s}  {3:5.1f} {4:8s}',
                 matcher.__name__, 
                 t_uncached, normalize(t_uncached, t_uncached_base), 
                 t_cached, normalize(t_cached, t_cached_base)))
    return (t_uncached, t_cached)

def normalize(time, base):
    if base:
        return '(x{0:5.2f})'.format(time / base)
    else:
        return ''

def main():
    print('{0:d} iterations; time per iteration in ms (best of {1:d})\n'.format(
            NUMBER, REPEAT))
    print(format('{0:>35s}    {1:s}', 're-compiled', 'cached'))
    (t_uncached, t_cached) = analyse(default)
    for matcher in matchers:
        if matcher is not default:
            analyse(matcher, t_uncached, t_cached)

if __name__ == '__main__':
    main()

# pylint: disable-msg=E0601
# (pylint parsing bug?)        
class PerformanceExample(Example):
    
    def test_parse(self):
    
        # run this to make sure nothing changes
        parsers = [default, clear, no_memo, full_memo, slow]
        examples = [(lambda: parser().parse('1.23e4 + 2.34e5 * (3.45e6 + 4.56e7 - 5.67e8)')[0],
"""Expression
 +- Factor
 |   `- Term
 |       `- 12300.0
 +- '+'
 `- Factor
     +- Term
     |   `- 234000.0
     +- '*'
     `- Term
         +- '('
         +- Expression
         |   +- Factor
         |   |   `- Term
         |   |       `- 3450000.0
         |   +- '+'
         |   +- Factor
         |   |   `- Term
         |   |       `- 45600000.0
         |   +- '-'
         |   `- Factor
         |       `- Term
         |           `- 567000000.0
         `- ')'""") for parser in parsers]
        self.examples(examples)
        
#    def test_cached(self):
#        matcher = full_memo()
#        print(matcher._raw_parser().matcher.tree())
#        matcher = default()
#        print(matcher._raw_parser().matcher.tree())
##        for line in data:
##            print(matcher.parse(line)[0])
            