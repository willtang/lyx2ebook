
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
Tests for the lepl package.
'''

from logging import getLogger, basicConfig, DEBUG
from sys import version
from types import ModuleType
from unittest import TestSuite, TestLoader, TextTestRunner

import lepl

# we need to import all files used in the automated self-test

# pylint: disable-msg=E0611, W0401
#@PydevCodeAnalysisIgnore
import lepl._test.bug_stalled_parser
import lepl._test.magus

# Number of tests if running in IDE with Python 3,
TOTAL = 394

def all():
    '''
    This runs all tests and examples.  It is something of a compromise - seems
    to be the best solution that's independent of other libraries, doesn't
    use the file system (since code may be in a zip file), and keeps the
    number of required imports to a minimum.
    '''
    #basicConfig(level=DEBUG)
    log = getLogger('lepl._test.all.all')
    suite = TestSuite()
    loader = TestLoader()
    runner = TextTestRunner(verbosity=2)
    for module in ls_all_tests():
        log.debug(module.__name__)
        suite.addTest(loader.loadTestsFromModule(module))
    result = runner.run(suite)
    print('\n\n\n----------------------------------------------------------'
          '------------\n')
    if version[0] == '2':
        print('Expect 4-5 failures + 1 error in Python 2.6: {0:d}, {1:d} '
              '(lenient comparison, format variation from address size, '
              'unicode ranges, weird string difference)'
              .format(len(result.failures), len(result.errors)))
        assert 4 <= len(result.failures) <= 5, len(result.failures)
        assert 1 <= len(result.errors) <= 1, len(result.errors)
        target = TOTAL - 22 - 9 # no bin/cairo tests (22)
    else:
        print('Expect at most 1 failure + 0 errors in Python 3: {0:d}, {1:d} '
              '(format variations from address size?)'
              .format(len(result.failures), len(result.errors)))
        assert 0 <= len(result.failures) <= 1, len(result.failures)
        assert 0 <= len(result.errors) <= 0, len(result.errors)
        target = TOTAL - 9 # no cairo tests (2), no random (1), no support[3] (6)
    print('Expect {0:d} tests total: {1:d}'.format(target, result.testsRun))
    assert result.testsRun == target, result.testsRun
    print('\nLooks OK to me!\n\n')


def ls_all_tests():
    '''
    All test modules.
    '''
    for root in ls_module(lepl, 
                          ['bin', 'contrib', 'core', 'lexer', 'matchers', 
                           'offside', 'regexp', 'stream', 'support'], 
                          True):
        for child in ls_module(root, ['_test', '_example']):
            for module in ls_module(child):
                yield module


def ls_module(parent, children=None, include_parent=False):
    '''
    Expand and return child modules.
    '''
    if include_parent:
        yield parent
    if not children:
        children = dir(parent)
    for child in children:
        try:
            # pylint: disable-msg=W0122
            exec('import {0}.{1}'.format(parent.__name__, child))
            module = getattr(parent, child, None)
            if isinstance(module, ModuleType):
                yield module
        except ImportError:
            pass


if __name__ == '__main__':
    all()
