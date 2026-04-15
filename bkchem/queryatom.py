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


"""home for query_atom class"""


from warnings import warn
from . import dom_extensions
from .oasa import periodic_table as PT
from . import marks
from .special_parents import drawable_chem_vertex
from . import data
import re
from . import debug

from . import oasa
from .singleton_store import Screen


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


### Class ATOM --------------------------------------------------
class queryatom( drawable_chem_vertex, oasa.query_atom):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'atom'
  meta__undo_properties = drawable_chem_vertex.meta__undo_properties + \
                          ( 'free_sites',)

  # only number marks are allowed for query atoms
  #meta__allowed_marks = () #"atom_number","free_sites")


  def __init__( self, standard=None, xy=(), package=None, molecule=None):
    drawable_chem_vertex.__init__( self, standard=standard, xy=xy, molecule=molecule)
    if xy:
      oasa.query_atom.__init__( self, coords=(xy[0],xy[1],0))
    else:
      oasa.query_atom.__init__( self)

    if package:
      self.read_package( package)



  ## ---------------------------------------- PROPERTIES ------------------------------


  # name
  def _get_name( self):
    return self.__name

  def _set_name( self, name):
    try:
      t = str(name)
    except UnicodeDecodeError:
      t = name.decode( 'utf-8')
    self.__name = t.encode('utf-8')
    self.dirty = 1

  name = property( _get_name, _set_name)



  #LOOK charge
  def _get_charge( self):
    return self.__charge

  def _set_charge( self, charge):
    self.__charge = charge
    self.dirty = 1

  charge = property( _get_charge, _set_charge)



  #LOOK valency (setting)
  def _get_valency( self):
    return 1

  def _set_valency( self, val):
    pass

  valency = property( _get_valency, _set_valency, None, "atoms (maximum) valency, used for hydrogen counting")




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



  # free-sites - replaces oasa.atom.free_sites
  def _set_free_sites( self, free_sites):
    self._free_sites = free_sites
    marks = self.get_marks_by_type( "free_sites")
    if self._free_sites:
      if not marks:
        self.create_mark( "free_sites", draw=self.drawn)
      elif self.drawn:
        marks[0].redraw()
    else:
      if marks:
        self.remove_mark( "free_sites")


  def _get_free_sites( self):
    return self._free_sites

  free_sites = property( _get_free_sites, _set_free_sites, None, "atoms free_sites")


  def _get_free_sites_text( self):
    """used by free-site mark"""
    if self.free_sites:
      return "[%d]" % self.free_sites
    else:
      return ""

  free_sites_text = property( _get_free_sites_text, None, None, "atoms free_sites as text")




  ## // -------------------- END OF PROPERTIES --------------------------



  def set_name( self, name, interpret=1, occupied_valency=None):
    try:
      self.symbol = name
    except oasa.oasa_exceptions.oasa_invalid_atom_symbol:
      return False
    else:
      return True


  def interpret_name( self, name):
    lf = oasa.linear_formula.linear_formula( name, start_valency=self.valency)
    return lf.molecule
      




  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    a = ['no','yes']
    on_off = ['off','on']
    self.id = package.getAttribute( 'id')
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

    self.symbol = package.getAttribute( "name")

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

    # marks
    for m in package.getElementsByTagName( 'mark'):
      mrk = marks.mark.read_package( m, self)
      self.marks.add( mrk)
    # number
    if package.getAttribute( 'show_number'):
      self.show_number = bool( data.booleans.index( package.getAttribute( 'show_number')))
    if package.getAttribute( 'number'):
      self.number = package.getAttribute( 'number')
    # free_sites
    if package.getAttribute( 'free_sites'):
      self.free_sites = int( package.getAttribute( 'free_sites'))




  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    y = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('query')
    a.setAttribute( 'id', str( self.id))
    a.setAttribute( 'pos', self.pos)
    a.setAttribute( 'name', self.symbol)

    if self.font_size != self.paper.standard.font_size \
       or self.font_family != self.paper.standard.font_family \
       or self.line_color != self.paper.standard.line_color:
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != self.paper.standard.line_color:
        font.setAttribute( 'color', self.line_color)

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
    # free_sites
    if self.free_sites:
      a.setAttribute( 'free_sites', str( self.free_sites))

    return a




  def get_formula_dict( self):
    """returns formula as dictionary that can
    be passed to functions in periodic_table"""
    return PT.formula_dict()
      


  def __str__( self):
    return self.id




