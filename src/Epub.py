#! /usr/bin/env python
"""
    A class of ePub file.
    
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

import LyX

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lyx2epub')

class Epub:
    
    def __init__(self, source):
        self.source_file = source
        self.folder, self.source_format = source_file.rsplit('.', 2)
        self.set_base_folder(file_name)

    def set_base_folder(self, folder):
        self.base_folder = folder
        self.meta_folder = self.base_folder + "/META-INF"
        self.ops_folder = self.base_folder + "/OPS"
        self.css_folder = self.ops_folder + "/css"
        
        return
    
    def convert(self):
        
#        if self.source_format.lower() == 'lyx':
#            convert_from_lyx()
#        else:
#            logger.error("Unknown file type: " + self.source_format)
        
        logging.info("Converting to ePub...")
        
        create_folder()
        
        write_mimetype()
        
        write_container()
        
        write_css()
        
        write_content()
        
        return
    
    def create_folder(self):
        
        logging.info("Creating directories in " + self.folder + "...")
        
        if not os.access(self.base_folder, os.F_OK):
            os.mkdir(self.base_folder)
        
        if not os.access(self.meta_folder, os.F_OK):
            os.mkdir(self.meta_folder)
        
        if not os.access(self.ops_folder, os.F_OK):
            os.mkdir(self.ops_folder)
        
        if not os.access(self.css_folder, os.F_OK):
            os.mkdir(self.css_folder)
        
        return
    
    def write_content(self):
        logging.info("Writing content...")
        
        convert()
        
        return
    
    def write_css(self):
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
    
    def write_container(self):
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
    
    def writeMimeType(self):
        logging.info("Writing MIME Type...")
        
        f = open(self.base_folder + '/mimetype', 'w')
        mime = "application/epub+zip"
        f.write(mime)
        f.close()
        
        return
    
    def write_chapter(title):
        
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
    
