#! /usr/bin/env python
"""
    Convert LyX file to ePub file.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import os
import logging
import rp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lyx2epub')

STATUS_UNKNOWN = 0
STATUS_DOCUMENT = 1
STATUS_HEAD = 2
STATUS_BODY = 3
STATUS_TITLE = 10
STATUS_AUTHOR = 11
STATUS_PART = 20
STATUS_PART_CONTENT = 21
STATUS_CHAPTER = 22
STATUS_CHAPTER_CONTENT = 23
STATUS_SECTION = 24
STATUS_SECTION_CONTENT = 25
STATUS_SUBSECTION = 26
STATUS_SUBSECTION_CONTENT = 27

def convertLyx2epub(lyx_file):
    """
    Convert Lyx file to epub file
    """
    
    output_file, ext = lyx_file.rsplit('.', 2)
    
    logging.info("Creating directories in " + output_file + "...")
    
    base_folder = output_file
    meta_folder = base_folder + "/META-INF"
    ops_folder = base_folder + "/OPS"
    css_folder = ops_folder + "/css"
    
    if not os.access(base_folder, os.F_OK):
        os.mkdir(base_folder)
    
    if not os.access(meta_folder, os.F_OK):
        os.mkdir(meta_folder)
    
    if not os.access(ops_folder, os.F_OK):
        os.mkdir(ops_folder)
    
    if not os.access(css_folder, os.F_OK):
        os.mkdir(css_folder)
    
    writeMimeType(base_folder)
    
    writeContainer(meta_folder)
    
    writeCss(css_folder)
    
    writeContent(ops_folder)
    
    return

def writeContent(folder):
    logging.info("Processing Lyx...")
    
    status = STATUS_UNKNOWN
    title = "No Title"
    author = "No Author"
    
    # Write to the XHTML
    content_xhtml = open(folder + "/chapter1.xhtml", 'w')
    
    # Write pre-body
    pre = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title></title>
  <style type="text/css">
/*<![CDATA[*/
  @import "page.css";
  /*]]>*/
  </style>
</head>

<body>
""" 
    content_xhtml.write(pre)
    
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
                logging.debug("Title: " + title.strip())
                status = STATUS_BODY

            elif status == STATUS_AUTHOR:
                # Output chapter
                logging.debug("Author: " + author.strip())
                status = STATUS_BODY

            elif status == STATUS_CHAPTER:
                # Output chapter
                logging.debug("Chapter: " + chapter.strip())
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
    
    content_xhtml.write('\n')
    
    content_xhtml.write('<div class="body">\n')
    content_xhtml.write('  <h1>' + title.strip() + '</h1>\n')
    content_xhtml.write('  <h2>' + author.strip() + '</h2>\n')
    content_xhtml.write('</div>\n')
    
    content_xhtml.write('\n')
    
    content_xhtml.write('<div>\n')
    content_xhtml.write('  <hr class="sigilChapterBreak" />\n')
    content_xhtml.write('</div>\n')
    
    content_xhtml.write('\n')
    
    # Write post-body
    post = """
</body>
    
</html>
"""
    content_xhtml.write(post)
    
    content_xhtml.close()
    
    return

def writeCss(folder):
    logging.info("Processing CSS...");
    
    f = open(folder + '/page.css', 'w')
    css = """
body {padding: 0;}

hr.sigilChapterBreak {
  border: none 0;
  border-top: 3px double #c00;
  height: 3px;
  clear: both;
}
"""
    f.write(css)
    f.close()
    
    return

def writeContainer(folder):
    logging.info("Processing Container...")
    
    f = open(folder + '/container.xml', 'w')
    mime = """<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/book.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""
    f.write(mime)
    f.close()
    
    return

def writeMimeType(folder):
    logging.info("Processing MIME Type...")
    
    f = open(folder + '/mimetype', 'w')
    mime = "application/epub+zip"
    f.write(mime)
    f.close()
    
    return

def main():
    """
    Usage: lyx2epub file.lyx
    
    Convert Lyx file to epub file.
    """
    
    # Process Lyx file
    convertLyx2epub(sys.argv[1])
    
    return

if __name__ == '__main__':
    main()
