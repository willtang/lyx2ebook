#!/usr/bin/env python
"""
    A class of eBook Document.
    
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

class EbookDocument(object):
    
    def __init__(self):
        self.title = "No Title"
        self.author = "Unknown Author"
        self.chapters = []
        self.file_name = ""
    
    def set_file(self, name):
        self.file_name = name
        
        return
    
    def write_content(self):
        logging.error("Write content function undefined.")
    
    def add_chapter(self, chapter):
        self.chapters.append(chapter)

class Chapter(object):
    
    def __init__(self, title):
        self.title = title
        self.paragraphs = []
    
    def add_paragraph(self, text):
        self.paragraphs.append(Paragraph(text))

class Paragraph(object):
    
    def __init__(self, text):
        self.text = text
