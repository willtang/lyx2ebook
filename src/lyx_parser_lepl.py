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

def parse(file):
    # Match one or more new line
    newlines = ~Newline()[1:]
    
    slash = ~Literal('\\')
    
    # Match sentence
    sentence = Word() & (Space() & Word())[:] & Space()[:] > "".join
    
    # Match comment which starts a new line with #
    comment = Literal('#') & AnyBut("\n\r")[:] & newlines
    
    # Match command in the format of "\XXX YYY ZZZ ..."
    command = slash & sentence & newlines > "".join
    
    # Main LyX document definition
    layout = slash & Literal('begin_layout') & newlines & (command | (sentence & newlines))[:] & slash & ~Literal('end_layout') & newlines > list
    body = slash & Literal('begin_body') & newlines & (command | (sentence & newlines))[:] & slash & ~Literal('end_body') & newlines > list
    header = slash & Literal('begin_header') & newlines & command[:] & slash & ~Literal('end_header') & newlines > list
    document = slash & Literal('begin_document') & newlines & header & body & slash & ~Literal('end_document') & newlines > list
    root = document | command | ~comment
    lyx = root[:]
    
    # Read LyX document
    f = open(file, 'r')
    
    # Parse the LyX document
    result = lyx.parse(f.read())
    
    # Close the opened LyX document
    f.close()
    
    return result

if __name__ == "__main__":
    
    print parse('novel.lyx')
