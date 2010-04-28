#!/usr/bin/env python
"""
    Convert LyX file to text file.
    
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

import sys
import logging
import logging.config

import LyxDocument
import TextDocument

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('lyx2ebook')

def lyx2epub(lyx_file):
    """
    Convert Lyx file to ePub file
    """
    
    lyx = LyxDocument.LyxDocument()
    lyx.parse(lyx_file)
    
    logger.info("Title: " + lyx.title)
    logger.info("Author: " + lyx.author)
    
    txt = TextDocument.TextDocument()
    
    txt.convert_from(lyx)
    
    txt.save()
    
    return

if __name__ == '__main__':
    """
    Convert Lyx file to text file.
    
    Usage: lyx2text file.lyx
    """
    
    print 'Converting', sys.argv[1]
    
    # Process Lyx file
    lyx2epub(sys.argv[1])
    
    print 'Converted'
