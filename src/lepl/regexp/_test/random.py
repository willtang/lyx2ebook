
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
Tests for the lepl.regexp package.  We generate random expressions and
test the results against the python regexp matcher.
'''

#from logging import basicConfig, DEBUG, getLogger
from random import randint, choice
from re import compile as compile_
from sys import exc_info
from unittest import TestCase

from lepl.regexp.matchers import DfaRegexp
from lepl.support.lib import format

def randbool(weight=1):
    return choice([True] * weight + [False])

def random_expression(depth_left, alphabet):
    '''
    Generate an expression.  If depth_left is 0 then the result must be
    a simple character; other levels build on this.  Alphabet is a list of
    possible regular characters.
    '''
    if depth_left:
        return choice([random_sequence,
                       random_option,
                       random_repeat,
                       random_choice,
                       random_range,
                       random_expression])(depth_left-1, alphabet)
    else:
        return choice(alphabet + '.')

def random_sequence(depth_left, alphabet):
    return ''.join(random_expression(depth_left, alphabet)
                   for _ in range(randint(1, 3)))

def random_option(depth_left, alphabet):
    subexpr = random_expression(depth_left, alphabet)
    if len(subexpr) > 1:
        return format('({0})?', subexpr)
    else:
        return subexpr + '?'

def random_repeat(depth_left, alphabet):
    subexpr = random_expression(depth_left, alphabet)
    if len(subexpr) > 1:
        return format('({0})*', subexpr)
    else:
        return subexpr + '*'

def random_choice(depth_left, alphabet):
    return format('({0})', '|'.join(random_expression(depth_left, alphabet)
                                    for _ in range(randint(1, 3))))

def random_range(_depth_left, alphabet):
    def random_chars():
        subexpr = ''
        for _ in range(randint(1, 2)):
            if randbool():
                subexpr += choice(alphabet)
            else:
                a, b = choice(alphabet), choice(alphabet)
                if a > b:
                    a, b = b, a
                subexpr += format('{0}-{1}', a, b)
        return subexpr
    def random_content():
        if randbool(len(alphabet)):
            return random_content()
        else:
            return '.'
    # cannot use random_content below with current lepl regexp
    if randbool():
        return format('[{0}]', random_chars())
    else:
        return format('[^{0}]', random_chars())

def random_string(depth_left, alphabet):
    if depth_left:
        return choice(alphabet) + random_string(depth_left-1, alphabet)
    else:
        return ''

class RandomTest(TestCase):
    
    def test_random(self):
        '''
        Compares lepl + python expressions.  This runs 'til it fails, and it
        always does fail, because lepl's expressions are guarenteed greedy
        while python's aren't.  This is "normal" (Perl is the same as Python)
        but I cannot fathom why it should be - it seems *harder* to make them
        wwork that way... 
        '''
        #basicConfig(level=DEBUG)
        #log = getLogger('lepl.reexgp._test.random')
        match_alphabet = '012'
        string_alphabet = '013'
        for _ in range(100):
            expression = random_expression(3, match_alphabet) 
            string = random_string(3, string_alphabet)
            matcher = DfaRegexp(expression)
            matcher.config.no_full_first_match()
            lepl_result = matcher.parse(string)
            if lepl_result:
                lepl_result = lepl_result[0]
            #log.debug(format('{0} {1} {2}', expression, string, lepl_result))
            try:
                python_result = compile_(expression).match(string) 
                if python_result:
                    python_result = python_result.group()
                assert lepl_result == python_result, \
                    format('{0} != {1}\n{2} {3}', 
                           lepl_result, python_result, expression, string)
            except:
                (e, v, _t) = exc_info()
                if repr(v) == "error('nothing to repeat',)":
                    pass
                else:
                    raise e
                