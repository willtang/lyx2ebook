
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
Tests for a bug reported for 3.2, 3.2.1
'''

# pylint: disable-msg=W0614, W0401, C0103, R0201, R0914, R0915
# test
#@PydevCodeAnalysisIgnore


#from logging import basicConfig, DEBUG
from unittest import TestCase

from lepl import *
from lepl.support.graph import ConstructorWalker
from lepl.matchers.matcher import Matcher, canonical_matcher_type,\
    MatcherTypeException, is_child
from lepl.matchers.memo import _LMemo, _RMemo, LMemo, RMemo
from lepl.matchers.transform import Transform, TransformationWrapper
from lepl.core.rewriters import DelayedClone, NodeStats, Flatten, Memoize, \
    ComposeTransforms, AutoMemoize


class MagusTest(TestCase):
    '''
    Based on the original bug report. 
    '''
    
    def test_magus(self):
        '''
        This was failing.
        '''
        #basicConfig(level=DEBUG)

        name = Word(Letter()) > 'name'

        expression = Delayed()
        variable = Delayed()

        function = (expression / '()') > 'function'
        expression += (variable | function) > 'expression'
        variable += (name | expression / '.' / name)

        dotted_name = function & Eos()

        dotted_name.config.clear().flatten().compose_transforms().auto_memoize()
        dotted_name.config.trace(False)
        parser = dotted_name.get_parse_string()
        parser("1func()")
        

class DelayedCloneTest(TestCase):
    '''
    The original problem for 3.2 was related to clones losing children.
    '''
    
    def test_clone(self):
        '''
        Clone and check children.
        '''
        a = Delayed()
        b = (a | 'c')
        a += b
        
        def simple_clone(node):
            '''
            Clone the node.
            '''
            walker = ConstructorWalker(node, Matcher)
            return walker(DelayedClone())
            
        self.assert_children(b)
        bb = simple_clone(b)
        self.assert_children(bb)
        
        
    def assert_children(self, b):
        '''
        Check children are non-None.
        '''
#        print('>>>{0!s}<<<'.format(b))
        assert is_child(b, Or)
        for child in b.matchers:
            assert child
            


class CloneTest(TestCase):
    '''
    Test various clone functions.
    '''
    
    def test_describe(self):
        '''
        Use a description of the graph to check against changes.
        '''
        #basicConfig(level=DEBUG)

        name = Word(Letter()) > 'name'

        expression = Delayed()
        variable = Delayed()

        function = (expression / '()') > 'function'
        expression += (variable | function) > 'expression'
        variable += (name | expression / '.' / name)

        dotted_name = function & Eos()
        desc0 = NodeStats(dotted_name)
        #print(desc0)
        assert desc0.total == 18, desc0
        self.assert_count(desc0, And, 5)
        self.assert_count(desc0, Or, 2)
        self.assert_count(desc0, Delayed, 2)
        
        clone1 = Flatten()(dotted_name)
        desc1 = NodeStats(clone1)
        #print(desc1)
        # flattened two matchers - one each of And and Or
        assert desc1.total == 16, desc1
        self.assert_count(desc1, And, 4)
        self.assert_count(desc1, Or, 1)
        self.assert_count(desc1, Delayed, 2)
        self.assert_count(desc1, Transform, 7)
        self.assert_count(desc1, TransformationWrapper, 7)
        
        clone2 = ComposeTransforms()(clone1)
        desc2 = NodeStats(clone2)
        #print(desc2)
        # compressed two transforms
        assert desc2.total == 16, desc2
        self.assert_count(desc2, And, 4)
        self.assert_count(desc2, Or, 1)
        self.assert_count(desc2, Delayed, 2)
        self.assert_count(desc2, Transform, 5)
        self.assert_count(desc2, TransformationWrapper, 5)
        
        clone3 = Memoize(RMemo)(clone2)
        desc3 = NodeStats(clone3) 
        #print(desc3)
        assert desc3.total == 16, desc3
        self.assert_count(desc3, _RMemo, 14)
        self.assert_count(desc3, Delayed, 2)

        clone4 = Memoize(LMemo)(clone2)
        desc4 = NodeStats(clone4) 
        #print(desc4)
        assert desc4.total == 16, desc4
        self.assert_count(desc4, _LMemo, 14)
        self.assert_count(desc4, Delayed, 2)
        
        clone5 = AutoMemoize(left=LMemo, right=RMemo)(clone2)
        desc5 = NodeStats(clone5) 
        #print(desc5)
        assert desc5.total == 16, desc5
        self.assert_count(desc5, _RMemo, 9)
        self.assert_count(desc5, _LMemo, 5)
        self.assert_count(desc5, Delayed, 2)
        
        try:
            clone3.config.clear()
            clone3.parse_string('1join()')
            assert False, 'Expected error'
        except MemoException as error:
            assert 'Left recursion with RMemo?' in str(error), str(error)
        
        clone4.config.clear()
        clone4.parse_string('1join()')
        clone5.config.clear()
        clone5.parse_string('1join()')
        
    def assert_count(self, desc, type_, count):
        '''
        Check the count for a given type.
        '''
        try:
            type_ = canonical_matcher_type(type_)
        except MatcherTypeException:
            pass
        assert type_ in desc.types and len(desc.types[type_]) == count, \
            len(desc.types[type_]) if type_ in desc.types else type_

        