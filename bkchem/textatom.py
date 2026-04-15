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


"""home for the textatom - a vertex of a molecular graph"""


from warnings import warn
from . import dom_extensions
import xml.dom.minidom as dom
import operator
from .oasa import periodic_table as PT
from .special_parents import drawable_chem_vertex
from . import data
import re
from . import debug
from . import marks

from . import oasa

from .singleton_store import Screen
from functools import reduce


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


### Class TEXTATOM --------------------------------------------------
class textatom( drawable_chem_vertex):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'atom'
  # these values will be automaticaly read from paper.standard on __init__
  meta__undo_properties = drawable_chem_vertex.meta__undo_properties + \
                          ( 'charge',)


  def __init__( self, standard=None, xy=(), package=None, molecule=None):
    drawable_chem_vertex.__init__( self, standard=standard, xy=xy, molecule=molecule)

    self.symbol = ''
    self.valency = 8 # high allowed valency

    if package:
      self.read_package( package)



  ## ---------------------------------------- PROPERTIES ------------------------------
      
  # symbol
  def _get_symbol( self):
    return self._symbol

  def _set_symbol( self, symbol):
    try:
      t = str(symbol)
    except UnicodeDecodeError:
      t = symbol.decode( 'utf-8')
    self._symbol = t
    self.dirty = 1

  symbol = property( _get_symbol, _set_symbol)



  ## JUST TO MIMICK ATOM
  # show
  def _get_show( self):
    return 1

  def _set_show( self, show):
    pass

  show = property( _get_show, _set_show, None,
                   "should the atom symbol be displayed? accepts both 0|1 and yes|no")


  # show_hydrogens
  def _get_show_hydrogens( self):
    return 1

  def _set_show_hydrogens( self, show_hydrogens):
    pass

  show_hydrogens = property( _get_show_hydrogens, _set_show_hydrogens)

  ## //




  ## // -------------------- END OF PROPERTIES --------------------------


  def set_name( self, name, interpret=1, occupied_valency=None):
    self.symbol = name
    return True




  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    a = ['no','yes']
    on_off = ['off','on']
    self.id = package.getAttribute( 'id')
    # marks
    for m in package.getElementsByTagName( 'mark'):
      mrk = marks.mark.read_package( m, self)
      self.marks.add( mrk)

    # position
    self.pos = package.getAttribute( 'pos')
    position = package.getElementsByTagName( 'point')[0]
    # reading of coords regardless of their unit
    x, y, z = Screen.read_xml_point( position)
    if z != None:
      self.z = z* self.paper.real_to_screen_ratio()
    # needed to support transparent handling of molecular size
    x, y = self.paper.real_to_screen_coords( (x, y))
    self.x = x
    self.y = y
    ft = package.getElementsByTagName('ftext')
    if ft:
      self.set_name( reduce( operator.add, [e.nodeValue for e in ft[0].childNodes if isinstance( e, dom.Text)], '').encode('utf-8'))
    else:
      raise TypeError("not text atom")
    # font and fill color
    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    # background color
    if package.getAttributeNode( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
    # number
    if package.getAttribute( 'show_number'):
      self.show_number = bool( data.booleans.index( package.getAttribute( 'show_number')))
    if package.getAttribute( 'number'):
      self.number = package.getAttribute( 'number')




  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    y = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('text')
    a.setAttribute( 'id', str( self.id))
    a.setAttribute( 'pos', self.pos)
    # font properties
    if self.font_size != self.paper.standard.font_size \
       or self.font_family != self.paper.standard.font_family \
       or self.line_color != self.paper.standard.line_color:
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != self.paper.standard.line_color:
        font.setAttribute( 'color', self.line_color)
    # the text
    ftext = dom_extensions.elementUnder( a, 'ftext')
    ftext.appendChild( doc.createTextNode( self.symbol))
    # area color
    if self.area_color != self.paper.standard.area_color:
      a.setAttribute( 'background-color', self.area_color)
    # needed to support transparent handling of molecular size
    x, y, z = map( Screen.px_to_text_with_unit, self.get_xyz( real=1))
    if self.z:
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y), ('z', z)))
    else: 
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y)))
    # marks
    for o in self.marks:
      a.appendChild( o.get_package( doc))
    # number
    if self.number:
      a.setAttribute( 'number', self.number)
      a.setAttribute( 'show_number', data.booleans[ int( self.show_number)])

    return a





  def get_formula_dict( self):
    """returns formula as dictionary that can
    be passed to functions in periodic_table"""
    return PT.formula_dict()



  def __str__( self):
    return self.id










