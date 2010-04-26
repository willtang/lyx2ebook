
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
# Contributor(s):
# - "mereandor" / mereandor at gmail dot com (Roman)
# Portions created by the Contributors are Copyright (C) 2009
# The Contributors.  All Rights Reserved.
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
Contributed matchers.
'''

from copy import copy

from lepl.matchers.derived import Optional
from lepl.matchers.combine import And, Or, BaseSearch
from lepl.matchers.matcher import is_child
from lepl.matchers.transform import Transform
from lepl.matchers.operators import _BaseSeparator


# (c) 2009 "mereandor" / mereandor at gmail dot com (Roman), Andrew Cooke

# pylint: disable-msg=R0903
class SmartSeparator2(_BaseSeparator):
    '''
    A substitute `Separator` with different semantics for optional matchers.
    This identifies optional matchers by type (whether they subclass 
    `BaseSearch`) and then constructs a replacement that adds space only
    when both matchers are used.
    
    See also `SmartSeparator1`, which is more general but less efficient.
    '''
    
    def _replacements(self, separator):
        '''
        Provide alternative definitions of '&` and `[]`.
        '''
        
        def non_optional_copy(matcher):
            '''
            Check whether a matcher is optional and, if so, make it not so.
            '''
            # both of the "copy" calls below make me nervous - it's not the
            # way the rest of lepl works - but i don't have any specific
            # criticism, or a good alternative.
            required, optional = matcher, False
            if isinstance(matcher, Transform):
                temp, optional = non_optional_copy(matcher.matcher)
                if optional:
                    required = copy(matcher)
                    required.matcher = temp
            elif is_child(matcher, BaseSearch, fail=False):
                # this introspection only works because Repeat sets named
                # (ie kargs) arguments. 
                optional = (matcher.start == 0)
                if optional:
                    required = copy(matcher)
                    required.start = 1
                    if required.stop == 1:
                        required = required.first
            return required, optional

        # pylint: disable-msg=W0141
        def and_(matcher_a, matcher_b):
            '''
            Combine two matchers.
            '''
            (requireda, optionala) = non_optional_copy(matcher_a)
            (requiredb, optionalb) = non_optional_copy(matcher_b)
          
            if not (optionala or optionalb):
                return And(matcher_a, separator, matcher_b)
            else:
                matcher = Or(
                    *filter((lambda x: x is not None), [
                        And(Optional(And(requireda, separator)), requiredb) 
                            if optionala else None,
                        And(requireda, Optional(And(separator, requiredb))) 
                            if optionalb else None]))
                if optionala and optionalb:
                    # making this explicit allows chaining (we can detect it
                    # when called again in a tree of "ands")
                    matcher = Optional(matcher)
                return matcher
        return (and_, self._repeat(separator))
    
