lyx2ebook
=========
0.1.2 alpha  


What is lyx2ebook
-----------------

I planned to write a book, and LyX is always preferred when dealing with publishing.
However, Lyx only does a good job for PDF file but not eBook format likes ePub, and I could not find a good converter.
Therefore, I wrote this simple LyX-to-eBook converter to do the job.

It is written in Python 2.6.



Features
--------

- Convert from LyX file, but ignore most formatting.
- Convert to ePub 2.0 file.



Usage
-----

Convert LyX document to ePub file:

    lyx2epub simple.lyx


Convert LyX document to Rich Text Format (RTF) file:

    lyx2rtf simple.lyx


Convert LyX document to text file:

    lyx2txt simple.lyx



To-Do list
----------

- Source folder path handling
- Fix included child document in a standard layout issue
- Add LyX Note support
- Gracefully ignore unknown LyX structure and commands
- Add more LyX commands
- Check if it runs in Python 3



License
-------

See the file LICENSE for license-related information.



Author
------

Will Tang


