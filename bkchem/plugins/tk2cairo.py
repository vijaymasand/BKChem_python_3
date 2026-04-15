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


import cairo
import tkinter.font as tkFont
from ..oasa import transform
from ..oasa import geometry
import math
from .. import misc
import string


class tk2cairo:


  _caps = {'butt': cairo.LINE_CAP_BUTT,
           'round': cairo.LINE_CAP_ROUND,
           'projecting': cairo.LINE_CAP_SQUARE}


  _font_remap = {'helvetica': 'Arial',
                 'times': 'Times New Roman'}

  _joins = {'round': cairo.LINE_JOIN_ROUND,
            'miter': cairo.LINE_JOIN_MITER,
            'bevel': cairo.LINE_JOIN_BEVEL}


  def __init__( self, text_to_curves=False):
    self.text_to_curves = text_to_curves
    self._font_size_remap_cache = {}


  def export_to_cairo( self, tk_canvas, cairo_context, transformer=None):
    self.context = cairo_context
    self.paper = tk_canvas
    if not transformer:
      self.transformer = self.prepare_dumb_transformer()
    else:
      self.transformer = transformer
    self.width_scaling = self.transformer.get_scaling()
    self.draw_document()
    



  def set_cairo_color( self, color):
    if not color:
      self.context.set_source_rgba( 0,0,0,1)
      return False
    else:
      colors = self.paper.winfo_rgb( color)
      self.context.set_source_rgb( *map( lambda x: x/65535.0, colors))
      return True


  def prepare_dumb_transformer( self):
    tr = transform.transform()
    tr.set_scaling( 1)
    return tr


  def p2c_width( self, w):
    """converts a paper width to canvas width using the value of self.width_scaling"""
    return self.width_scaling * w




  def draw_document( self):
    # initial values
    self.context.set_fill_rule( cairo.FILL_RULE_EVEN_ODD)
    self.context.set_antialias( cairo.ANTIALIAS_BEST)
    # the conversion function for coordinates
    for item in self.paper.find_all():
      if not "no_export" in self.paper.gettags( item):
        method = "_draw_" + self.paper.type( item)
        if not hasattr( self, method):
          print("method to draw %s is not implemented" % self.paper.type( item))
        else:
          getattr( self, method)( item)
    self.context.show_page()



  def _draw_line( self, item):
    if self.paper.itemcget( item, 'fill') != '':
      # arrows at first as they make the lines bellow them shorter
      start = None
      end = None
      arrows = self.paper.itemcget( item, 'arrow')
      if arrows != "none":
        color = self.paper.itemcget( item, 'fill')
        coords = self.paper.coords( item)
        if arrows in ("last", "both"):
          end = self._create_arrow( self.paper.itemcget( item, 'arrowshape'), coords[-4:-2], coords[-2:], color)
        if arrows in ("first", "both"):
          start = self._create_arrow( self.paper.itemcget( item, 'arrowshape'), coords[2:4], coords[0:2], color)

      coords = self.transformer.transform_xy_flat_list( self.paper.coords( item))
      if start:
        coords[0] = start[0]
        coords[1] = start[1]
      if end:
        coords[-2] = end[0]
        coords[-1] = end[1]

      # cap style
      cap = self.paper.itemcget( item, 'capstyle')
      self.context.set_line_cap( self._caps[ cap])
      # join style
      join = self.paper.itemcget( item, 'joinstyle')
      self.context.set_line_join( self._joins[ join])
      # color
      is_visible = self.set_cairo_color( self.paper.itemcget( item, 'fill'))
      # line width
      width = self.p2c_width( float( self.paper.itemcget( item, 'width')))
      self.context.set_line_width( width)
      # the path itself 
      cs = self._flat_list_to_list_of_tuples( coords)
      if self.paper.itemcget( item, 'smooth') != "0":
        # smooth lines
        xycoords = self._flat_list_to_list_of_tuples( coords)
        beziers = geometry.tkspline_to_cubic_bezier( xycoords)
        for bez in beziers:
          self._create_cairo_curve( bez, closed=False)
      else:
        self._create_cairo_path( cs, closed=False)
      # stroke it
      if is_visible:
        self.context.stroke()
    else:
      pass #transparent things


  def _draw_text( self, item):
    text = str( self.paper.itemcget( item, 'text'))
    x1, y1, x2, y2 = self.paper.bbox( item)
    x1, y1, x2, y2 = self.transformer.transform_4( (x1+1, y1, x2-2, y2))
    afont = tkFont.Font( font=self.paper.itemcget( item, 'font'))
    conf = afont.config()
    font_family = conf['family']
    slant =  'italic' in conf['slant'] and cairo.FONT_SLANT_ITALIC or cairo.FONT_SLANT_NORMAL
    weight = 'bold' in conf['weight'] and cairo.FONT_WEIGHT_BOLD or cairo.FONT_WEIGHT_NORMAL

    # color
    is_visible = self.set_cairo_color( self.paper.itemcget( item, 'fill'))
    # helvetica which is often used does not work for me - therefore I use remap
    font_name = self._font_remap.get( font_family, font_family)
    self.context.select_font_face( font_name, slant, weight)

    # here we compute the font_size so that it matches what is on the screen
    # it the text is short, we use scaling based on some sample text, otherwise we compute it exactly for the string
    if len( text) <= 5:
      cairo_size = self._get_cairo_font_size( afont)
    else:
      cairo_size = self._compute_cairo_font_size( afont, text=text)
    self.context.set_font_size( cairo_size)

    xbearing, ybearing, width, height, x_advance, y_advance = self.context.text_extents( text)
    y = max(y1,y2)- self.transformer.get_scaling_xy()[1] * afont.metrics()['descent'] # * cairo_size / conf['size']
    if is_visible:
      if self.text_to_curves:
        self.context.new_path()
        self.context.move_to( x1 - (width - x2 + x1)/2 - xbearing, y)
        self.context.text_path( text)
        self.context.fill()
      else:
        self.context.move_to( x1 - (width - x2 + x1)/2 - xbearing, y)
        self.context.show_text( text)




  def _draw_rectangle( self, item):
    coords = self.transformer.transform_4( self.paper.coords( item))
    outline = self.paper.itemcget( item, 'outline')
    fill = self.paper.itemcget( item, 'fill')
    width = self.p2c_width( float( self.paper.itemcget( item, 'width')))
    x1, y1, x2, y2 = coords
    self.context.set_line_join( cairo.LINE_JOIN_MITER)
    self.context.rectangle( x1, y1, x2-x1, y2-y1)
    is_visible = self.set_cairo_color( fill)
    if is_visible:
      self.context.fill_preserve()
    is_visible = self.set_cairo_color( outline)
    if is_visible:
      self.context.set_line_width( width)
      self.context.stroke()
    else:
      self.context.new_path()

    
    
  def _draw_polygon( self, item):
    coords = self.transformer.transform_xy_flat_list( self.paper.coords( item))
    outline = self.paper.itemcget( item, 'outline')
    fill = self.paper.itemcget( item, 'fill')
    width = self.p2c_width( float( self.paper.itemcget( item, 'width')))
    cs = self._flat_list_to_list_of_tuples( coords)

    # join style
    join = self.paper.itemcget( item, 'joinstyle')
    self.context.set_line_join( self._joins[ join])

    self._create_cairo_path( cs, closed=True)
    is_visible = self.set_cairo_color( fill)
    if is_visible:
      self.context.fill_preserve()
    is_visible = self.set_cairo_color( outline)
    if is_visible:
      self.context.set_line_width( width)
      self.context.stroke()
    else:
      self.context.new_path()
    

  def _draw_oval( self, item):
    coords = self.transformer.transform_4( self.paper.coords( item))
    outline = self.paper.itemcget( item, 'outline')
    fill = self.paper.itemcget( item, 'fill')
    width = self.p2c_width( float( self.paper.itemcget( item, 'width')))
    x1, y1, x2, y2 = coords
    w = x2 - x1
    h = y2 - y1
    # save the context - we are going to use custom transform for the oval
    self.context.save()
    self.context.new_path()
    self.context.translate( x1+w/2, y1+h/2)
    self.context.scale( w/2.0, h/2.0)
    self.context.arc( 0, 0, 1, 0, 2 * math.pi)
    # restore the context to its previous state
    self.context.restore()
    # draw it
    is_visible = self.set_cairo_color( fill)
    if is_visible:
      self.context.fill_preserve()
    is_visible = self.set_cairo_color( outline)
    if is_visible:
      self.context.set_line_width( width)
      self.context.stroke()
    else:
      self.context.new_path()

    


  # other than drawing private methods

  def _create_arrow( self, shape, start, to, color):
    """creates an arrow with 'shape' pointing from 'start' to 'to' filled with 'color'
    and returns x, y - where the to should be to not to overlay the arrow"""
    a, b, c = map( float, shape.split())
    points = [a,0, a-b,c, 0,0, a-b,-c]
    ang = geometry.clockwise_angle_from_east( to[0]-start[0], to[1]-start[1])
    tr = transform.transform()
    tr.set_move( -a, 0)
    tr.set_rotation( ang)
    tr.set_move( to[0], to[1])
    points = tr.transform_xy_flat_list( points)
    points = self.transformer.transform_xy_flat_list( points)
    points = self._flat_list_to_list_of_tuples( points)

    self.context.set_line_join( cairo.LINE_JOIN_MITER)
    self._create_cairo_path( points, closed=True)
    is_visible = self.set_cairo_color( color)
    if is_visible:
      self.context.fill()

    return points[1]



  def _flat_list_to_list_of_tuples( self, coords):
    i = 0
    cs = []
    for c in coords:
      if i == 0:
        x = c
        i = 1
      else:
        cs.append( (x, c))
        i = 0
    return cs



  def _create_cairo_path( self, points, closed=False):
    x, y = points.pop( 0)
    self.context.move_to( x, y)
    for (x,y) in points:
      self.context.line_to( x, y)
    if closed:
      self.context.close_path()


  def _create_cairo_curve( self, points, closed=False):
    x1, y1, x2, y2, x3, y3, x4, y4 = points
    self.context.move_to( x1, y1)
    self.context.curve_to( x2, y2, x3, y3, x4, y4)
    if closed:
      self.context.close_path()


  # the following methods deal with font_size remapping between cairo and Tk
  def _get_cairo_font_size( self, tk_font):
    conf = tk_font.config()
    family = conf['family']
    tk_font_size = conf['size']
    if family in self._font_size_remap_cache:
      if tk_font_size in self._font_size_remap_cache[family]:
        return self._font_size_remap_cache[family][tk_font_size]
    else:
      self._font_size_remap_cache[family] = {}
    cairo_size = self._compute_cairo_font_size( tk_font)
    self._font_size_remap_cache[family][tk_font_size] = cairo_size
    return cairo_size


  def _compute_cairo_font_size( self, tk_font, text=""):
    if text:
      test_string = text
    else:
      test_string = string.ascii_letters + string.punctuation
    tk_length = self.p2c_width( tk_font.measure( test_string))
    cairo_size = self.p2c_width( tk_font.config()['size'])
    self.context.set_font_size( cairo_size)
    for i in range(2): # two iterations should be enough
      xbearing, ybearing, width, height, x_advance, y_advance = self.context.text_extents( test_string)
      cairo_size *= tk_length/width
      self.context.set_font_size( cairo_size)
    return cairo_size
    
    




