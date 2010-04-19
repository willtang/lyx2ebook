from lepl import *

#with TraceVariables():
#    word = ~Lookahead('OR') & Word()
#    phrase = String()
#    with DroppedSpace():
#        text = (phrase | word)[1:] > list
#        query = text[:, Drop('OR')]
#    
#    query.config.auto_memoize(full=True)
#    
#    print query.parse('spicy meatballs OR "el bulli restaurant"')
#

document = Literal('\\begin_document') & ~Newline() & UnsignedInteger() & ~Newline() & Literal('\\end_document') & ~Newline()
root = document | (Literal('\\lyxformat')  & ~Space() & UnsignedInteger() & ~Newline())
lyx = root[:]

f = open('test2.lyx', 'r')

result = lyx.parse(f.read())

f.close()

print result
