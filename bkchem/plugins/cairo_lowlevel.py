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


from . import plugin
from .tk2cairo import tk2cairo
from ..oasa import transform
import cairo


from ..singleton_store import Screen, Store
import gettext
_ = gettext.gettext


class cairo_exporter( plugin.exporter):

  def __init__( self, paper, converter_class=None, attrs=None):
    """converter_class is the class used for convert, it is tk2piddle or its derivative;
    attrs are passed to converter_class on init"""
    self.paper = paper
    self.attrs = attrs or {}
    if not converter_class:
      self.converter_class = tk2piddle
    else:
      self.converter_class = converter_class



  def init_surface( self):
    """to be overriden; makes use of self.pagesize and self.filename"""
    pass


  def init_context( self):
    """to be overriden; should be called after init_surface"""
    return cairo.Context( self.surface)



  def save( self):
    """to be overriden; makes use of self.filename"""
    pass


  def get_scaling( self, x, y):
    """x and y are the original sizes of the drawing"""
    return 1, 1



  def on_begin( self, scaling=None):
    self.paper.unselect_all()
    if self.paper.get_paper_property( 'crop_svg'):

      if len( self.paper.find_all()) <= 1: # background only
        Store.log( _('There is nothing to export. If you want to export an empty paper disable cropping of the drawing in the File/Properties menu.'), message_type="error")
        return 0

      x1, y1, x2, y2 = self.paper.get_cropping_bbox()
      dx = x2-x1
      dy = y2-y1
      scalex, scaley = scaling or self.get_scaling( dx, dy)
      if not scalex:
        # the setting of scaling was canceled
        return 0

      self.transformer = transform.transform()
      self.transformer.set_move( -x1, -y1)
      self.transformer.set_scaling_xy( scalex, scaley)
    else:
      dx = Screen.mm_to_px( self.paper._paper_properties['size_x'])
      dy = Screen.mm_to_px( self.paper._paper_properties['size_y'])
      scalex, scaley = scaling or self.get_scaling( dx, dy)
      if not scalex:
        # the setting of scaling was canceled
        return 0

      self.transformer = transform.transform()
      self.transformer.set_scaling_xy( scalex, scaley)

    x1, y1, x2, y2 = self.transformer.transform_4( (0, 0, dx, dy))
    self.pagesize = tuple( map( round, (x2-x1, y2-y1)))
    self.attrs['text_to_curves'] = False
    self.converter = self.converter_class( **self.attrs)
    return 1


  def write_to_file( self, name):
    self.filename = name
    self.surface = self.init_surface()
    self.context = self.init_context()
    self.converter.export_to_cairo( self.paper, self.context, transformer=self.transformer)
    self.save()

