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
        
        self.folder, self.format = self.file_name.rsplit('.', 2)
        
        self.base_folder = self.folder + "/"
        self.meta_folder = "META-INF/"
        self.ops_folder = "OPS/"
        self.css_folder = self.ops_folder + "css/"
        
        return
    
    def convert_from(self, source):
        name, self.format = source.file_name.rsplit('.', 2)
        self.set_file(name + '.zip')
        
        self.chapters = source.chapters
        
        return
    
    def save(self):
        
        logging.info("Converting to ePub...")
        
        #self.zip = zipfile.ZipFile(self.file_name, 'w', zipfile.ZIP_STORED)
        
        self._create_folder()
        
        self._write_mimetype()
        
        self._write_container()
        
        self._write_css()
        
        self._write_content()
        
        #self.zip.close()
        
        return
    
    def _create_folder(self):
        
        logging.info("Creating directories in " + self.base_folder + "...")
        
        if not os.access(self.base_folder, os.F_OK):
            os.mkdir(self.base_folder)
        
        if not os.access(self.base_folder + self.meta_folder, os.F_OK):
            os.mkdir(self.base_folder + self.meta_folder)
        
        #self.zip.write(self.meta_folder)
        
        if not os.access(self.base_folder + self.ops_folder, os.F_OK):
            os.mkdir(self.base_folder + self.ops_folder)
        
        #self.zip.write(self.ops_folder)
        
        if not os.access(self.base_folder + self.css_folder, os.F_OK):
            os.mkdir(self.base_folder + self.css_folder)
        
        #self.zip.write(self.css_folder)
        
        return
    
    def _write_content(self):
        logging.info("Writing content...")
        
        for counter, chapter in enumerate(self.chapters):
            self._write_chapter(chapter, counter)
        
        return
    
    def _write_css(self):
        logging.info("Writing CSS...");
        
        f = open(self.base_folder + self.css_folder + 'page.css', 'w')
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
        
        f = open(self.base_folder + self.meta_folder + 'container.xml', 'w')
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
        
        f = open(self.base_folder + 'mimetype', 'w')
        mime = "application/epub+zip"
        f.write(mime)
        f.close()
        
        return
    
    def _write_chapter(self, chapter, num):
        
        f = open(self.base_folder + self.ops_folder + 'chapter' + str(num) + '.xhtml', 'w')
        
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
