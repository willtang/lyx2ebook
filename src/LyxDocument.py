#!/usr/bin/env python
"""
    A class of LyX Document.
    
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
import re

from lepl import *

from EbookDocument import *

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('lyx2ebook')

class LyxDocument(EbookDocument):
    
    def __init__(self):
        super(LyxDocument, self).__init__()
    
    def process_standard(self, content):
        
        text = ""
        for element in content:
            if type(element) is unicode or type(element) is str:
                if element != 'begin_layout Standard': 
                    text += element + '\n'
        
        return text
    
    def process_chapter(self, title, content):
        logger.debug("Adding chapter: " + title)
        chapter = Chapter(title)
        for standard in content:
            chapter.add_text(self.process_standard(standard))
        
        #print "TEXT: ", chapter.text
        self.add_chapter(chapter)
        
        return
    
    def process_body(self, body):
        for element in body:
            if type(element) is list:
                # layout block
                t = element[0]
                if type(t) is unicode or type(t) is str:
                    words = t.split()
                    
                    if words[0] == 'begin_layout':
                        
                        if words[1] == 'Title':
                            self.title = element[1]
                        elif words[1] == 'Author':
                            self.author = element[1]
                        elif words[1] == 'Chapter':
                            self.process_chapter(element[1], element[2:])
            
            elif type(element) is unicode:
                logger.warning('Unknown command: ' + element)
        
        return
    
    def process_header(self, body):
        for element in body:
            if type(element) is unicode:
                logger.warning('Unknown command: ' + element)
        
        return
    
    def process_document(self, body):
        for element in body:
            if type(element) is list:
                t = element[0]
                if t.startswith('begin_header'):
                    self.process_header(element)
                elif t.startswith('begin_body'):
                    self.process_body(element)
            elif type(element) is unicode:
                logger.warning('Unknown command: ' + element)
        
        return
    
    def process_root(self, body):
        for element in body:
            if type(element) is list:
                t = element[0]
                if t.startswith('begin_document'):
                    self.process_document(element)
            elif type(element) is unicode:
                words = element.split()
                if words[0] == 'lyxformat':
                    logger.info('LyX document format version ' + words[1])
                else:
                    logger.warning('Unknown command: ' + element)
        
        return
    
    def preprocess(self, text):
        """
        Handle included LyX child document
        """
        def replace_included(match):
            #print 'Opening: ', match.group(1)
            f = open(match.group(1), 'r')
            result = re.search('\\\\begin_body(.+)\\\\end_body', f.read(), re.DOTALL).group(1)
            #print 'Content: ', result
            f.close()
            return result
        
        return re.sub("""\\\\begin_layout Standard\n+\\\\begin_inset CommandInset include\n+LatexCommand include
filename \"([\w\.]+)\"\n+\\\\end_inset\n+\\\\end_layout
""", replace_included, text)
    
    def parse(self, file):
        
        super(LyxDocument, self).set_file(file)
        
        # Match one or more new line
        newlines = ~Newline()[1:]
        
        backslash = ~Literal('\\')
        
        # Match sentence
        sentence = AnyBut(' \\') & Word()[:1] & (Space() & Word())[:] & Space()[:] > "".join
        
        # Match comment which starts a new line with #
        comment = Literal('#') & AnyBut("\n\r")[:] & newlines
        
        # Match command in the format of "\XXX YYY ZZZ ..."
        command = backslash & sentence & newlines > "".join
        
        inset = backslash & Literal('begin_inset') & (Space() & sentence)[:1] & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_inset') & newlines > list
        content = ((sentence & newlines) | inset)[:]
        
        # Main LyX document definition
        #layout = backslash & Literal('begin_layout') & (Space() & Word())[:] & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines > list
        standard = backslash & Literal('begin_layout Standard') & newlines & content & backslash & ~Literal('end_layout') & newlines > list
        chapter = backslash & Literal('begin_layout Chapter') & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines & standard[:] & newlines > list
        date = backslash & Literal('begin_layout Date') & newlines & content & backslash & ~Literal('end_layout') & newlines > list
        author = backslash & Literal('begin_layout Author') & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines > list
        title = backslash & Literal('begin_layout Title') & newlines & (sentence & newlines)[:] & backslash & ~Literal('end_layout') & newlines > list
        body_content = (title | author | ~date | standard | chapter)
        body = backslash & Literal('begin_body') & newlines & body_content[:] & backslash & ~Literal('end_body') & newlines > list
        header = backslash & Literal('begin_header') & newlines & command[:] & backslash & ~Literal('end_header') & newlines > list
        document = backslash & Literal('begin_document') & newlines & header & body & backslash & ~Literal('end_document') & newlines > list
        root = document | command | ~comment
        lyx = root[:]
        
        # Read LyX document
        f = open(file, 'r')
        
        # Parse the LyX document
        preprocessed = self.preprocess(f.read())
        print preprocessed
        result = lyx.parse(preprocessed)
        
        # Close the opened LyX document
        f.close()
        
        self.process_root(result)
        
        return
