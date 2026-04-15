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


"""provides exporters to XML formats (SVG for now)"""

from .oasa import geometry
import xml.dom.minidom as dom
from xml.dom.minidom import Document
import re
from . import data
from . import dom_extensions
import operator
from . import dom_extensions
import os
from .tuning import Tuning
from .ftext import ftext as ftext_class

from .singleton_store import Screen


class XML_writer:
  """This is abstract class that serves as parent for specialized writters - CDML, SVG ...
  construct_dom_tree method is virtual and should be overriden"""
  def __init__( self, paper):
    self.paper = paper
    self.document = Document()
    self.top = None # top level element
    #self.construct_dom_tree()

  def construct_dom_tree( self, top_levels):
    pass

  def write_xml_to_file( self, file):
    "writes XML representation of entire 'paper' to 'file'"
    pass

  def get_nicely_formated_document( self):
    """returns text form of self.document indented with dom_extensions.safe_indent"""
    dom_extensions.safe_indent( self.top, dont_indent=("text","ftext","user-data"))
    return self.document.toxml()

# Tkinter states that it takes font sizes in pt. However this is not true (as for python 2.2.2)
# therefor there is this variable to quickly change the settings and control the SVG output
pt_or_px="pt"


class SVG_writer( XML_writer):

  def __init__( self, paper):
    XML_writer.__init__( self, paper)
    self.full_size = not (paper.get_paper_property( 'crop_svg') and len( paper.stack))
    # shortcut for color conversion
    self.cc = self.paper.any_color_to_rgb_string
    # the conversion function for coordinates
    self.convert = lambda x: "%.2f" % x

    

  def construct_dom_tree( self, top_levels):
    """constructs the SVG dom from all top_levels"""
    # the constants
    border_size = self.paper.get_paper_property( 'crop_margin')

    # converter
    px_to_cm_txt = lambda x: Screen.px_to_text_with_unit( x, unit="cm", round_to=5)
    px_to_mm_txt = lambda x: Screen.px_to_text_with_unit( x, unit="mm", round_to=5)

    # the code
    self._id = 0
    doc = self.document
    self.top = dom_extensions.elementUnder( doc, "svg", attributes=(("xmlns", "http://www.w3.org/2000/svg"),
                                                                    ("version", "1.0")))
    if self.full_size:
      sx = self.paper.get_paper_property( 'size_x')
      sy = self.paper.get_paper_property( 'size_y')
      dom_extensions.setAttributes( self.top, (("width", '%fmm' % sx),
                                               ("height", '%fmm' % sy),
                                               ('viewBox', '0 0 %d %d' % (Screen.mm_to_px(sx), Screen.mm_to_px(sy)))))
    else:
      items = list( self.paper.find_all())
      items.remove( self.paper.background)
      x1, y1, x2, y2 = self.paper.list_bbox( items)
      w = px_to_mm_txt( x2 -x1 +2*border_size)
      h = px_to_mm_txt( y2 -y1 +2*border_size)
      bx2, by2 = x2-x1+2*border_size, y2-y1+2*border_size
      dom_extensions.setAttributes( self.top, (("width", w),
                                               ("height", h),
                                               ("viewBox",'0 0 %d %d' % ( bx2, by2))))
    self.group = dom_extensions.elementUnder( self.top, 'g',
                                              (('font-size', '12pt'),
                                               ('font-family', 'Helvetica'),
                                               ('stroke-linecap', 'round')))
    if not self.full_size:
      self.group.setAttribute( 'transform', 'translate(%d,%d)' % (-x1+border_size, -y1+border_size))
      
    # sort the top_levels according to paper.stack
    cs = []
    for c in self.paper.stack:
      if c in top_levels:
        cs.append( c)
    for o in cs:
      if o.object_type == 'molecule':
        for b in o.bonds:
          self.add_bond( b)
        for a in o.atoms:
          self.add_atom( a)
      elif o.object_type == 'arrow':
        self.add_arrow( o)
      elif o.object_type == 'text':
        self.add_text( o)
      elif o.object_type == 'plus':
        self.add_plus( o)
      elif o.object_type in data.vector_graphics_types:
        if o.object_type == 'rect':
          self.add_rect( o)
        elif o.object_type == 'oval':
          self.add_oval( o)
        elif o.object_type == 'polygon':
          self.add_polygon( o)
        elif o.object_type == 'polyline':
          self.add_polyline( o)
          

    
  def add_bond( self, b):
    """adds bond item to SVG document"""
    if not b.item:
      return
    line_width = (b.type == 'b') and b.wedge_width or b.type != 'w' and b.line_width or 1.0
    l_group = dom_extensions.elementUnder( self.group, 'g',
                                           (('stroke-width', str( line_width)),
                                            ('stroke', self.cc( b.line_color))))
    if sum( [int( a.show) for a in b.atoms]) == 2:
      # both atoms are visible, it does not look good with round caps
      l_group.setAttribute('stroke-linecap', 'butt')

    line_items, items = b.get_exportable_items()
    # export itself
    if b.type in 'nbhd':
      for i in items:
        x1, y1, x2, y2 = self.paper.coords( i)
        line = dom_extensions.elementUnder( l_group, 'line',
                                            (( 'x1', self.convert( x1)),
                                             ( 'y1', self.convert( y1)),
                                             ( 'x2', self.convert( x2)),
                                             ( 'y2', self.convert( y2))))
    elif b.type == 'o':
      for i in items:
        x1, y1, x2, y2 = self.paper.coords( i)
        dom_extensions.elementUnder( l_group, 'ellipse',
                                     (( 'cx', self.convert( 0.5*(x2+x1))),
                                      ( 'cy', self.convert( 0.5*(y2+y1))),
                                      ( 'rx', self.convert( 0.5*(x2-x1))),
                                      ( 'ry', self.convert( 0.5*(y2-y1))),
                                      ( 'stroke-width', '1.0')))
    elif b.type == 'w':
      for i in items:
        coords = self.paper.coords( b.item)
        line = dom_extensions.elementUnder( l_group, 'polygon',
                                            (( 'fill', self.cc( b.line_color)),
                                             ( 'stroke', self.cc( b.line_color)),
                                             ( 'points', list_to_svg_points( coords))))
    elif b.type in 'h':
      for i in items:
        for p in i:
          x1, y1, x2, y2 = self.paper.coords( p)
          line = dom_extensions.elementUnder( l_group, 'line',
                                              (( 'x1', self.convert( x1)),
                                               ( 'y1', self.convert( y1)),
                                               ( 'x2', self.convert( x2)),
                                               ( 'y2', self.convert( y2))))
    elif b.type == 'a':
      for i in items:
        coords = self.paper.coords( i)
        points = ' '.join( map( self.convert, coords))
        line = dom_extensions.elementUnder( l_group, 'polyline',
                                            (( 'points', points),
                                             ( 'fill', 'none')))
    # the line items for simple_double
    for i in line_items:
      x1, y1, x2, y2 = self.paper.coords( i)
      line = dom_extensions.elementUnder( l_group, 'line',
                                          (( 'x1', self.convert( x1)),
                                           ( 'y1', self.convert( y1)),
                                           ( 'x2', self.convert( x2)),
                                           ( 'y2', self.convert( y2)),
                                           ( 'stroke-width', str( b.line_width))))

            
  def add_arrow( self, a):
    """adds arrow item to SVG document"""
    i = self._id
    for item in a.items:
      # polygons (arrow heads, etc.)
      if self.paper.type( item) == "polygon":
        points = geometry.coordinate_flat_list_to_xy_tuples( self.paper.coords( item))
        ps = " ".join( ["%.2f,%.2f" % (x,y) for (x,y) in points])
        a_color = self.paper.itemcget( item, "fill")
        l_color = self.paper.itemcget( item, "outline")
        poly = dom_extensions.elementUnder( self.group, 'polygon',
                                            (( 'points', ps),
                                             ( 'stroke-width', '1'),
                                             ( 'fill-rule', 'evenodd'),
                                             ( 'fill', self.cc( l_color)),
                                             ( 'stroke', self.cc( l_color))))
      # polylines - standard arrows
      elif self.paper.type( item) == "line":
        # the pins
        line_pin = a._pins.index( self.paper.itemcget( item, 'arrow'))
        if line_pin == 1 or line_pin == 3:
          d1, d2, d3 = map( int, self.paper.itemcget( item, "arrowshape").split())
          defs = dom_extensions.elementUnder( self.group, 'defs')
          arrow_point = dom_extensions.elementUnder( defs, 'marker', (('id','Arrow'+str(i)),('refX',str(d2)),('refY',str(d3)),
                                                                ('markerUnits','userSpaceOnUse'),
                                                                ('markerWidth',str(d2)),('markerHeight',str(2*d3)),
                                                                ('orient','auto'),
                                                                ('stroke', self.cc( a.line_color)),
                                                                ('fill', self.cc( a.line_color))))
          dom_extensions.elementUnder( arrow_point, 'path', (('d', 'M %d %d L 0 0 L %d %d L 0 %d z'%(d2, d3, d2-d1, d3, 2*d3)),))
        if line_pin == 2 or line_pin == 3:
          d1, d2, d3 = map( int, self.paper.itemcget( item, "arrowshape").split())
          defs = dom_extensions.elementUnder( self.group, 'defs')
          arrow_point = dom_extensions.elementUnder( defs, 'marker', (('id','ArrowBack'+str(i)),('refX','0'),('refY',str(d3)),
                                                                ('markerUnits','userSpaceOnUse'),
                                                                ('markerWidth',str(d2)),('markerHeight',str(2*d3)),
                                                                ('orient','auto'),
                                                                ('stroke', self.cc( a.line_color)),
                                                                ('fill', self.cc( a.line_color))))
          dom_extensions.elementUnder( arrow_point, 'path', (('d', 'M 0 %d L %d 0 L %d %d L %d %d z'%(d3, d2, d1, d3, d2, 2*d3)),))
        # the item
        if self.paper.itemcget( item, "smooth") != "0" and len( self.paper.coords( item)) > 4:
          # spline
          points = geometry.coordinate_flat_list_to_xy_tuples( self.paper.coords( item))
          beziers = geometry.tkspline_to_quadratic_bezier( points)
          ps = 'M%.2f,%.2f Q%.2f,%.2f %.2f,%.2f' % (beziers[0])
          for bez in beziers[1:]:
            ps += 'Q%.2f,%.2f %.2f,%.2f ' % (bez[2:])
          line = dom_extensions.elementUnder( self.group, 'path',
                                              (( 'd', ps),
                                               ( 'stroke-width', str( a.line_width)),
                                               ( 'fill', 'none'),
                                               ( 'stroke', self.cc( a.line_color))))
        else:
          # normal line
          points = geometry.coordinate_flat_list_to_xy_tuples( self.paper.coords( item))
          ps = " ".join( ["%.2f,%.2f" % (x,y) for (x,y) in points])
          line = dom_extensions.elementUnder( self.group, 'polyline',
                                              (( 'points', ps),
                                               ( 'stroke-width', str( a.line_width)),
                                               ( 'fill', 'none'),
                                               ( 'stroke', self.cc( a.line_color))))
        if line_pin == 1 or line_pin == 3:
          line.setAttribute( 'marker-end','url(#Arrow'+str(i)+')')
        if line_pin == 2 or line_pin == 3:
          line.setAttribute( 'marker-start','url(#ArrowBack'+str(i)+')')
        self._id += 1


  def add_text( self, t):
    """adds text item to SVG document"""
    x1, y1 = t.get_xy()
    x, y, x2, y2 = t.ftext.bbox( complete=True)
    _x, y, _x2, y2 = t.ftext.bbox( complete=False)
    if t.area_color:
      # it is not needed to export the rectangle in case its transparent
      dom_extensions.elementUnder( self.group, 'rect',
                                   (( 'x', self.convert( x)),
                                    ( 'y', self.convert( y)),
                                    ( 'width', self.convert( x2-x)),
                                    ( 'height', self.convert( y2-y)),
                                    ( 'fill', self.cc( t.area_color)),
                                    ( 'stroke', self.cc( t.area_color))))
    y1 += (y2-y)/4.0
    x += 2 ## hack to compensate for the wrong measuring of text
    text = ftext_dom_to_svg_dom( dom.parseString( t.ftext.sanitized_text()), self.document, replace_minus=t.paper.get_paper_property('replace_minus'))
    dom_extensions.setAttributes( text, (( "x", self.convert( x)),
                                         ( "y", self.convert( y1)),
                                         ( "font-family", t.font_family),
                                         ( "font-size", '%d%s' % (t.font_size, pt_or_px)),
                                         ( 'fill', self.cc( t.line_color)),
                                         ( 'textLength', "%d" % (x2-x+len( [1 for i in t.xml_ftext if i=="-" and t.paper.get_paper_property( 'replace_minus')])))))
    self.group.appendChild( text)

  def add_plus( self, p):
    """adds plus item to SVG document"""
    item = p.item
    x1, y1 = p.get_xy()
    x, y, x2, y2 = self.paper.bbox( item)
    if p.area_color:
      # it is not needed to export the rectangle in case its transparent
      dom_extensions.elementUnder( self.group, 'rect',
                                   (( 'x', self.convert( x)),
                                    ( 'y', self.convert( y)),
                                    ( 'width', self.convert( x2-x)),
                                    ( 'height', self.convert( y2-y)),
                                    ( 'fill', self.cc( p.area_color)),
                                    ( 'stroke', self.cc( p.area_color))))
    y1 += (y2-y)/4.0
    text = dom_extensions.textOnlyElementUnder( self.group, 'text', '+',
                                                (('font-size', "%d%s" % (p.font_size, pt_or_px)),
                                                 ('font-family', p.font_family),
                                                 ( "x", self.convert( x)),
                                                 ( "y", self.convert( round( y1))),
                                                 ( 'fill', self.cc( p.line_color))))

  def add_atom( self, a):
    """adds atom item to SVG document"""
    if a.show:
      item = a.selector
      x1, y1 = a.get_xy()
      x, y, x2, y2 = self.paper.bbox( item)
      if a.area_color != '':
        # it is not needed to export the rectangle in case its transparent
        dom_extensions.elementUnder( self.group, 'rect',
                                     (( 'x', self.convert( x)),
                                      ( 'y', self.convert( y)),
                                      ( 'width', self.convert( x2-x)),
                                      ( 'height', self.convert( y2-y)),
                                      ( 'fill', self.cc( a.area_color)),
                                      ( 'stroke', self.cc( a.area_color))))

      # some fine tuning 
      y1 += a.font.metrics('descent') + Tuning.SVG.text_y_shift
      x += Tuning.SVG.text_x_shift ## hack to compensate for the wrong measuring of text

      text = ftext_to_svg_dom( a.xml_ftext)
      dom_extensions.setAttributes( text, (( "x", self.convert( x)),
                                           ( "y", self.convert( y1)),
                                           ( "font-family", a.font_family),
                                           ( "font-size", '%d%s' % (a.font_size, pt_or_px)),
                                           ( 'fill', self.cc( a.line_color))))
      # set the text length but only for text longer than threshold
      if (x2-x) > 50:
        text.setAttribute( 'textLength', "%.1f" % (x2-x))
      self.group.appendChild( text)

    if hasattr( a, "marks"):
      for m in a.marks:
        self.group.appendChild( m.get_svg_element( self.document))




  def add_rect( self, o):
    x1, y1, x2, y2 = o.coords
    el = dom_extensions.elementUnder( self.group, 'rect',
                                      (( 'x', self.convert( x1)),
                                       ( 'y', self.convert( y1)),
                                       ( 'width', self.convert( x2-x1)),
                                       ( 'height', self.convert( y2-y1)),
                                       ( 'stroke-width', str( o.line_width))))

    el.setAttribute( 'fill', self.cc( o.area_color))
    el.setAttribute( 'stroke', self.cc( o.line_color))
      

    
  def add_oval( self, o):
    x1, y1, x2, y2 = o.coords
    el = dom_extensions.elementUnder( self.group, 'ellipse',
                                      (( 'cx', self.convert( (x2+x1)/2)),
                                       ( 'cy', self.convert( (y2+y1)/2)),
                                       ( 'rx', self.convert( (x2-x1)/2)),
                                       ( 'ry', self.convert( (y2-y1)/2)),
                                       ( 'stroke-width', str( o.line_width))))

    el.setAttribute( 'fill', self.cc( o.area_color))
    el.setAttribute( 'stroke', self.cc( o.line_color))


  def add_polygon( self, o):
    ps = ''
    for (x,y) in [p.get_xy() for p in o.points]:
      ps += '%.2f,%.2f ' % (x,y)
    poly = dom_extensions.elementUnder( self.group, 'polygon',
                                        (( 'points', ps),
                                         ( 'stroke-width', str( o.line_width)),
                                         ( 'fill-rule', 'evenodd')))

    poly.setAttribute( 'fill', self.cc( o.area_color))
    poly.setAttribute( 'stroke', self.cc( o.line_color))




  def add_polyline( self, o):
    # the item
    points = [p.get_xy() for p in o.points]
    if o.spline and len( o.points) > 2:
      # spline
      beziers = geometry.tkspline_to_quadratic_bezier( points)
      ps = 'M%.2f,%.2f Q%.2f,%.2f %.2f,%.2f' % (beziers[0])
      for bez in beziers[1:]:
        ps += 'Q%.2f,%.2f %.2f,%.2f ' % (bez[2:])
      line = dom_extensions.elementUnder( self.group, 'path',
                                          (( 'd', ps),
                                           ( 'stroke-width', str( o.line_width)),
                                           ( 'fill', 'none'),
                                           ( 'stroke', self.cc( o.line_color))))
    else:
      # normal line
      ps = ''
      for (x,y) in points:
        ps += '%.2f,%.2f ' % (x,y)
      poly = dom_extensions.elementUnder( self.group, 'polyline',
                                          (( 'points', ps),
                                           ( 'stroke-width', str( o.line_width)),
                                           ( 'fill', 'none'),
                                           ( 'stroke', self.cc( o.line_color))))



def list_to_svg_points( l):
  return ' '.join( ["%.2f" % x for x in l])


def ftext_to_svg_dom( ftext):
  fd = dom.parseString( ftext_class.sanitize_text( ftext)).childNodes[0]
  svg = dom.Document()
  return ftext_dom_to_svg_dom( fd, svg)


def ftext_dom_to_svg_dom( ftext, doc, add_to=None, replace_minus=False):
  if not add_to:
    element = doc.createElement( 'text')
  else:
    element = add_to

  if not ftext.nodeValue:
    name = ftext.nodeName
    # check if to add attributes to already existing element or create a new one
    if (not element.lastChild and element.nodeName == "tspan") or name == "ftext":
      my_svg = element
    else:
      my_svg = doc.createElement( 'tspan')
      element.appendChild( my_svg)

    # now put the attributes inside
    if name == 'b':
      dom_extensions.setAttributes( my_svg, (('font-weight', 'bold'),))
    elif name == 'i':
      dom_extensions.setAttributes( my_svg, (('font-style', 'italic'),))
    elif name == 'sup':
      dom_extensions.setAttributes( my_svg, (('baseline-shift', 'super'),('font-size','75%')))
    elif name == 'sub':
      dom_extensions.setAttributes( my_svg, (('baseline-shift', 'sub'),('font-size','75%')))

    # continue with the children
    for el in ftext.childNodes:
      ftext_dom_to_svg_dom( el, doc, add_to=my_svg)
  else:
    if replace_minus:
      element.appendChild( doc.createTextNode( ftext.nodeValue.replace( "-", chr( 8722))))
    else:
      element.appendChild( doc.createTextNode( ftext.nodeValue))

  return element
