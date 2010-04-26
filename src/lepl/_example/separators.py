
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

# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103
#@PydevCodeAnalysisIgnore
# (the code style is for documentation, not "real")

'''
This is an example that generates some tables showing how the different
separators handle spaces in a variety of different cases.  The output
format is restructured text, which can be included directly in the 
documentation.
'''

from lepl import *

# columns widths
W_STREAM = 10
W_YES = 14


def _print(*_args, **_kargs):
    '''
    Isolate this for Python 2.6.  We need to exclude this to avoid errors
    on install.
    '''
#    print(*args, **kargs)


def make_table(base, streams, separators_, title, titles_):
    '''
    Generate the entire table, given a base matcher, some streams to test 
    it against, and separators (with titles) that define how spaces will be
    handled.
    
    `base` must be a function that evaluates to give a matcher, so that we
    can define the matcher within the scope of the different separators (and
    add `Eos()` in different ways).
    '''
    assert len(titles_) == len(separators_)
    parsers = build_parsers(base, separators_)
    print()
    print_titles(title, titles_)
    for stream in streams:
        ok = ['yes' if parser.parse(stream) is not None else ''
              for parser in parsers]
        print_columns(repr(stream), 1, 1, ok)
        print_row(True, len(titles_) * 4, 1)
    print()
    
def print_titles(title, titles_):
    '''
    Print titles in the format expected by restructured text.
    '''
    n_titles = len(titles_)
    width = W_STREAM + n_titles * (W_YES+1) * 4
    print('+{0}+'.format('-' * width))
    print('|{0:{1}}|'.format(title, width))
    print_row(True, n_titles, 4)
    print_columns('', 1, 4, titles_)
    print_row(False,  n_titles*2, 2)
    print_columns('', n_titles, 2, ['And(..., Eos())', '... & Eos()'])
    print_row(False,  n_titles*4, 1)
    print_columns('', n_titles*2, 1, ["' '", "' '[:]"])
    print_row(True,  n_titles*4, 1, '=')
    
def print_row(left, count, width, line='-'):
    if left:
        _print('+' + line * W_STREAM, end='')
    else:
        _print('|' + ' ' * W_STREAM, end='')
    for _i in range(count):
        _print('+' + line * (W_YES * width + width - 1) , end='')
    print('+')

def print_columns(left, count, width, titles_):
    _print('|{0:{1}}'.format(left, W_STREAM), end='')
    for _i in range(count):
        for title in titles_:
            _print('|{0:{1}}'.format(title, width * W_YES + width - 1), end='')
    _print('|')
    
def build_parsers(base, separators_):
    '''
    Construct parsers from 'base', with fixed or optional spaces and 'Eos()' 
    connected via 'And()' or '&'.
    '''
    parsers = []
    for separator in separators_:
        with separator(' '):
            parsers.append(And(base(), Eos()))
        with separator(Literal(' ')[:]):
            parsers.append(And(base(), Eos()))
        with separator(' '):
            parsers.append(base() & Eos())
        with separator(Literal(' ')[:]):
            parsers.append(base() & Eos())
    return parsers


if __name__ == '__main__':
    separators =  [Separator, SmartSeparator1, SmartSeparator2]
    titles = ['Separator', 'SmartSeparator1', 'SmartSeparator2']
    make_table(lambda: Optional('a') & Optional('b'), 
               ['a b ', 'a b', 'ab', ' b', 'b', 'a ', 'a', '', ' '],
               separators, "Optional('a') & Optional('b')", titles)
    make_table(lambda: Optional('a') & Optional('b') & 'c', 
               ['a b c ', 'a b c', ' b c', 'b c', 'ab c', 'a c', 'a  c', 'c', ' c'],
               separators, "Optional('a') & Optional('b') & 'c'", titles)
    
    
    