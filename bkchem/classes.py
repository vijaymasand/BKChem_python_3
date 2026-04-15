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


"""set of basic classes such as standard, plus, text etc.
also imports atom, bond and molecule from historical reasons :)"""



from math import atan2, sin, cos, pi, sqrt
from . import misc
from warnings import warn
from .ftext import ftext
from . import dom_extensions
import xml.dom.minidom as dom
import operator
import tkinter.font as tkFont
from .parents import meta_enabled, container, with_line, text_like, line_colored
from .parents import area_colored, point_drawable, interactive, drawable, top_level
from .parents import child, with_font
from .reaction import reaction

from .singleton_store import Screen
from functools import reduce

### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself



##-------------------- STANDARD CLASS ------------------------------

class standard:

  def __init__( self):
    # common
    self.line_width = '1px'
    self.font_size = 12
    self.font_family = 'helvetica'
    self.line_color = "#000"
    self.area_color = '' ##ffffff'
    # bond
    self.bond_length = '0.7cm'
    self.bond_width = '6px'
    self.wedge_width = '5px'
    self.double_length_ratio = 0.75
    # atom
    self.show_hydrogens = 0
    # arrow
    self.arrow_length = '1.6cm'
    # paper
    self.paper_type = 'A4'
    self.paper_orientation = 'portrait'
    self.paper_crop_svg = 0
    self.paper_crop_margin = 10


  def __eq__( self, other):
    for (k,v) in self.__dict__.items():
      if str( v) != str( other.__dict__[ k]):
        return 0
    return 1

  def __ne__( self, other):
    return not self.__eq__( other)


  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    ret = doc.createElement( 'standard')
    dom_extensions.setAttributes( ret, (('line_width', str( self.line_width)),
                                        ('font_size', str( self.font_size)),
                                        ('font_family', str( self.font_family)),
                                        ('line_color', self.line_color),
                                        ('area_color', self.area_color),
                                        ('paper_type', self.paper_type),
                                        ('paper_orientation', self.paper_orientation),
                                        ('paper_crop_svg', str( self.paper_crop_svg)),
                                        ('paper_crop_margin', str( self.paper_crop_margin))))
    dom_extensions.elementUnder( ret, 'bond', (('length', str( self.bond_length)),
                                               ('width', str( self.bond_width)),
                                               ('wedge-width', str( self.wedge_width)),
                                               ('double-ratio', str( self.double_length_ratio))))
    dom_extensions.elementUnder( ret, 'arrow', (('length', str( self.arrow_length)),))
    dom_extensions.elementUnder( ret, 'atom', (('show_hydrogens', str( int( self.show_hydrogens))),))
    return ret

  def read_package( self, p):
    for attr in ('line_width', 'font_size', 'font_family', 'line_color','area_color',
                 'paper_crop_svg','paper_orientation','paper_type','paper_crop_margin'):
      if p.getAttribute( attr):
        self.__dict__[ attr] = p.getAttribute( attr)
    self.font_size = int( self.font_size)
    self.paper_crop_svg = int( self.paper_crop_svg)
    self.paper_crop_margin = int( self.paper_crop_margin)
    b = dom_extensions.getFirstChildNamed( p, 'bond')
    if b:
      self.bond_length = b.getAttribute( 'length') or self.bond_length
      self.bond_width = b.getAttribute( 'width') or self.bond_width
      self.double_length_ratio = b.getAttribute( 'double-ratio') or self.double_length_ratio
      self.double_length_ratio = float( self.double_length_ratio)
      self.wedge_width = b.getAttribute( 'wedge-width') or self.wedge_width
    a = dom_extensions.getFirstChildNamed( p, 'arrow')
    if a:
      self.arrow_length = a.getAttribute( 'length')
    a = dom_extensions.getFirstChildNamed( p, 'atom')
    if a:
      show_hydrogens = a.getAttribute('show_hydrogens')
      if show_hydrogens == "False":
        show_hydrogens = 0
      elif show_hydrogens == "True":
        show_hydrogens = 1
      self.show_hydrogens = int( show_hydrogens)
      
    




## -------------------- POINT CLASS ------------------------------

class point( point_drawable, interactive, child):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'point'

  # undo related metas
  meta__undo_properties = point_drawable.meta__undo_properties
  

  def __init__( self, paper, xy=(), arrow=None, package=None, type='invisible'):
    point_drawable.__init__( self)
    if xy:
      self.x, self.y = xy
    self.paper = paper
    self.item = None
    self.focus_item = None
    self.selector = None
    self.type = type
    if arrow:
      self.arrow = arrow
    if package:
      self.read_package( package)


  def draw( self):
    if self.item:
      self.redraw()
    else:
      if self.type == 'invisible':
        self.item = self.paper.create_line( self.x, self.y, self.x, self.y, tags='point', fill='')
      elif self.type == 'circle':
        self.item = self.paper.create_oval( self.x-2, self.y-2, self.x+2, self.y+2, fill='grey', outline='grey', tags='point')
      else:
        warn( 'unknown point type')
        return 
      self.paper.register_id( self.item, self)

  def redraw( self):
    if not self.item:
      self.draw()
    else:
      self.paper.delete( self.item)
      self.item = None
      self.draw()
      if self.selector:
        self.paper.coords( self.selector, self.x-2, self.y-2, self.x+2, self.y+2)

  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)

  def move_to( self, x, y):
    if not self.item:
      self.x = x
      self.y = y
      self.draw()
    else:
      dx = x -self.x
      dy = y -self.y
      self.move( dx, dy)

  def focus( self):
    self.focus_item = self.paper.create_oval( self.x-4, self.y-4, self.x+4, self.y+4)
    if self.item:
      self.paper.lift( self.item)

  def unfocus( self):
    if self.focus_item:
      self.paper.delete( self.focus_item)
      self.focus_item = None

  def select( self):
    if not self.selector:
      self.selector = self.paper.create_rectangle( self.x-2, self.y-2, self.x+2, self.y+2)
      self.paper.lower( self.selector)

  def unselect( self):
    if self.selector:
      self.paper.delete( self.selector)
      self.selector = None
    
  def get_xy( self):
    return self.x, self.y

  def delete( self):
    self.unselect()
    self.unfocus()
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None

  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    x, y, z = Screen.read_xml_point( package)
    self.x, self.y = self.paper.real_to_screen_coords( (x,y))
    #self.z = int( package.getAttribute( 'z') )
  
  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pnt = doc.createElement('point')
    x, y = map( Screen.px_to_text_with_unit, self.paper.screen_to_real_coords( (self.x, self.y)))
    dom_extensions.setAttributes( pnt, (('x', x),
                                        ('y', y)))
    return pnt

  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.item:
      self.paper.lift( self.item)

  def change_type( self, type):
    self.type = type
    self.redraw()

  def transform( self, tr):
    x, y = tr.transform_xy( self.x, self.y)
    self.move_to( x, y)

  # parent
  def _get_parent( self):
    return self.arrow

  def _set_parent( self, par):
    self.arrow = par

  parent = property( _get_parent, _set_parent, None,
                     "returns self.molecule")








##-------------------- PLUS CLASS ------------------------------

class plus(meta_enabled, interactive, point_drawable, with_font, area_colored, top_level):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'plus'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_family']
  # undo related metas
  meta__undo_properties = point_drawable.meta__undo_properties +\
                          with_font.meta__undo_properties +\
                          area_colored.meta__undo_properties

  def __init__( self, paper, xy=(), package=None):
    area_colored.__init__( self)
    point_drawable.__init__( self)
    with_font.__init__( self)
    meta_enabled.__init__( self, standard=paper.standard)

    self.paper = paper

    self.x = self.y = None
    self.focus_item = None
    self.selector = None
    self._selected = 0
    self.font_size = 14
    if xy:
      self.x, self.y = xy
    if package:
      self.read_package( package)
    # standard values
    self.update_font()
    
  def draw( self):
    self.update_font()
    self.item = self.paper.create_text( self.x, self.y, text='+', tags='plus', font = self.font, fill=self.line_color)
    self.paper.register_id( self.item, self)
    self.selector = self.paper.create_rectangle( self.paper.bbox( self.item), fill=self.area_color, outline=self.area_color)
    self.paper.lift( self.item)


  def redraw( self):
    self.update_font()
    self.paper.coords( self.item, self.x, self.y)
    self.paper.itemconfig( self.item, font = self.font, fill=self.line_color)
    if self.selector:
      self.paper.coords( self.selector, self.paper.bbox( self.item))
      self.paper.itemconfig( self.selector, fill=self.area_color, outline=self.area_color)

  def focus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill='grey')

  def unfocus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill=self.area_color)

  def get_id( self):
    return self.item

  def select( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1
 
  def unselect( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline=self.area_color)
    self._selected = 0
    
  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    if hasattr( self, 'item') and self.item:
      self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)

  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.move( dx, dy)

  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    if package.getAttribute( 'id'):
      self.id = package.getAttribute( 'id')
    pnt = package.getElementsByTagName( 'point')[0]
    self.x, self.y, z = Screen.read_xml_point( pnt)
    if package.getAttribute( 'font_size'):
      self.font_size = int( package.getAttribute( 'font_size')) 
    if package.getAttribute( 'color'):
      self.line_color = package.getAttribute( 'color')
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
  
  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pls = doc.createElement('plus')
    pls.setAttribute( 'id', self.id)
    x, y = Screen.px_to_text_with_unit( (self.x, self.y))
    dom_extensions.elementUnder( pls, 'point', (('x', x),
                                                ('y', y)))
    pls.setAttribute('font_size', str( self.font_size))
    if self.line_color != '#000':
      pls.setAttribute( 'color', self.line_color)
    if self.area_color != '#ffffff':
      pls.setAttribute( 'background-color', self.area_color)
    return pls

  def delete( self):
    self.paper.delete( self.selector)
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)

  def get_xy( self):
    return self.x, self.y

  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    if hasattr( self, 'item') and self.item:
      return self.paper.bbox( self.item)
    else:
      dx = self.font.measure( '+') / 2
      return self.x + dx, self.y + 0.7*self.font_size, self.x - dx, self.y - 0.3*self.font_size

  def scale_font( self, ratio):
    """scales font of plus. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()

  def update_font( self):
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)

  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.item:
      self.paper.lift( self.item)

##--------------------TEXT CLASS--------------------

class text( meta_enabled, interactive, point_drawable, text_like, area_colored, top_level):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'text'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_size','font_family']
  # undo related metas
  meta__undo_properties = point_drawable.meta__undo_properties +\
                          text_like.meta__undo_properties +\
                          area_colored.meta__undo_properties +\
                          ("xml_ftext",)
  

  def __init__( self, paper, xy=(), text='', package=None):
    text_like.__init__( self)
    point_drawable.__init__( self)
    area_colored.__init__( self)
    meta_enabled.__init__( self, standard=paper.standard)

    self.paper = paper

    self.selector = None
    self._selected = 0
    self.ftext = None
    if xy:
      self.set_xy( xy[0], xy[1])
    self.xml_ftext = text
    self.item = None
    if package:
      self.read_package( package)
    self.focus_item = None
    self.justify = 'right'

  # public methods

  def set_xy( self, x, y):
    self.x = round( x, 2)
    self.y = round( y, 2)

  def draw( self):
    "draws text"
    self.update_font()
    self.ftext = ftext( self.paper, (self.x, self.y), self.xml_ftext, font=self.font, fill=self.line_color, justify=self.justify)
    self.ftext.draw()
    x1, y1, x2, y2 = self.ftext.bbox()
    self.item = self.paper.create_rectangle( x1, y1, x2, y2, fill='', outline='', tags=('text','no_export'))
    self.selector = self.paper.create_rectangle( x1, y1, x2, y2, fill=self.area_color, outline='', tags=('helper_a','no_export'))
    self.ftext.lift()
    self.paper.lift( self.item)
    self.paper.register_id( self.item, self)

  def redraw( self):
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    if self.selector:
      self.paper.delete( self.selector)
    if self.ftext:
      self.ftext.delete()
    self.draw()
    if self._selected:
      self.select()

  def focus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill='gray')

  def unfocus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill=self.area_color)

  def select( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1




  def unselect( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline=self.area_color)
    self._selected = 0


  def move( self, dx, dy):
    """moves object with his selector (when present)"""
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move( dx, dy)


  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.set_xy( x, y)
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move_to( x, y)


  def get_x( self):
    return self.x


  def get_y( self):
    return self.y


  def get_xy( self):
    return self.x, self.y


  def delete( self):
    if self.focus_item:
      self.unfocus()
    if self.selector:
      self.paper.delete( self.selector)
      self.selector = None
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
    if self.ftext:
      self.ftext.delete()
    return self


  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    if package.getAttribute( 'id'):
      self.id = package.getAttribute( 'id')
    pos = package.getElementsByTagName( 'point')[0]
    x, y, z = Screen.read_xml_point( pos)
    self.set_xy( x, y)
    ft = package.getElementsByTagName('ftext')
    try:
      self.xml_ftext = reduce( operator.add, [e.nodeValue for e in ft[0].childNodes if isinstance( e, dom.Text)], '')
    except IndexError:
      self.xml_ftext = "?"

    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')



  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    a = doc.createElement('text')
    a.setAttribute( 'id', self.id)
    if self.area_color != '':
      a.setAttribute( 'background-color', self.area_color)
    if self.font_size != self.paper.standard.font_size \
       or self.font_family != self.paper.standard.font_family \
       or self.line_color != self.paper.standard.line_color:
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != self.paper.standard.line_color:
        font.setAttribute( 'color', self.line_color)
    x, y = Screen.px_to_text_with_unit( (self.x, self.y))
    dom_extensions.elementUnder( a, 'point', attributes=(('x', x),('y', y)))
    ftext = dom_extensions.elementUnder( a, 'ftext')
    ftext.appendChild( doc.createTextNode( self.xml_ftext))
    return a


  # xml_ftext
  def _get_xml_ftext( self):
    return self._ftext

  def _set_xml_ftext( self, text):
    if isinstance(text, bytes):
      text = text.decode( 'utf-8')
    self._ftext = text

  xml_ftext = property( _get_xml_ftext, _set_xml_ftext, None, "the text used for rendering using the ftext class")



  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.ftext.bbox()



  def update_font( self):
    #if 'font_family' in self.__dict__ and 'font_size' in self.__dict__:
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)



  def scale_font( self, ratio):
    """scales font of text. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()




  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)


