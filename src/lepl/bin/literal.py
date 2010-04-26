
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
Specify and construct binary structures.

This is necessary for tests and may be useful in its own right.  Note that it
is also quite easy to construct `Node` instances with `BitString` data directly 
in Python.

The construction of binary values is a two-stage process.  First, we describe
a Python structure.  Then we encode that structure as a binary value.  As is
standard in LEPL, the Python construct consists of `Node` instances.

The description of values has the form:
  Node(byte=0xff/8, 0*100, Node(...), (...))
  
In more detail:
  () is used for grouping, must exist outside the entire description, and
     defines a Node.  If preceded by a name, then that is used to create 
     a subclass of Node (unless it is "Node", in which case it is the 
     default).  For now, repeated names are not validated in any way for 
     consistency.
  name=value/length is used for defining a value, in various ways:
    value anonymous value (byte or array)
    value/length anonymous value with specified length
    name=value named byte or array
    name=value/length named value with given length
  * repeats a value, so a*b repeats 'a', b number of times.
'''

if bytes is str:
    print('Binary parsing unsupported in this Python version')
else:

    from lepl.bin.bits import BitString
    from lepl.support.node import Node
    
    
    def make_binary_parser():
        '''
        Create a parser for binary data.
        '''
        
        # avoid import loops
        from lepl import Word, Letter, Digit, UnsignedInteger, \
            Regexp, DfaRegexp, Drop, Separator, Delayed, Optional, Any, First, \
            args
            
        classes = {}
        
        def named_class(name, *args):
            '''
            Given a name and some args, create a sub-class of Binary and 
            create an instance with the given content.
            '''
            if name not in classes:
                classes[name] = type(name, (Node,), {})
            return classes[name](*args)
        
        mult    = lambda l, n: BitString.from_sequence([l] * int(n, 0)) 
            
        # an attribute or class name
        name    = Word(Letter(), Letter() | Digit() | '_')
    
        # lengths can be integers (bits) or floats (bytes.bits)
        # but if we have a float, we do not want to parse as an int
        # (or we will get a conversion error due to too small length)
        length  = First(UnsignedInteger() + '.' + Optional(UnsignedInteger()),
                        UnsignedInteger())
    
        # a literal decimal
        decimal = UnsignedInteger()
    
        # a binary number (without pre/postfix)
        binary  = Any('01')[1:]
    
        # an octal number (without pre/postfix)
        octal   = Any('01234567')[1:]
    
        # a hex number (without pre/postfix)
        hex_     = Regexp('[a-fA-F0-9]')[1:]
        
        # the letters used for binary, octal and hex values 
        #(eg the 'x' in 0xffee)
        # pylint: disable-msg=C0103
        b, o, x, d = Any('bB'), Any('oO'), Any('xX'), Any('dD')
    
        # a decimal with optional pre/postfix
        dec     = '0' + d + decimal | decimal + d + '0' | decimal
    
        # little-endian literals have normal prefix syntax (eg 0xffee) 
        little  = decimal | '0' + (b + binary | o + octal | x + hex_)
    
        # big-endian literals have postfix (eg ffeex0)
        big     = (binary + b | octal + o | hex_ + x) + '0'
    
        # optional spaces - will be ignored 
        # (use DFA here because it's multi-line, so \n will match ok)
        spaces  = Drop(DfaRegexp('[ \t\n\r]*'))
            
        with Separator(spaces):
            
            # the grammar is recursive - expressions can contain expressions - 
            # so we use a delayed matcher here as a placeholder, so that we can 
            # use them before they are defined.
            expr = Delayed()
            
            # an implict length value can be big or little-endian
            ivalue = big | little                 > args(BitString.from_int)
            
            # a value with a length can also be decimal
            lvalue = (big | little | dec) & Drop('/') & length  \
                                                  > args(BitString.from_int)
            
            value = lvalue | ivalue
            
            repeat = value & Drop('*') & little   > args(mult)
            
            # a named value is also a tuple
            named = name & Drop('=') & (expr | value | repeat)  > tuple
            
            # an entry in the expression could be any of these
            entry = named | value | repeat | expr
            
            # and an expression itself consists of a comma-separated list of
            # one or more entries, surrounded by paremtheses
            entries = Drop('(') & entry[1:, Drop(',')] & Drop(')')
            
            # the Binary node may be explicit or implicit and takes the list of
            # entries as an argument list
            node = Optional(Drop('Node')) & entries             > Node
            
            # alternatively, we can give a name and create a named sub-class
            other = name & entries                > args(named_class)
            
            # and finally, we "tie the knot" by giving a definition for the
            # delayed matcher we introduced earlier, which is either a binary
            # node or a subclass
            expr += spaces & (node | other) & spaces
        
        return expr.get_parse_string()
    
    
    __PARSER = None
    
    def parse(spec):
        '''
        Use the parser.
        '''
        # pylint: disable-msg=W0603
        # global
        global __PARSER
        if __PARSER is None:
            __PARSER = make_binary_parser()
        result = __PARSER(spec)
        if result:
            return result[0]
        else:
            raise ValueError('Cannot parse: {0!r}'.format(spec))
