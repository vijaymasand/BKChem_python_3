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





"""Openoffice Draw export plugin"""



# there is a problem with font sizes. It seems that OpenOffice does not distinguish

# between pt and px. Unfortunately it seems that the font sizes handling is also different

# in the Tcl/Tk 8.3.4 than in the version I have used before. Maybe I would have to switch

# to px sizes instead of pt sizes.





from . import plugin

import xml.dom.minidom as dom

from .. import dom_extensions as dom_ext

from .. import dom_extensions

import math

import operator

from .. import os_support

from ..oasa.oasa import geometry

from ..singleton_store import Screen
import gettext
_ = gettext.gettext

from functools import reduce





## DEFINITIONS



class OO_exporter( plugin.exporter):

  """Exports the drawing into OpenOffice Draw format (native for OO prior to 2.0),

note that this is not an ODF (Open Document Format) export."""



  doc_string = _("Exports the drawing into OpenOffice Draw format (native for OO prior to 2.0), note that this is not an ODF (Open Document Format) export.")



  def __init__( self, paper):

    self.paper = paper

    self.used_styles = []



  def on_begin( self):

    return 1

##     import tkinter.messagebox as tkMessageBox

##     yes = tkMessageBox.askyesno( _("Really export?"),

##                                  _('This plugin is not finished and will probably not work correctly.') + ' ' +

##                                  _('Proceed?'))

##     return yes



  def write_to_file( self, name):

    self.doc = dom.Document()

    out = self.doc

    root = dom_ext.elementUnder( out, 'office:document-content',

                                 (('office:class', 'drawing'),

                                  ('office:version', '1.0'),

                                  ('xmlns:draw', 'http://openoffice.org/2000/drawing'),

                                  ('xmlns:form', "http://openoffice.org/2000/form"),

                                  ('xmlns:office',"http://openoffice.org/2000/office"),

                                  ('xmlns:style',"http://openoffice.org/2000/style"),

                                  ('xmlns:svg',"http://www.w3.org/2000/svg"),

                                  ('xmlns:text',"http://openoffice.org/2000/text"),

                                  ('xmlns:fo',"http://www.w3.org/1999/XSL/Format")))



    self.styles_element = dom_ext.elementUnder( root, 'office:automatic-styles')

    # drawing page

    body = dom_ext.elementUnder( root, 'office:body')

    page = dom_ext.elementUnder( body, 'draw:page', (('draw:master-page-name','vychozi'),

                                                     ('draw:name', 'page1')))

    for o in self.paper.stack:

      if o.object_type == 'molecule':

        group = dom_ext.elementUnder( page, 'draw:g')

        for b in o.bonds:

          self.add_bond( b, group)

        for b in o.atoms:

          self.add_atom( b, group)

      elif o.object_type == 'arrow':

        self.add_arrow( o, page)

      elif o.object_type == 'text':

        self.add_text( o, page)

      elif o.object_type == 'plus':

        self.add_plus( o, page)

      elif o.object_type == 'rect':

        self.add_rect( o, page)

      elif o.object_type == 'oval':

        self.add_oval( o, page)

      elif o.object_type == 'polygon':

        self.add_polygon( o, page)



#    dom_ext.safe_indent( root)

    

    import tempfile

    # content file

    cfname = tempfile.mktemp()

    f = open( cfname, "wb")

    f.write( out.toxml().encode('utf-8'))

    f.close()

    # styles file

    sfname = tempfile.mktemp()

    f = open( sfname, "wb")

    f.write( self.create_styles_document().toxml().encode('utf-8'))

    f.close()

    import zipfile

    zip = zipfile.ZipFile( name, 'w', zipfile.ZIP_DEFLATED)

    manifest = os_support.get_path( 'oo_manifest.xml', 'template')

    if manifest:

      zip.write( os_support.get_path( 'oo_manifest.xml', 'template'), 'META-INF/manifest.xml')

      zip.write( cfname, 'content.xml')

      zip.write( sfname, 'styles.xml')

      zip.close()

    else:

      zip.close()

      raise plugin.export_exception( _("The manifest file not found in the plugin directory"))





  def add_bond( self, b, page):

    """adds bond item to page"""

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( b.line_color),

                        stroke_width=Screen.px_to_cm( b.line_width))

    style_name = self.get_appropriate_style_name( s)

    l_group = page

    # items to export

    line_items, items = b.get_exportable_items()



    # the export itself

    if b.type in 'nhd':

      for i in items:

        coords = map( Screen.px_to_cm, self.paper.coords( i))

        self.create_oo_line( coords, page, style_name)

    elif b.type == 'o':

      for i in items:

        x, y, x2, y2 = map( Screen.px_to_cm, self.paper.coords( i))

        size = Screen.px_to_cm( x2-x)

        dom_extensions.elementUnder( page, 'draw:ellipse',

                                     (( 'svg:x', '%fcm' %  x),

                                      ( 'svg:y', '%fcm' %  y),

                                      ( 'svg:width', '%fcm' %  size),

                                      ( 'svg:height', '%fcm' % size),

                                      ( 'draw:style-name', style_name)))

    elif b.type == 'b':

      # bold bonds width is determined by the wedge_width

      s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( b.line_color),

                          stroke_width=Screen.px_to_cm( b.wedge_width))

      b_style_name = self.get_appropriate_style_name( s)

      for i in items:

        coords = map( Screen.px_to_cm, self.paper.coords( i))

        self.create_oo_line( coords, page, b_style_name)

    elif b.type == 'w':

      s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( b.line_color),

                          fill_color=self.paper.any_color_to_rgb_string( b.line_color),

                          stroke_width=Screen.px_to_cm( b.line_width))

      style_name = self.get_appropriate_style_name( s)

      for i in items:

        coords = map( Screen.px_to_cm, self.paper.coords( i))

        point_array = []

        for i in range( 0, len( coords), 2):

          point_array.append( (coords[i], coords[i+1]))

        self.create_oo_polygon( point_array, page, style_name)

    elif b.type == 'a':

      s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( b.line_color),

                          stroke_width=Screen.px_to_cm( b.line_width))

      style_name = self.get_appropriate_style_name( s)

      for i in items:

        coords = self.paper.coords( i)

        points = []

        for j in range( 0, len( coords), 2):

          points.append( ( Screen.px_to_cm( coords[j]), Screen.px_to_cm(coords[j+1])))

        self.create_oo_polyline( points, page, style_name)

    # line_items

    for i in line_items:

      coords = map( Screen.px_to_cm, self.paper.coords( i))

      self.create_oo_line( coords, page, style_name)







  def add_atom( self, a, page):

    """adds atom to document"""

    if a.show:

      coords = map( Screen.px_to_cm, self.paper.coords( a.selector))

      # we need to use negative padding of the text because oo puts too much space above

      # and under text

      dy = abs( coords[3]-coords[1])

      ptop = -0.25*dy

      pbot = -0.2*dy

      gr_style = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( a.line_color),

                                 fill_color=self.paper.any_color_to_rgb_string( a.area_color),

                                 padding=(ptop,pbot))

      gr_style_name = self.get_appropriate_style_name( gr_style)

      para_style = paragraph_style( font_size='%dpx' % round(a.font_size*1), font_family=a.font_family,

                                    color=self.paper.any_color_to_rgb_string( a.line_color))

      para_style_name = self.get_appropriate_style_name( para_style)

      txt_style = text_style( font_size='%dpx' % round(a.font_size*1), font_family=a.font_family)

      txt_style_name = self.get_appropriate_style_name( txt_style)



      self.create_oo_text( '<ftext>%s</ftext>' % a.xml_ftext, coords, page, para_style_name, txt_style_name, gr_style_name)

    # marks

    for m in a.marks:

      if m:

        name = m.__class__.__name__

        if name == 'radical':

          self.add_radical_mark( m, page)

        elif name in ('biradical','dotted_electronpair'):

          self.add_radical_mark( m, page)

        elif name == 'electronpair':

          self.add_electronpair_mark( m, page)

        elif name == 'minus':

          self.add_plus_mark( m, page)

        elif name == 'plus':

          self.add_plus_mark( m, page)

        elif name in ("atom_number","oxidation_number","free_sites"):

          self.add_text_mark( m, page)

        elif name == "pz_orbital":

          self.add_orbital( m, page)



##       s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( m.outline),

##                           fill_color=self.paper.any_color_to_rgb_string( m.line_color),

##                           stroke_width=Screen.px_to_cm( o.line_width))

##       style_name = self.get_appropriate_style_name( s)

##       x, y, x2, y2 = map( Screen.px_to_cm, o.coords)

##       dom_extensions.elementUnder( page, 'draw:rect',

##                                    (( 'svg:x', '%fcm' %  x),

##                                     ( 'svg:y', '%fcm' %  y),

##                                     ( 'svg:width', '%fcm' %  (x2-x)),

##                                     ( 'svg:height', '%fcm' % (y2-y)),

##                                     ( 'draw:style-name', style_name)))







  def add_text( self, a, page):

    """adds text object to document"""

    gr_style = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( a.line_color),

                               fill_color=self.paper.any_color_to_rgb_string( a.area_color))

    gr_style_name = self.get_appropriate_style_name( gr_style)

    para_style = paragraph_style( font_size='%dpx' % round(a.font_size*1), font_family=a.font_family,

                                  color=self.paper.any_color_to_rgb_string( a.line_color))

    para_style_name = self.get_appropriate_style_name( para_style)

    txt_style = text_style( font_size='%dpx' % round(a.font_size*1), font_family=a.font_family)

    txt_style_name = self.get_appropriate_style_name( txt_style)



    coords = map( Screen.px_to_cm, self.paper.coords( a.selector))

    self.create_oo_text( '<ftext>%s</ftext>' % a.xml_ftext, coords, page, para_style_name, txt_style_name, gr_style_name)





  def add_plus( self, a, page):

    """adds text object to document"""

    gr_style = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( a.line_color),

                                 fill_color=self.paper.any_color_to_rgb_string( a.area_color))

    gr_style_name = self.get_appropriate_style_name( gr_style)

    para_style = paragraph_style( font_size='%dpx' % round(a.font_size*1), font_family=a.font_family, color=a.line_color)

    para_style_name = self.get_appropriate_style_name( para_style)

    txt_style = text_style( font_size='%dpx' % round(a.font_size*1), font_family=a.font_family)

    txt_style_name = self.get_appropriate_style_name( txt_style)



    coords = map( Screen.px_to_cm, self.paper.coords( a.selector))

    self.create_oo_text( '<ftext>+</ftext>', coords, page, para_style_name, txt_style_name, gr_style_name)







  def add_arrow( self, a, page):

    for item in a.items:

      # polygons (arrow heads, etc.)

      if self.paper.type( item) == "polygon":

        a_color = self.paper.itemcget( item, "fill")

        l_color = self.paper.itemcget( item, "outline")

        l_width = float( self.paper.itemcget( item, "width"))

        s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( l_color),

                            fill_color=self.paper.any_color_to_rgb_string( a_color),

                            stroke_width=Screen.px_to_cm( l_width))

        style_name = self.get_appropriate_style_name( s)

        ps = geometry.coordinate_flat_list_to_xy_tuples( self.paper.coords( item))

        points = [map( Screen.px_to_cm, p) for p in ps]

        self.create_oo_polygon( points, page, style_name)

      # polylines - standard arrows

      elif self.paper.type( item) == "line":

        line_pin = a._pins.index( self.paper.itemcget( item, 'arrow'))

        end_pin, start_pin = None,None

        if line_pin==1 or line_pin==3:

          end_pin = 1

        if line_pin==2 or line_pin==3:

          start_pin = 1

        l_color = self.paper.itemcget( item, "fill")

        l_width = float( self.paper.itemcget( item, "width"))

        s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( l_color),

                            marker_end=end_pin,

                            marker_start=start_pin,

                            stroke_width=Screen.px_to_cm( l_width))

        style_name = self.get_appropriate_style_name( s)

        ps = geometry.coordinate_flat_list_to_xy_tuples( self.paper.coords( item))

        points = [map( Screen.px_to_cm, p) for p in ps]

        if self.paper.itemcget( item, "smooth") == "0":

          self.create_oo_polyline( points, page, style_name)

        else:

          self.create_oo_bezier( points, page, style_name)

        





  def add_polygon( self, o, page):

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( o.line_color),

                        fill_color=self.paper.any_color_to_rgb_string( o.area_color),

                        stroke_width=Screen.px_to_cm( o.line_width))

    style_name = self.get_appropriate_style_name( s)

    points = [map( Screen.px_to_cm, p.get_xy()) for p in o.points]

    self.create_oo_polygon( points, page, style_name)





  def add_rect( self, o, page):

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( o.line_color),

                        fill_color=self.paper.any_color_to_rgb_string( o.area_color),

                        stroke_width=Screen.px_to_cm( o.line_width))

    style_name = self.get_appropriate_style_name( s)

    x, y, x2, y2 = map( Screen.px_to_cm, o.coords)

    dom_extensions.elementUnder( page, 'draw:rect',

                                       (( 'svg:x', '%fcm' %  x),

                                        ( 'svg:y', '%fcm' %  y),

                                        ( 'svg:width', '%fcm' %  (x2-x)),

                                        ( 'svg:height', '%fcm' % (y2-y)),

                                        ( 'draw:style-name', style_name)))

    



  def add_oval( self, o, page):

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( o.line_color),

                        fill_color=self.paper.any_color_to_rgb_string( o.area_color),

                        stroke_width=Screen.px_to_cm( o.line_width))

    style_name = self.get_appropriate_style_name( s)

    x, y, x2, y2 = map( Screen.px_to_cm, o.coords)

    dom_extensions.elementUnder( page, 'draw:ellipse',

                                       (( 'svg:x', '%fcm' %  x),

                                        ( 'svg:y', '%fcm' %  y),

                                        ( 'svg:width', '%fcm' %  (x2-x)),

                                        ( 'svg:height', '%fcm' % (y2-y)),

                                        ( 'draw:style-name', style_name)))

    



  def add_radical_mark( self, o, page):

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( o.atom.line_color),

                        fill_color=self.paper.any_color_to_rgb_string( o.atom.line_color),

                        stroke_width=Screen.px_to_cm( 0.1))

    style_name = self.get_appropriate_style_name( s)

    for i in o.items:

      x, y, x2, y2 = map( Screen.px_to_cm, self.paper.coords( i))

      size = Screen.px_to_cm( o.size)

      dom_extensions.elementUnder( page, 'draw:ellipse',

                                   (( 'svg:x', '%fcm' %  x),

                                    ( 'svg:y', '%fcm' %  y),

                                    ( 'svg:width', '%fcm' %  size),

                                    ( 'svg:height', '%fcm' % size),

                                    ( 'draw:style-name', style_name)))



  def add_electronpair_mark( self, o, page):

    i = o.items[0]

    width = float( self.paper.itemcget( i, 'width'))

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( o.atom.line_color),

                        fill_color=self.paper.any_color_to_rgb_string( o.atom.line_color),

                        stroke_width=Screen.px_to_cm( width))

    style_name = self.get_appropriate_style_name( s)

    coords = map( Screen.px_to_cm, self.paper.coords( i))

    self.create_oo_line( coords, page, style_name)

      



  def add_plus_mark( self, o, page):

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( o.atom.line_color),

                        fill_color=self.paper.any_color_to_rgb_string( o.atom.area_color),

                        stroke_width=Screen.px_to_cm( 1))

    style_name = self.get_appropriate_style_name( s)

    # we must process oval first - it would otherwise cover the lines

    for i in o.items:

      if self.paper.type( i) == "oval":

        x, y, x2, y2 = map( Screen.px_to_cm, self.paper.coords( i))

        size = Screen.px_to_cm( o.size)

        dom_extensions.elementUnder( page, 'draw:ellipse',

                                     (( 'svg:x', '%fcm' %  x),

                                      ( 'svg:y', '%fcm' %  y),

                                      ( 'svg:width', '%fcm' %  size),

                                      ( 'svg:height', '%fcm' % size),

                                      ( 'draw:style-name', style_name)))

    for i in o.items:

      if self.paper.type( i) == "line":

        coords = self.paper.coords( i)

        # because some weird bug in tcl/tk i had to hack the coordinates in marks.py

        # the hack is reversed here in order to get the coords back

        # I also reduce the size of the mark a little

        #if o.items.index( i) == 1:

        #  coords[0] += 0

        #  coords[2] += -1

        #elif o.items.index( i) == 2:

        #  coords[1] += 0

        #  coords[3] += -1

        # end of hack

        coords = map( Screen.px_to_cm, coords)

        self.create_oo_line( coords, page, style_name)

        



  def add_orbital( self, o, page):

    s = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( o.atom.line_color),

                        fill_color=self.paper.any_color_to_rgb_string( o.atom.area_color),

                        stroke_width=Screen.px_to_cm( 1.0))



    style_name = self.get_appropriate_style_name( s)

    i = 0

    points = []

    for c in o._get_my_curve( num_points=50):

      if not i:

        x = c

        i = 1

      else:

        points.append( map( Screen.px_to_cm, (x, c)))

        i = 0

      

    self.create_oo_polygon( points, page, style_name)



  def add_text_mark( self, a, page):

    """adds text object to document"""

    gr_style = graphics_style( stroke_color=self.paper.any_color_to_rgb_string( a.atom.line_color),

                               fill_color=self.paper.any_color_to_rgb_string( a.atom.area_color))

    gr_style_name = self.get_appropriate_style_name( gr_style)

    para_style = paragraph_style( font_size='%dpx' % round(a.size*1), font_family=a.atom.font_family, color=a.atom.line_color)

    para_style_name = self.get_appropriate_style_name( para_style)

    txt_style = text_style( font_size='%dpx' % round(a.size*1), font_family=a.atom.font_family)

    txt_style_name = self.get_appropriate_style_name( txt_style)



    coords = map( Screen.px_to_cm, self.paper.bbox( a.items[0]))

    self.create_oo_text( '<ftext>%s</ftext>' % a.text, coords, page, para_style_name, txt_style_name, gr_style_name)









# HELPER METHODS



  def get_appropriate_style_name( self, style):

    """if same style already exists return its name, otherwise append the current style and return its name"""

    for s in self.used_styles:

      if style == s:

        return s.name

    style.name = style.name + str( len( self.used_styles))

    self.used_styles.append( style)

    self.styles_element.appendChild( style.to_dom( self.doc))

    return style.name



  def ftext_dom_to_oo_dom( self, ftext, oo_dom):

    if ftext.nodeValue:

      # style inherited from parents

      parents = dom_extensions.getParentNameList( ftext)

      font_weight, font_style, text_position = None, None, None

      if 'b' in parents:

        font_weight = 'bold'

      if 'i' in parents:

        font_style = 'italic'

      if 'sub' in parents:

        text_position = "sub 70%"

      if 'sup' in parents:

        text_position = "super 70%"



      if ftext.parentNode.nodeName == 'ftext':

        oo_dom.appendChild( oo_dom.ownerDocument.createTextNode( ftext.nodeValue))

      else:

        st = span_style( font_style=font_style, font_weight=font_weight, text_position=text_position)

        element = dom_extensions.elementUnder( oo_dom, 'text:span', (('text:style-name', self.get_appropriate_style_name( st)),))

        element.appendChild( oo_dom.ownerDocument.createTextNode( ftext.nodeValue))

    else:

      for el in ftext.childNodes:

        self.ftext_dom_to_oo_dom( el, oo_dom)



## AUTOMATIZED CREATION OF OO OBJECTS



  def create_oo_line( self, coords, page, gr_style_name):

    x1, y1, x2, y2 = coords

    dom_extensions.elementUnder( page, 'draw:line',

                                 (( 'svg:x1', '%fcm' %  x1),

                                  ( 'svg:y1', '%fcm' %  y1),

                                  ( 'svg:x2', '%fcm' %  x2),

                                  ( 'svg:y2', '%fcm' %  y2),

                                  ( 'draw:layer', 'layout'),

                                  ( 'draw:style-name', gr_style_name)))

    



  def create_oo_text( self, ftext, coords, page, para_style_name, txt_style_name, gr_style_name):

    x, y, x2, y2 = coords

    box = dom_extensions.elementUnder( page, 'draw:text-box',

                                       (( 'svg:x', '%fcm' %  x),

                                        ( 'svg:y', '%fcm' %  y),

                                        ( 'svg:width', '%fcm' %  (x2-x)),

                                        ( 'svg:height', '%fcm' % (y2-y)),

                                        ( 'draw:style-name', gr_style_name),

                                        ( 'draw:text-style-name', para_style_name)))



    text = dom_extensions.elementUnder( box, 'text:p', (('text:style-name', para_style_name),))

    oo_text = dom_extensions.elementUnder( text, 'text:span', (('text:style-name', '%s' % txt_style_name),))

    to_parse = dom.parseString( ftext).childNodes[0]

    self.ftext_dom_to_oo_dom( to_parse, oo_text)



  def create_oo_polygon( self, points, page, gr_style_name):

    maxX, maxY, minX, minY = None,None,None,None

    for (x,y) in points:

      if not maxX or x > maxX:

        maxX = x

      if not minX or x < minX:

        minX = x

      if not maxY or y > maxY:

        maxY = y

      if not minY or y < minY:

        minY = y

    points_txt = ""

    for (x,y) in points:

      points_txt += "%d,%d " % ((x-minX)*1000, (y-minY)*1000)



    dom_extensions.elementUnder( page, 'draw:polygon',

                                 (( 'svg:x', '%fcm' % minX),

                                  ( 'svg:y', '%fcm' % minY),

                                  ( 'svg:width', '%fcm' % (maxX-minX)),

                                  ( 'svg:height', '%fcm' % (maxY-minY)),

                                  ( 'svg:viewBox', '0 0 %d %d' % ((maxX-minX)*1000,(maxY-minY)*1000)),

                                  ( 'draw:points', points_txt),

                                  ( 'draw:layer', 'layout'),

                                  ( 'draw:style-name', gr_style_name)))





  def create_oo_polyline( self, points, page, gr_style_name):

    maxX, maxY, minX, minY = None,None,None,None

    for (x,y) in points:

      if not maxX or x > maxX:

        maxX = x

      if not minX or x < minX:

        minX = x

      if not maxY or y > maxY:

        maxY = y

      if not minY or y < minY:

        minY = y

    points_txt = ""

    for (x,y) in points:

      points_txt += "%d,%d " % ((x-minX)*1000, (y-minY)*1000)



    line = dom_extensions.elementUnder( page, 'draw:polyline',

                                        (( 'svg:x', '%fcm' % minX),

                                         ( 'svg:y', '%fcm' % minY),

                                         ( 'svg:width', '%fcm' % (maxX-minX)),

                                         ( 'svg:height', '%fcm' % (maxY-minY)),

                                         ( 'svg:viewBox', '0 0 %d %d' % ((maxX-minX)*1000,(maxY-minY)*1000)),

                                         ( 'draw:points', points_txt),

                                         ( 'draw:layer', 'layout'),

                                         ( 'draw:style-name', gr_style_name)))







  def create_oo_bezier( self, points, page, gr_style_name):

    ps = reduce( operator.add, map( geometry.quadratic_beziere_to_polyline,

                                    geometry.tkspline_to_quadratic_bezier( points)))

    maxX, maxY, minX, minY = None,None,None,None

    for (x,y) in ps:

      if not maxX or x > maxX:

        maxX = x

      if not minX or x < minX:

        minX = x

      if not maxY or y > maxY:

        maxY = y

      if not minY or y < minY:

        minY = y

    points_txt = ""

    for (sx, sy, cxa, cya, cxb, cyb, ex, ey) in geometry.tkspline_to_cubic_bezier( points):

      if not points_txt:

        points_txt += "m %d %d c " % (1000*(sx-minX), 1000*(sy-minY))

      points_txt += "%d %d %d %d %d %d " % (1000*(cxa-sx),1000*(cya-sy),1000*(cxb-sx),1000*(cyb-sy),1000*(ex-sx),1000*(ey-sy))

  

    line = dom_extensions.elementUnder( page, 'draw:path',

                                        (( 'svg:x', '%fcm' % minX),

                                         ( 'svg:y', '%fcm' % minY),

                                         ( 'svg:width', '%fcm' % (maxX-minX)),

                                         ( 'svg:height', '%fcm' % (maxY-minY)),

                                         ( 'svg:viewBox', '0 0 %d %d' % ((maxX-minX)*1000,(maxY-minY)*1000)),

                                         ( 'svg:d', points_txt),

                                         ( 'draw:layer', 'layout'),

                                         ( 'draw:style-name', gr_style_name)))









  def create_styles_document( self):

    style_doc = dom.Document()

    root = dom_ext.elementUnder( style_doc, 'office:document-styles',

                                 (('office:version', '1.0'),

                                  ('xmlns:draw', 'http://openoffice.org/2000/drawing'),

                                  ('xmlns:form', "http://openoffice.org/2000/form"),

                                  ('xmlns:office',"http://openoffice.org/2000/office"),

                                  ('xmlns:style',"http://openoffice.org/2000/style"),

                                  ('xmlns:svg',"http://www.w3.org/2000/svg"),

                                  ('xmlns:text',"http://openoffice.org/2000/text"),

                                  ('xmlns:fo',"http://www.w3.org/1999/XSL/Format")))





    w = self.paper.get_paper_property( 'size_x')/10.0

    h = self.paper.get_paper_property( 'size_y')/10.0

    s = dom_ext.elementUnder( root, 'office:styles')

    astyles = dom_ext.elementUnder( root, 'office:automatic-styles')

    pm = dom_ext.elementUnder( astyles, 'style:page-master', (('style:name','PM1'),))

    dom_ext.elementUnder( pm, 'style:properties', (('fo:page-height','%fcm' % h),

                                                   ('fo:page-width','%fcm' % w),

                                                   ('style:print-orientation','portrait'),

                                                   ('fo:margin-bottom','0.5cm'),

                                                   ('fo:margin-left','0.5cm'),

                                                   ('fo:margin-top','0.5cm'),

                                                   ('fo:margin-right','0.5cm')))

    dp = dom_ext.elementUnder( astyles, 'style:style', (('style:family', 'drawing-page'),

                                                        ('style:name', 'dp1')))

    dom_ext.elementUnder( dp, 'style:properties', (('draw:backgroud-size','border'),

                                                   ('draw:fill', 'none')))



    oms = dom_ext.elementUnder( root, 'office:master-styles')

    mp = dom_ext.elementUnder( oms, 'style:master-page', (('draw:style-name','dp1'),

                                                          ('style:page-master-name','PM1'),

                                                          ('style:name', 'vychozi')))

    return style_doc





  

# PLUGIN INTERFACE SPECIFICATION

name = "OpenOffice Draw"

extensions = [".sxd",".zip"]

exporter = OO_exporter

local_name = _("OpenOffice 1.0 Draw")





## PRIVATE CLASSES AND FUNCTIONS



class style:



  def __init__( self):

    pass



  def __eq__( self, other):

    for a in self.__dict__:

      if a == 'name':

        continue

      if a in other.__dict__:

        if self.__dict__[a] != other.__dict__[a]:

          return 0

      else:

        return 0

    return 1



  def __ne__( self, other):

    return not self.__eq__( other)



  def to_dom( self, doc):

    pass





class graphics_style( style):



  def __init__( self, name='gr', stroke_color='#ffffff', fill='solid', fill_color='#ffffff', stroke_width=0,

                marker_end=None, marker_end_width=None, marker_start=None, marker_start_width=None, padding=(0,0)):

    self.name = name

    self.family = 'graphics'

    self.stroke_color = stroke_color

    self.fill = fill

    self.fill_color = fill_color

    if self.fill_color == "none":

      self.fill = "none"  # this simplifies things very much

    self.stroke_color = stroke_color

    self.stroke_width = stroke_width

    self.marker_end = marker_end

    self.marker_end_width = marker_end_width

    self.marker_start = marker_start

    self.marker_start_width = marker_start_width

    self.padding_top, self.padding_bottom = padding

    self.padding_left = 0

    self.padding_right = 0



  def to_dom( self, doc):

    style = doc.createElement( 'style:style')

    dom_extensions.setAttributes( style, (('style:family', self.family),

                                          ('style:name', self.name),

                                          ('style:parent-style-name','standard')))

    pad_top = "%scm" % self.padding_top

    pad_bot = "%scm" % self.padding_bottom

    pad_left = "%scm" % self.padding_left

    pad_right = "%scm" % self.padding_right

    prop = dom_extensions.elementUnder( style, 'style:properties', (( 'draw:fill', self.fill),

                                                                    ( 'svg:stroke-color', self.stroke_color),

                                                                    ( 'draw:fill-color', self.fill_color),

                                                                    ( 'svg:stroke-width', '%fcm' % self.stroke_width),

                                                                    ( 'draw:auto-grow-width', 'true'),

                                                                    ( 'draw:auto-grow-height', 'true'),

                                                                    ( 'draw:textarea-horizontal-align','middle'),

                                                                    ( 'draw:textarea-vertical-align','middle'),

                                                                    ( 'fo:padding-top', pad_top),

                                                                    ( 'fo:padding-bottom', pad_bot),

                                                                    ( 'fo:padding-left', pad_left),

                                                                    ( 'fo:padding-right', pad_right)))



    if self.marker_end:

      prop.setAttribute( 'draw:marker-end', 'Arrow')

      if self.marker_end_width:

        prop.setAttribute( 'draw:marker-end-width',

                           "%dcm" % self.marker_end_width)

    if self.marker_start:

      prop.setAttribute( 'draw:marker-start', 'Arrow')

      if self.marker_start_width:

        prop.setAttribute( 'draw:marker-start-width',

                           "%dcm" % self.marker_start_width)

    if not self.stroke_width:

      prop.setAttribute('draw:stroke', 'none')

    else:

      prop.setAttribute('draw:stroke', self.stroke_color)

      

    return style





class paragraph_style( style):



  def __init__( self, name='para', font_size='12pt', font_family='Helvetica', color="#000"):

    self.name = name

    self.family = 'paragraph'

    self.font_size = font_size

    if font_family in font_family_remap:

      self.font_family = font_family_remap[ font_family]

    else:

      self.font_family = font_family

    self.color = color





  def to_dom( self, doc):

    style = doc.createElement( 'style:style')

    dom_extensions.setAttributes( style, (('style:family', self.family),

                                          ('style:name', self.name)))

    dom_extensions.elementUnder( style, 'style:properties', (( 'fo:font-size', self.font_size),

                                                             ( 'fo:font-family', self.font_family),

                                                             ( 'fo:text-align', 'center'),

                                                             ( 'fo:color', self.color)))

    return style





class text_style( style):



  def __init__( self, name='text', font_size='12pt', font_family='Helvetica', font_style='normal', font_weight='normal'):

    self.name = name

    self.family = 'text'

    if font_family in font_family_remap:

      self.font_family = font_family_remap[ font_family]

    else:

      self.font_family = font_family

    self.font_size = font_size

    self.font_style = font_style

    self.font_weight = font_weight



  def to_dom( self, doc):

    style = doc.createElement( 'style:style')

    dom_extensions.setAttributes( style, (('style:family', self.family),

                                          ('style:name', self.name)))

    prop = dom_extensions.elementUnder( style, 'style:properties', (( 'fo:font-size', self.font_size),

                                                                    ( 'fo:font-family', self.font_family),

                                                                    ( 'fo:font-style', self.font_style),

                                                                    ( 'fo:font-weight', self.font_weight)))

    return style





class span_style( style):



  def __init__( self, name='span', font_style=None, font_weight=None, text_position=None):

    self.name = name

    self.family = 'text'

    self.font_style = font_style

    self.font_weight = font_weight

    self.text_position = text_position



  def to_dom( self, doc):

    style = doc.createElement( 'style:style')

    dom_extensions.setAttributes( style, (('style:family', self.family),

                                          ('style:name', self.name)))

    prop = dom_extensions.elementUnder( style, 'style:properties')

    if self.font_style:

      prop.setAttribute( 'fo:font-style', self.font_style)

    if self.font_weight:

      prop.setAttribute( 'fo:font-weight', self.font_weight)

    if self.text_position:

      prop.setAttribute( 'style:text-position', self.text_position)

      

    return style





font_family_remap = {'helvetica': 'Albany',

                     'times': 'Thorndale'}

