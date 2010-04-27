#!/usr/bin/env python
"""
    A class of Rich Text Format v1.3 Document.
    
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

from EbookDocument import *

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('lyx2ebook')

class RTFDocument(EbookDocument):
    
    def __init__(self):
        super(RTFDocument, self).__init__()
        
        self.file_ext = '.rtf'
    
    def save(self):
        
        logging.info("Converting to RTF...")
        
        f = open(self.file_name, 'w')
        
        f.write('{\\rtf\\ansi\\ansicpg1252\\cocoartf949\\cocoasubrtf540')
        
        f.write('{\\fonttbl\\f0\\fswiss\\fcharset0 Arial;}')
        f.write('{\\colortbl;\\red255\\green255\\blue255;}')
        
        f.write('\\pard\\pardeftab720\\f0')
        f.write('\\fs36 \\cf0 ' + self.title + '\\\n')
        f.write('by ' + self.author + '\\\n')
        
        for counter, chapter in enumerate(self.chapters):
            chapter_num = str(counter + 1)
            f.write('\\\n')
            f.write('\\fs32 Chapter ' + chapter_num + ' ' + chapter.title + '\\\n')
            
            for paragraph in chapter.paragraphs:
                f.write('\\fs22 ' + paragraph.text + '\\\n')
        
        f.write('}')
        
        f.close()
        
        return
