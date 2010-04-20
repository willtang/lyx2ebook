#!/usr/bin/env python
"""
    Convert LyX file to ePub file.
    
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

import EpubDocument

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lyx2epub')

def lyx2epub(lyx_file):
    """
    Convert Lyx file to ePub file
    """
    
    # Should be changed to take in Ebook,
    # therefore easier to implement other source formats
    epub = EpubDocument.EpubDocument(lyx_file)
    
    #epub.convert()
    
    return

if __name__ == '__main__':
    """
    Usage: lyx2epub file.lyx
    
    Convert Lyx file to epub file.
    """
    
    # Process Lyx file
    lyx2epub(sys.argv[1])
