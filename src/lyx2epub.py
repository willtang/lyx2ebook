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
import lyx_parser
import LyX, Epub

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lyx2epub')

def beginChapter(title):
    
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
    
    return

def processBody(body, lyx):
    for element in body:
        if type(element) is list:
            # layout block
            t = element[0]
            if type(t) is unicode or type(t) is str:
                words = t.split()
                
                if words[0] == 'begin_layout':
                    
                    if words[1] == 'Title':
                        lyx.title = element[1]
                    elif words[1] == 'Author':
                        lyx.author = element[1]
                    elif words[1] == 'Chapter':
                        print 'Chapter'
                        lyx.addChapter(element[1], element[2:])
        
        elif type(element) is unicode:
            print 'Unknown command: ' + element
    
    return lyx

def processHeader(body, lyx):
    for element in body:
        if type(element) is unicode:
            print 'Unknown command: ' + element
    
    return lyx

def processDocument(body, lyx):
    for element in body:
        if type(element) is list:
            t = element[0]
            if t.startswith('begin_header'):
                processHeader(element, lyx)
            elif t.startswith('begin_body'):
                processBody(element, lyx)
        elif type(element) is unicode:
            print 'Unknown command: ' + element
    
    return

def processRoot(body, lyx):
    for element in body:
        if type(element) is list:
            t = element[0]
            if t.startswith('begin_document'):
                processDocument(element, lyx)
        elif type(element) is unicode:
            words = element.split()
            if words[0] == 'lyxformat':
                logger.info('LyX document format version ' + words[1])
            else:
                print 'Unknown command: ' + element
    
    return lyx

def convertLyx2epub(lyx_file):
    """
    Convert Lyx file to epub file
    """
    
    epub = Epub.Epub()
    
    output_file, ext = lyx_file.rsplit('.', 2)
    
    logging.info("Creating directories in " + output_file + "...")
    
    epub.source_file = lyx_file
    epub.set_base_folder(output_file)
    
    if not os.access(epub.base_folder, os.F_OK):
        os.mkdir(epub.base_folder)
    
    if not os.access(epub.meta_folder, os.F_OK):
        os.mkdir(epub.meta_folder)
    
    if not os.access(epub.ops_folder, os.F_OK):
        os.mkdir(epub.ops_folder)
    
    if not os.access(epub.css_folder, os.F_OK):
        os.mkdir(epub.css_folder)
    
    writeMimeType(epub)
    
    writeContainer(epub)
    
    writeCss(epub)
    
    writeContent(epub)
    
    return

def writeContent(epub):
    logging.info("Processing Lyx...")
    
    tree = lyx_parser.parse(epub.source_file)
    
    lyx = processRoot(tree, LyX.LyX())
    
    print len(lyx.chapters)
    
    for chapter in lyx.chapters:
        print chapter
    
    return
    
    # Write to the XHTML
    content_xhtml = open(folder + "/chapter0.xhtml", 'w')
    
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
    post = """
</body>
    
</html>
"""
    
    sep = """<div>
  <hr class="sigilChapterBreak" />
</div>
"""
    
    content_xhtml.write(pre)
    
    tree = lyx_parser.parse(lyx_file)
    
    lyx = processRoot(tree, LyX.LyX())
    
    print 'Title: ' + lyx.title
    print 'Author: ' + lyx.author
    
    print 'TREE: '
    print tree
    
    content_xhtml.write('\n')
    
    content_xhtml.write('<div class="body">\n')
    content_xhtml.write('  <h1>' + "".strip() + '</h1>\n')
    content_xhtml.write('  <h2>' + "".strip() + '</h2>\n')
    content_xhtml.write('</div>\n')
    
    content_xhtml.write('\n')
    
    content_xhtml.write(sep)
    
    content_xhtml.write('\n')
    
    # Write post-body
    content_xhtml.write(post)
    
    content_xhtml.close()
    
    return

def writeCss(epub):
    logging.info("Processing CSS...");
    
    f = open(epub.css_folder + '/page.css', 'w')
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

def writeContainer(epub):
    logging.info("Processing Container...")
    
    f = open(epub.meta_folder + '/container.xml', 'w')
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

def writeMimeType(epub):
    logging.info("Processing MIME Type...")
    
    f = open(epub.base_folder + '/mimetype', 'w')
    mime = "application/epub+zip"
    f.write(mime)
    f.close()
    
    return

if __name__ == '__main__':
    """
    Usage: lyx2epub file.lyx
    
    Convert Lyx file to epub file.
    """
    
    # Process Lyx file
    convertLyx2epub(sys.argv[1])
