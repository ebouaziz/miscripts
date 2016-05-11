#!/usr/bin/env python
# -*- coding: utf8 -*-

# Generate a PNG thumbnail from the first page of a PDF file

from wand.image import Image

with Image(filename="/Users/eblot/Downloads/page.pdf") as img:
     img.resize(140, 200, 'lanczos2sharp')
     img.save(filename="/Users/eblot/Desktop/temp.png")
