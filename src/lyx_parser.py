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
    
    backslash = ~Literal('\\')
    
    # Match sentence
    sentence = AnyBut(' \\') & Word()[:1] & (Space() & Word())[:] & Space()[:] > "".join
    
    # Match comment which starts a new line with #
    comment = Literal('#') & AnyBut("\n\r")[:] & newlines
    
    # Match command in the format of "\XXX YYY ZZZ ..."
    command = backslash & sentence & newlines > "".join
    
    # Main LyX document definition
    #layout = backslash & Literal('begin_layout') & (Space() & Word())[:] & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines > list
    standard = backslash & Literal('begin_layout Standard') & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines > list
    chapter = backslash & Literal('begin_layout Chapter') & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines & standard[:] & newlines > list
    author = backslash & Literal('begin_layout Author') & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines > list
    title = backslash & Literal('begin_layout Title') & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines > list
    content = (title | author | chapter)
    body = backslash & Literal('begin_body') & newlines & content[:] & backslash & ~Literal('end_body') & newlines > list
    header = backslash & Literal('begin_header') & newlines & command[:] & backslash & ~Literal('end_header') & newlines > list
    document = backslash & Literal('begin_document') & newlines & header & body & backslash & ~Literal('end_document') & newlines > list
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
