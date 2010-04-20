#! /usr/bin/env python
"""
    A class of LyX file.
    
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

import Ebook

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lyx2epub')

class LyX(Ebook):
    
    def add_chapter(self, title, content):
        print "Adding: " + title
        self.chapter_names.append(title)
        self.chapters.append(content)
        
        return
    
    def read(self):
        pass

    def process_body(body):
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
                            print 'Chapter'
                            self.add_chapter(element[1], element[2:])
            
            elif type(element) is unicode:
                print 'Unknown command: ' + element
        
        return
    
    def process_header(body):
        for element in body:
            if type(element) is unicode:
                print 'Unknown command: ' + element
        
        return
    
    def process_document(body):
        for element in body:
            if type(element) is list:
                t = element[0]
                if t.startswith('begin_header'):
                    self.process_header(element)
                elif t.startswith('begin_body'):
                    self.process_body(element)
            elif type(element) is unicode:
                print 'Unknown command: ' + element
        
        return
    
    def process_root(body):
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
                    print 'Unknown command: ' + element
        
        return

