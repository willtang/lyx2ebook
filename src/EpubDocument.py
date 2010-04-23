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
import random
import zipfile
from xml.dom.minidom import parse, parseString

from zipdir import zipdir

from EbookDocument import EbookDocument
from LyxDocument import LyxDocument

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('lyx2ebook')

class EpubDocument(EbookDocument):
    
    def __init__(self):
        super(EpubDocument, self).__init__()
        
        self._dc = 'http://purl.org/dc/elements/1.1/'
        self._opf = 'http://www.idpf.org/2007/opf'
        
        self.uid = 'Book_%05d' % random.randint(1, 99999)
        
        self.zip = None
        self.template_folder = "template"
    
    def set_file(self, name):
        super(EpubDocument, self).set_file(name);
        
        self.name, self.format = self.file_name.rsplit('.', 2)
        
        self.base_folder = self.name
        
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
        
        # Write a new zip file from the created folder
        if os.access(self.file_name, os.F_OK):
            os.remove(self.file_name)
        zipdir(self.base_folder, self.file_name)
        
        return
    
    def _create_folder(self):
        
        logging.info("Creating directories in " + self.base_folder + "...")
        
        if not os.access(self.base_folder, os.F_OK):
            os.mkdir(self.base_folder)
        
        if not os.access(self.base_folder + '/META-INF', os.F_OK):
            os.mkdir(self.base_folder + '/META-INF')
        
        #self.zip.write(self.meta_folder)
        
        if not os.access(self.base_folder + '/OPS', os.F_OK):
            os.mkdir(self.base_folder + '/OPS')
        
        #self.zip.write(self.ops_folder)
        
        if not os.access(self.base_folder + '/OPS/css', os.F_OK):
            os.mkdir(self.base_folder + '/OPS/css')
        
        #self.zip.write(self.css_folder)
        
        return
    
    def _write_chapters(self):
        logging.info("Writing chapters...")
        
        for counter, chapter in enumerate(self.chapters):
            self._write_chapter(chapter, counter + 1)
        
        return
    
    def _write_css(self):
        logging.info("Writing CSS...");
        
        fi = open(self.template_folder + '/OPS/css/style.css', 'r')
        fo = open(self.base_folder + '/OPS/css/style.css', 'w')
        
        fo.write(fi.read())
        
        fi.close()
        fo.close()
        
        return
    
    def _write_container(self):
        logging.info("Writing Container...")
        
        fi = open(self.template_folder + '/META-INF/container.xml', 'r')
        fo = open(self.base_folder + '/META-INF/container.xml', 'w')
        
        fo.write(fi.read())
        
        fi.close()
        fo.close()
        
        return
    
    def _write_mimetype(self):
        logging.info("Writing MIME Type...")
        
        f = open(self.base_folder + '/mimetype', 'w')
        mime = "application/epub+zip"
        f.write(mime)
        f.close()
        
        return
    
    def _write_chapter(self, chapter, num):
        
        f = open(self.base_folder + '/OPS/chapter' + str(num) + '.xhtml', 'w')
        doc = parse(self.template_folder + '/OPS/chapter.xhtml')
        
        e = doc.getElementsByTagName('div')[0]
        
        xml = parseString('<div class="chapter"><h2><span class="chapterHeader"><span class="translation">' +
                          'Chapter</span> <span class="count">' + str(num) + '</span></span> ' +
                          chapter.title + '</h2></div>')
        header = doc.importNode(xml.firstChild, True)
        e.appendChild(header)
        
        div = doc.createElement('div')
        e.appendChild(div)
        
        for para in chapter.text.split('\n'):
            p = doc.createElement('p')
            p.appendChild(doc.createTextNode(para))
            div.appendChild(p)
        
        doc.writexml(f, '', '', '', 'utf-8')
        f.close()
        
        return
    
    def _write_metadata(self):
        logging.info("Writing metadata file...")
        
        f = open(self.base_folder + '/OPS/book.opf', 'w')
        doc = parse(self.template_folder + '/OPS/book.opf')
        
        identifier = doc.getElementsByTagNameNS(self._dc, 'identifier')[0]
        identifier.appendChild(doc.createTextNode(self.uid))
        
        title = doc.getElementsByTagNameNS(self._dc, 'title')[0]
        title.appendChild(doc.createTextNode(self.title))
        
        creator = doc.getElementsByTagNameNS(self._dc, 'creator')[0]
        creator.setAttributeNS(self._opf, 'opf:file-as', self.author)
        creator.appendChild(doc.createTextNode(self.author))
        
        manifest = doc.getElementsByTagName('manifest')[0]
        spine = doc.getElementsByTagName('spine')[0]
        for counter, chapter in enumerate(self.chapters):
            ch_num = str(counter + 1)
            
            item = doc.createElement('item')
            item.setAttribute('id', 'chapter' + ch_num)
            item.setAttribute('href', 'chapter' + ch_num + '.xhtml')
            item.setAttribute('media-type', 'application/xhtml+xml')
            manifest.appendChild(item)
        
            itemref = doc.createElement('itemref')
            itemref.setAttribute('idref', 'chapter' + ch_num)
            itemref.setAttribute('linear', 'yes')
            spine.appendChild(itemref)
        
        item = doc.createElement('item')
        item.setAttribute('id', 'main-style')
        item.setAttribute('href', 'css/style.css')
        item.setAttribute('media-type', 'text/cs')
        manifest.appendChild(item)
        
        item = doc.createElement('item')
        item.setAttribute('id', 'ncx')
        item.setAttribute('href', 'book.ncx')
        item.setAttribute('media-type', 'application/x-dtbncx+xml')
        manifest.appendChild(item)
        
        doc.writexml(f, '', '', '', 'utf-8')
        f.close()
        
        return
    
    def _write_navigation(self):
        logging.info("Writing Navigation Control file...")
        
        f = open(self.base_folder + '/OPS/book.ncx', 'w')
        doc = parse(self.template_folder + '/OPS/book.ncx')
        
        meta = doc.getElementsByTagName('meta')
        for m in meta:
            if m.getAttribute('name') == 'dtb:uid':
                m.setAttribute('content', self.uid)
        
        docTitle = doc.getElementsByTagName('docTitle')[0]
        text = doc.createElement('text')
        text.appendChild(doc.createTextNode(self.title))
        docTitle.appendChild(text)
        
        docAuthor = doc.getElementsByTagName('docAuthor')[0]
        text = doc.createElement('text')
        text.appendChild(doc.createTextNode(self.author))
        docAuthor.appendChild(text)
        
        navMap = doc.getElementsByTagName('navMap')[0]
        for counter, chapter in enumerate(self.chapters):
            ch_num = str(counter + 1)
            
            navPoint = doc.createElement('navPoint')
            navPoint.setAttribute('class', 'chapter')
            navPoint.setAttribute('id', ch_num)
            navPoint.setAttribute('playOrder', ch_num)
            navMap.appendChild(navPoint)
            
            navLabel = doc.createElement('navLabel')
            text = doc.createElement('text')
            text.appendChild(doc.createTextNode('Chapter ' + ch_num))
            navLabel.appendChild(text)
            navPoint.appendChild(navLabel)
            
            content = doc.createElement('content')
            content.setAttribute('src', 'chapter' + ch_num + '.xhtml')
            navPoint.appendChild(content)
        
        doc.writexml(f, '', '', '', 'utf-8')
        f.close()
        
        return
