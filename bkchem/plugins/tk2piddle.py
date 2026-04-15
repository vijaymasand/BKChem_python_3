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


from .piddle import piddle
import tkinter.font as tkFont
from ..oasa.oasa import transform
from ..oasa.oasa import geometry


class tk2piddle:

  # this is useful for tweaking the output
  text_x_shift = 0.7

  def __init__( self):
    pass


  def export_to_piddle_canvas( self, tk_canvas, piddle_canvas, transformer=None):
    self.canvas = piddle_canvas
    self.paper = tk_canvas
    self.convert = self.paper_to_canvas_coord
    if not transformer:
      self.transformer = self.prepare_dumb_transformer()
    else:
      self.transformer = transformer
    self.draw_document()
    self.canvas.flush()



  def paper_to_canvas_color( self, color):
    if not color:
      return piddle.transparent
    colors = self.paper.winfo_rgb( color)
    return piddle.Color( *map( lambda x: x/65535.0, colors))



  def paper_to_canvas_coord( self, x):
    dpi = self.paper.winfo_fpixels( '254m')/10.0
    return 72*x/dpi


  def prepare_dumb_transformer( self):
    tr = transform.transform()
    tr.set_scaling( self.paper_to_canvas_coord( 1))
    return tr



  def draw_document( self):
    # the conversion function for coordinates
    for item in self.paper.find_all():
      if not "no_export" in self.paper.gettags( item):
        method = "_draw_" + self.paper.type( item)
        if not hasattr( self, method):
          print("method to draw %s is not implemented" % self.paper.type( item))
        else:
          getattr( self, method)( item)



  def _draw_line( self, item):
    if self.paper.itemcget( item, 'fill') != '':
      # arrows at first as they make the lines bellow them shorter
      start = None
      end = None
      arrows = self.paper.itemcget( item, 'arrow')
      if arrows != "none":
        color = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
        coords = self.paper.coords( item)
        if arrows in ("last", "both"):
          end = self._create_arrow( self.paper.itemcget( item, 'arrowshape'), coords[-4:-2], coords[-2:], color)
        if arrows in ("first", "both"):
          start = self._create_arrow( self.paper.itemcget( item, 'arrowshape'), coords[2:4], coords[0:2], color)

      coords = self.transformer.transform_xy_flat_list( self.paper.coords( item))
      coords = [int(c) for c in coords]
      if start:
        coords[0] = start[0]
        coords[1] = start[1]
      if end:
        coords[-2] = end[0]
        coords[-1] = end[1]
   
      if len( coords) > 4:
        if self.paper.itemcget( item, 'smooth') != "0":   #smooth is spline 
          outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
          fill = piddle.transparent
          width = self.convert( float( self.paper.itemcget( item, 'width')))
          xycoords = self._flat_list_to_list_of_tuples( coords)
          beziers = geometry.tkspline_to_cubic_bezier( xycoords)
          for bez in beziers:
            x1, y1, x2, y2, x3, y3, x4, y4 = [int(c) for c in bez]
            self.canvas.drawCurve(x1, y1, x2, y2, x3, y3, x4, y4, edgeColor=outline, edgeWidth=width, fillColor=fill, closed=0)
        
        else:
          # polyline
          outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
          fill = piddle.transparent
          width = self.convert( float( self.paper.itemcget( item, 'width')))
          cs = self._flat_list_to_list_of_tuples( coords)
          self.canvas.drawPolygon( cs, edgeColor=outline, edgeWidth=width, fillColor=fill, closed=0)
      else:
        # simple line
        fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
        width = self.convert( float( self.paper.itemcget( item, 'width')))
        x1, y1, x2, y2 = coords
        self.canvas.drawLine( x1, y1, x2, y2, color=fill, width=width)
    else:
      pass #transparent things


  def _draw_text( self, item):
    text = self.paper.itemcget( item, 'text')
    x1, y1, x2, y2 = self.transformer.transform_4( self.paper.bbox( item))
    afont = tkFont.Font( font=self.paper.itemcget( item, 'font'))
    conf = afont.config()
    font_family = conf['family']
    # Scale font to match the transformer's scaling (includes zoom and DPI)
    orig_size = conf['size']
    tr_scale = self.transformer.get_scaling() if hasattr(self.transformer, 'get_scaling') else 1.0
    font_size = int(orig_size * tr_scale)
    italic = 'italic' in conf['slant']
    bold = 'bold' in conf['weight']
    y = int(max(y1,y2) - self.convert(afont.metrics()['descent']))
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    font = piddle.Font( face=font_family, size=font_size, bold=bold, italic=italic)
    self.canvas.drawString( text, int(x1+self.convert( self.text_x_shift)), y, font=font, color=fill)


  def _draw_rectangle( self, item):
    coords = self.transformer.transform_4( self.paper.coords( item))
    coords = [int(c) for c in coords]
    outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'outline'))
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    width = self.convert( float( self.paper.itemcget( item, 'width')))
    x1, y1, x2, y2 = coords
    if fill != piddle.transparent or outline != piddle.transparent:
      self.canvas.drawRect( x1, y1, x2, y2, edgeColor=outline, edgeWidth=width, fillColor=fill)
    
    
  def _draw_polygon( self, item):
    coords = self.transformer.transform_xy_flat_list( self.paper.coords( item))
    coords = [int(c) for c in coords]
    outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'outline'))
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    width = self.convert( float( self.paper.itemcget( item, 'width')))
    cs = self._flat_list_to_list_of_tuples( [int(c) for c in coords])
    self.canvas.drawPolygon( cs, edgeColor=outline, edgeWidth=width, fillColor=fill, closed=1)
    

  def _draw_oval( self, item):
    coords = self.transformer.transform_4( self.paper.coords( item))
    outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'outline'))
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    width = self.convert( float( self.paper.itemcget( item, 'width')))
    x1, y1, x2, y2 = [int(c) for c in coords]
    self.canvas.drawEllipse( x1, y1, x2, y2, edgeColor=outline, edgeWidth=width, fillColor=fill)
    


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
    tr.set_move( int(to[0]), int(to[1]))
    points = tr.transform_xy_flat_list( points)
    points = self.transformer.transform_xy_flat_list( points)
    points = [int(c) for c in points]
    points = self._flat_list_to_list_of_tuples( points)
    self.canvas.drawPolygon( points, edgeColor=color, edgeWidth=0, fillColor=color, closed=1)    
    return points[2]



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







class tk2piddle_pdf( tk2piddle):
  """specialized class to make use of available additional functions of the piddle PDF
  interface (and pdfgen)"""

  _caps = {'butt': 0,
           'round': 1,
           'projecting': 2}

  def _draw_line( self, item):
    cap = self.paper.itemcget( item, 'capstyle')
    self.canvas.pdf.setLineCap( self._caps[ cap])
    tk2piddle._draw_line( self, item)
  




class tk2piddle_ps( tk2piddle):
  """specialized class to make use of available additional functions of the piddle PS
  interface"""

  _caps = {'butt': 0,
           'round': 1,
           'projecting': 2}

  def _draw_line( self, item):
    cap = self.paper.itemcget( item, 'capstyle')
    self.canvas.setLineCap( self._caps[ cap])
    tk2piddle._draw_line( self, item)
