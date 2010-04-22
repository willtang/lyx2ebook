#!/usr/bin/env python
"""
    A class of ePub Document.
    
    This file is part of lyx2ebook.
    
    lyx2ebook is free software: you can redistribute it and/or modify
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

import os
import logging
import zipfile

from zipdir import zipdir

from EbookDocument import EbookDocument
from LyxDocument import LyxDocument

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('lyx2ebook')

class EpubDocument(EbookDocument):
    
    def __init__(self):
        super(EpubDocument, self).__init__()
        
        self.zip = None
    
    def set_file(self, name):
        super(EpubDocument, self).set_file(name);
        
        self.name, self.format = self.file_name.rsplit('.', 2)
        
        self.base_folder = self.name
        self.meta_folder = self.base_folder + "/META-INF"
        self.ops_folder = self.base_folder + "/OPS"
        self.css_folder = self.ops_folder + "/css"
        
        return
    
    def convert_from(self, source):
        name, self.format = source.file_name.rsplit('.', 2)
        self.set_file(name + '.epub')
        
        print 'SOURCE:', source.chapters
        self.chapters = source.chapters
        self.title = source.title
        self.author = source.author
        
        return
    
    def save(self):
        
        logging.info("Converting to ePub...")
        
        self._create_folder()
        
        self._write_mimetype()
        
        self._write_container()
        
        self._write_css()
        
        self._write_chapters()
        
        self._write_metadata()
        
        self._write_navigation()
        
        # Write zip file from the created folder
        zipdir(self.base_folder, self.file_name)
        
        return
    
    def _create_folder(self):
        
        logging.info("Creating directories in " + self.base_folder + "...")
        
        if not os.access(self.base_folder, os.F_OK):
            os.mkdir(self.base_folder)
        
        if not os.access(self.meta_folder, os.F_OK):
            os.mkdir(self.meta_folder)
        
        #self.zip.write(self.meta_folder)
        
        if not os.access(self.ops_folder, os.F_OK):
            os.mkdir(self.ops_folder)
        
        #self.zip.write(self.ops_folder)
        
        if not os.access(self.css_folder, os.F_OK):
            os.mkdir(self.css_folder)
        
        #self.zip.write(self.css_folder)
        
        return
    
    def _write_chapters(self):
        logging.info("Writing chapters...")
        
        for counter, chapter in enumerate(self.chapters):
            self._write_chapter(chapter, counter + 1)
        
        return
    
    def _write_css(self):
        logging.info("Writing CSS...");
        
        f = open(self.css_folder + '/page.css', 'w')
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
    
    def _write_container(self):
        logging.info("Writing Container...")
        
        f = open(self.meta_folder + '/container.xml', 'w')
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
    
    def _write_mimetype(self):
        logging.info("Writing MIME Type...")
        
        f = open(self.base_folder + '/mimetype', 'w')
        mime = "application/epub+zip"
        f.write(mime)
        f.close()
        
        return
    
    def _write_chapter(self, chapter, num):
        
        f = open(self.ops_folder + '/chapter' + str(num) + '.xhtml', 'w')
        
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
        f.write(pre)
        
        f.write('<div class="body chapter">\n')
        
        f.write('  <h2>Chapter ' + str(num) + ' ' + chapter.title + '</h2>\n\n')
        
        f.write('  <p>')
        f.write(chapter.text)
        f.write('</p>\n\n')
        
        f.write('</div>\n')
        
        post = """
</body>
</html>
"""
        f.write(post)
        
        f.close()
        
        return
    
    def _write_metadata(self):
        logging.info("Writing metadata file...")
        
        
        f = open(self.ops_folder + '/book.opf', 'w')
        
        pre = """<?xml version="1.0"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="GeneratedBookId">

  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>Lorem Ipsum</dc:title>
    <dc:language>en</dc:language>
    <dc:identifier id="BookId" opf:scheme="ISBN">123456789X</dc:identifier>
    <dc:creator opf:file-as="Tang, Will" opf:role="tan">Will Tang</dc:creator>
  </metadata>
 
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter3" href="chapter3.xhtml" media-type="application/xhtml+xml"/>
    <item id="stylesheet" href="page.css" media-type="text/css"/>
    <item id="ncx" href="book.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
 
  <spine toc="ncx">
    <itemref idref="chapter1" />
    <itemref idref="chapter2" />
    <itemref idref="chapter3" />
  </spine>

"""
        f.write(pre)
        
        
        
        post = """
</package>
"""
        f.write(post)
        
        f.close()
        
        return
    
    def _write_navigation(self):
        logging.info("Writing Navigation Control file...")
        
        f = open(self.ops_folder + '/book.ncx', 'w')
        
        pre = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
 
<ncx version="2005-1" xml:lang="en" xmlns="http://www.daisy.org/z3986/2005/ncx/">
 
  <head>
<!-- The following four metadata items are required for all NCX documents,
including those conforming to the relaxed constraints of OPS 2.0 -->
 
    <meta name="dtb:uid" content="123456789X"/> <!-- same as in .opf -->
    <meta name="dtb:depth" content="1"/> <!-- 1 or higher -->
    <meta name="dtb:totalPageCount" content="0"/> <!-- must be 0 -->
    <meta name="dtb:maxPageNumber" content="0"/> <!-- must be 0 -->
  </head>

"""
        f.write(pre)
        
        f.write("<docTitle>\n")
        f.write("  <text>" + self.title + "</text>\n")
        f.write("</docTitle>\n\n")
        
        f.write("<docAuthor>\n")
        f.write("  <text>" + self.author + "</text>\n")
        f.write("</docAuthor>\n\n")
        
        f.write("<navMap>\n\n")
        
        for counter, chapter in enumerate(self.chapters):
            ch_num = str(counter + 1)
            f.write('  <navPoint class="chapter" id="chapter' + ch_num + '" playOrder="' + ch_num + '">\n')
            f.write('    <navLabel><text>Chapter ' + ch_num + '</text></navLabel>\n')
            f.write('    <content src="chapter' + ch_num + '.xhtml"/>\n')
            f.write('  </navPoint>\n\n')
        
        f.write("</navMap>\n\n")
        
        post = """</ncx>
"""
        f.write(post)
        
        f.close()
        
        return
