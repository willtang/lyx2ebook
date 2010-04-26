
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

#@PydevCodeAnalysisIgnore
# pylint: disable-msg=W0401,C0111,W0614,W0622,C0301,C0321,C0324,C0103
# (the code style is for documentation, not "real")

'''
Process a table of data based on values from
http://www.swivel.com/data_sets/spreadsheet/1002196
'''

#from logging import basicConfig, DEBUG

from lepl import *
from lepl._example.support import Example


class ColumnExample(Example):
    
    def test_columns(self):
        #basicConfig(level=DEBUG)
        
        # http://www.swivel.com/data_sets/spreadsheet/1002196
        table = '''
US Foreign Aid, top recipients, constant dollars
Year            Iraq          Israel           Egypt
2005   6,981,200,000   2,684,100,000   1,541,900,000
2004   8,333,400,000   2,782,400,000   2,010,600,000
2003   4,150,000,000   3,878,300,000   1,849,600,000
2002      41,600,000   2,991,200,000   2,362,800,000
'''
        spaces = ~Space()[:]
        integer = (spaces & Digit()[1:, ~Optional(','), ...] & spaces) >> int
        cols = Columns((4,  integer),
                       # if we give widths, they follow on from each other
                       (16, integer),
                       # we can also specify column indices
                       ((23, 36), integer),
                       # and then start with widths again
                       (16, integer))
        # by default, Columns consumes a whole line (see skip argument), so
        # for the whole table we only need to (1) drop the text and (2) put
        # each row in a separate list.
        parser = ~SkipTo(Digit(), include=False) & (cols > list)[:]
        
        # L included below to check that it's ignored in comparison
        # (appears in windows?)
        self.examples([(lambda: parser.parse(table),
                        '[[2005, 6981200000L, 2684100000, 1541900000], ' 
                        '[2004, 8333400000, 2782400000, 2010600000], ' 
                        '[2003, 4150000000, 3878300000, 1849600000], ' 
                        '[2002, 41600000, 2991200000, 2362800000]]')])
        

        
        
        