STATUS_UNKNOWN             = 0
STATUS_DOCUMENT            = 1
STATUS_HEAD                = 2
STATUS_BODY                = 3
STATUS_TITLE               = 10
STATUS_AUTHOR              = 11
STATUS_PART                = 20
STATUS_PART_CONTENT        = 21
STATUS_CHAPTER             = 22
STATUS_CHAPTER_CONTENT     = 23
STATUS_SECTION             = 24
STATUS_SECTION_CONTENT     = 25
STATUS_SUBSECTION          = 26
STATUS_SUBSECTION_CONTENT  = 27

def processLyx():
    print ">Processing Lyx"
    
    status = STATUS_UNKNOWN
    title = "No Title"
    author = "No Author"
    
    # write the content XHTML
    content_xhtml = open('content.xhtml', 'w')
    
    # read pre-body
    f = open('pre.txt', 'r')
    for line in f:
        #print line
        content_xhtml.write(line)
    
    f = open('novel.lyx', 'r')
    for l in f:
        if l.startswith("#"):
            # Skip comment
            continue
        
        line = l.strip()
        words = line.split(' ')

        if words[0] == "\\begin_document":
            status = STATUS_DOCUMENT
            
        elif words[0] == "\\begin_body":
            status = STATUS_BODY
        
        elif words[0] == "\\begin_layout":
            
            if words[1] == "Title":
                status = STATUS_TITLE
                title = ''
                
            elif words[1] == "Author":
                status = STATUS_AUTHOR
                author = ''
                
            elif words[1] == "Chapter":
                status = STATUS_CHAPTER
                chapter = ''
        
        elif words[0] == "\\end_layout":
            
            if status == STATUS_TITLE:
                # Output chapter
                print "Title: " + title.strip()
                status = STATUS_BODY

            elif status == STATUS_AUTHOR:
                # Output chapter
                print "Author: " + author.strip()
                status = STATUS_BODY

            elif status == STATUS_CHAPTER:
                # Output chapter
                print "Chapter: " + chapter.strip()
                status = STATUS_CHAPTER_CONTENT
            
            else:
                status = STATUS_BODY
        
        elif words[0] == "\\end_body":
            status = STATUS_UNKNOWN
                
        else:
            if status == STATUS_TITLE:
                title += line + "\n"
            
            elif status == STATUS_AUTHOR:
                author += line + "\n"
            
            elif status == STATUS_CHAPTER:
                chapter += line + "\n"
    
    content_xhtml.write('<div class="body">\n')
    content_xhtml.write('<h1>' + title.strip() + '</h1>\n')
    content_xhtml.write('<h2>' + author.strip() + '</h2>\n')
    content_xhtml.write('</div>\n')
    
    # read post-body
    f = open('post.txt', 'r')
    for line in f:
        #print line
        content_xhtml.write(line)
    
    return

def main():
    """
    Convert Lyx file to epub file
    """
    
    # process Lyx file
    processLyx()
    
    return

if __name__ == '__main__':
    main()
