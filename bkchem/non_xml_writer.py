#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#     Copyright (C) 2002-2009 Beda Kosata <beda@zirael.org>

#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     Complete text of GNU GPL can be found in the file gpl.txt in the
#     main directory of the program

#--------------------------------------------------------------------------
#
#
#
#--------------------------------------------------------------------------

"""provides basic class(es) for exporting to non-XML formates
(bitmaps or text oriented formats)"""

__all__ = ['enabled','Bitmap_writer']

from . import import_checker
# try to import PIL
if import_checker.PIL_available:
  if import_checker.PIL_prefix:
    import PIL.ImageDraw as ImageDraw, PIL.Image as Image #, PIL.ImageFont as ImageFont
  else:
    import Image, ImageDraw #, ImageFont
else:
  enabled = 0

import operator
from io import StringIO

def RGB_color( r, g, b):
  """converts 3 RGB values to one for use in PIL.Image"""
  return r*65536+g*256+b

class Bitmap_writer:
  """class to export to bitmap formates"""
  def __init__( self, paper, mode='RGB'):
    self.paper = paper
    self.image = Image.new( mode, (int(self.paper.cget('width')), int(self.paper.cget('height'))), RGB_color( 255, 255, 255))
    self.draw = ImageDraw.Draw( self.image)
    self.fill_image()

  def fill_image( self):
    for item in self.paper.find_all():
      if self.paper.type( item) == "line":
        self.draw.line( self.paper.coords( item), fill=0)
      elif self.paper.type( item) == "text":
        pass
        #font = ImageFont.load( '../fonts/helvR10.pil')
        #self.draw.text( self.paper.coords( item), self.paper.itemcget( item, 'text'), font=font, fill=0)
        

  def write_image( self, name):
    del self.draw
    self.image.save( name)
    del self.image

