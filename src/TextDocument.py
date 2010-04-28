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

import logging

from EbookDocument import EbookDocument

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('lyx2ebook')

class TextDocument(EbookDocument):
    
    def __init__(self):
        super(TextDocument, self).__init__()
        
    def convert_from(self, source):
        name, self.format = source.file_name.rsplit('.', 2)
        self.set_file(name + '.txt')
        
        self.chapters = source.chapters
        self.title = source.title
        self.author = source.author
        
        return
    
    def save(self):
        
        logging.info("Converting to text...")
        
        f = open(self.file_name, 'w')
        
        f.write(self.title + '\n')
        f.write('by ' + self.author + '\n\n\n')
        
        for counter, chapter in enumerate(self.chapters):
            chapter_num = str(counter + 1)
            
            f.write('Chapter %s %s\n\n' % (chapter_num, chapter.title))
            
            for paragraph in chapter.paragraphs:
                
                f.write(paragraph.text + '\n')
            
            f.write('\n\n')
        
        f.close()
        
        return
