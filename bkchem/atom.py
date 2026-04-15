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


"""home for atom class"""


from warnings import warn
from . import dom_extensions
import operator
from .oasa import periodic_table as PT
from . import marks
from .special_parents import drawable_chem_vertex
from . import data
import re
from . import debug

from . import oasa
from .singleton_store import Screen, Store
from functools import reduce


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


### Class ATOM --------------------------------------------------
class atom( drawable_chem_vertex, oasa.atom):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'atom'
  meta__undo_properties = drawable_chem_vertex.meta__undo_properties + \
                          ( 'show_hydrogens',
                            'multiplicity', 'valency', 'free_sites', 'symbol')


  def __init__( self, standard=None, xy=(), package=None, molecule=None):
    drawable_chem_vertex.__init__( self, standard=standard, xy=xy, molecule=molecule)
    if xy:
      oasa.atom.__init__( self, coords=(xy[0],xy[1],0))
    else:
      oasa.atom.__init__( self)

    # chemistry attrs
    self.show = 0
    self.show_hydrogens = 0
    self.multiplicity = 1

    if package:
      self.read_package( package)
    else:
      self.set_name( 'C')



  ## ---------------------------------------- PROPERTIES ------------------------------
      
  # symbol (overrides the oasa.atom.symbol property)
  def _get_symbol( self):
    return self._symbol

  def _set_symbol( self, symbol):
    oasa.atom._set_symbol( self, symbol)
    if self._symbol != 'C':
      self.show = True

  symbol = property( _get_symbol, _set_symbol, None, "the atom symbol")


  # show
  def _get_show( self):
    return self._show

  def _set_show( self, show):
    if show in data.booleans:
      self._show = data.booleans.index( show)
    else:
      self._show = int( show)
    self.dirty = 1
    self._reposition_on_redraw = 1

  show = property( _get_show, _set_show, None,
                   "should the atom symbol be displayed? accepts both 0|1 and yes|no")


  # show_hydrogens
  def _get_show_hydrogens( self):
    return self._show_hydrogens

  def _set_show_hydrogens( self, show_hydrogens):
    if show_hydrogens in data.on_off:
      self._show_hydrogens = data.on_off.index( show_hydrogens)
    else:
      self._show_hydrogens = int( show_hydrogens)
    self.dirty = 1
    self._reposition_on_redraw = 1

  show_hydrogens = property( _get_show_hydrogens, _set_show_hydrogens)


  # charge (override of oasa.chem_vertex.charge)
  def _get_charge( self):
    return drawable_chem_vertex._get_charge( self)

  def _set_charge( self, charge):
    drawable_chem_vertex._set_charge( self, charge)
    self.dirty = 1

  charge = property( _get_charge, _set_charge)



  # valency
  def _get_valency( self):
    try:
      self._valency
    except AttributeError:
      self.set_valency_from_name()
    return self._valency

  def _set_valency( self, val):
    drawable_chem_vertex._set_valency( self, val)

  valency = property( _get_valency, _set_valency, None, "atoms (maximum) valency, used for hydrogen counting")



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


  # oxidation number as text
  def _get_oxidation_number_text( self):
    return data.roman_numbers[ self._get_oxidation_number()]

  oxidation_number_text = property( _get_oxidation_number_text, None, None, "atoms oxidation number as text")



  # xml_ftext (override drawable_chem_vertex.xml_ftext)
  def _get_xml_ftext( self):
    ret = self.symbol
    if not self.pos:
      self.decide_pos()
    # hydrogens
    if self.show_hydrogens:
      v = self.free_valency
      if v:
        h = 'H'
      else:
        h = ''
      if v > 1:
        h += '<sub>%d</sub>' % v
      if self.pos == 'center-last':
        ret = h + ret
      else:
        ret = ret + h
    # charge
    if self.charge -self.get_charge_from_marks():
      ch = ''
      if abs( self.charge) > 1:
        ch += str( abs( self.charge -self.get_charge_from_marks()))
      if self.charge -self.get_charge_from_marks() > 0:
        ch = '<sup>%s+</sup>' % ch
      else:
        ch = u'<sup>%s%s</sup>' % (ch, self.paper.get_paper_property( 'use_real_minus') and chr( 8722) or "-")
    else:
      ch = ''
    if self.pos == 'center-last':
      ret = ch + ret
    else:
      ret = ret + ch
    return ret

  xml_ftext = property( _get_xml_ftext, None, None, "the text used for rendering using the ftext class")



  ## // -------------------- END OF PROPERTIES --------------------------


  ## -------------------- OVERRIDES OF CHEM_VERTEX METHODS --------------------

  def decide_pos( self):
    if self.show_hydrogens or self.free_valency:
      # in case hydrogens are shown, use the chem_vertex.decide_pos algorithm
      drawable_chem_vertex.decide_pos( self)
    else:
      #  otherwise always center the first letter
      self.pos = "center-first"
  

  ## // -------------------- END --------------------


  def set_name( self, name, interpret=1, check_valency=1, occupied_valency=None):
    ret = self._set_name( name, interpret=interpret, check_valency=check_valency, occupied_valency=occupied_valency)
    self.set_valency_from_name()
    self.update_after_valency_change()
    return ret


  def _set_name( self, name, interpret=1, check_valency=1, occupied_valency=None):
    # every time name is set the charge should be set to zero or the value specified by marks
    self.charge = self.get_charge_from_marks()
    self.dirty = 1
    # try to interpret name
    if name.lower() != 'c':
      self.show = 1
    else:
      self.show = 0
    elch = self.split_element_and_charge( name)
    if elch:
      # name is element symbol + charge
      self.symbol = elch[0]
      #self.show_hydrogens = 0
      self.charge += elch[1]
      return True
    else:
      # try if name is hydrogenated form of an element
      form = PT.text_to_hydrogenated_atom( name)
      if form:
        # it is!
        a = form.keys()
        a.remove( 'H')
        if occupied_valency == None:
          valency = self.occupied_valency
        else:
          valency = occupied_valency
        if form['H'] in [i-valency+self.charge for i in PT.periodic_table[a[0]]['valency']]:
          self.symbol = a[0]
          self.show_hydrogens = 1
          # decide hydrogen placement based on how the name was written (only if it has no neighbor)
          if occupied_valency:
            self.pos = None # decide later
          else:
            if name.lower().find( "h") < name.lower().find( self.symbol.lower()):
              self.pos = "center-last"
            else:
              self.pos = "center-first"
          #self.show = 1
          return True
    return False







  def draw( self, redraw=False):
    "draws atom with respect to its properties"
    if self.show:
      drawable_chem_vertex.draw( self, redraw=redraw)
    else:
      if self.item:
        warn( "drawing atom that is probably drawn", UserWarning, 2)
      x, y = self.x, self.y
      self.item = self.paper.create_line( x, y, x, y, tags=("atom", 'nonSVG'), fill='')
      self.selector = None
      if not redraw:
        [m.draw() for m in self.marks]
      self.paper.register_id( self.item, self)
      self._reposition_on_redraw = 0





  def focus( self):
    if self.show:
      drawable_chem_vertex.focus( self)
    else:
      x, y = self.x, self.y
      self.focus_item = self.paper.create_oval( x-4, y-4, x+4, y+4, tags=('helper_f','no_export'))
      self.paper.lift( self.item)




  def unfocus( self):
    if self.show:
      drawable_chem_vertex.unfocus( self)
    if self.focus_item:
      self.paper.delete( self.focus_item)
      self.focus_item = None




  def select( self):
    if self.show:
      drawable_chem_vertex.select( self)
    else:
      x, y = self.x, self.y
      if self.selector:
        self.paper.coords( self.selector, x-2, y-2, x+2, y+2)
      else:
        self.selector = self.paper.create_rectangle( x-2, y-2, x+2, y+2)
      self.paper.lower( self.selector)
      self._selected = 1




  def unselect( self):
    if self.show:
      drawable_chem_vertex.unselect( self)
    else:
      self.paper.delete( self.selector)
      self.selector = None
      self._selected = 0



  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    a = ['no','yes']
    on_off = ['off','on']
    self.id = package.getAttribute( 'id')
    # marks (we read them here because they influence the charge)
    for m in package.getElementsByTagName( 'mark'):
      mrk = marks.mark.read_package( m, self)
      self.marks.add( mrk)
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
      self.set_name( reduce( operator.add, [e.toxml() for e in ft[0].childNodes], ''), check_valency=0, interpret=0)
    else:
      self.set_name( package.getAttribute( 'name'), check_valency=0)
    # charge
    self.charge = package.getAttribute('charge') and int( package.getAttribute('charge')) or 0
    # hydrogens
    if package.getAttribute( 'hydrogens'):
      self.show_hydrogens = package.getAttribute('hydrogens')
    else:
      self.show_hydrogens = 0
    # font and fill color
    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    # show
    if package.getAttribute( 'show'):
      self.show = package.getAttribute( 'show')
    else:
      self.show = (self.symbol!='C')
    # background color
    if package.getAttributeNode( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
    # multiplicity
    if package.getAttribute( 'multiplicity'):
      self.multiplicity = int( package.getAttribute( 'multiplicity'))
    # valency
    if package.getAttribute( 'valency'):
      self.valency = int( package.getAttribute( 'valency'))
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
    yes_no = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('atom')
    a.setAttribute( 'id', str( self.id))
    # charge
    if self.charge:
      a.setAttribute( "charge", str( self.charge))
    #show attribute is set only when non default
    if (self.show and self.symbol=='C') or (not self.show and self.symbol!='C'): 
      a.setAttribute('show', yes_no[ self.show])
    if self.show:
      a.setAttribute( 'pos', self.pos)
    if self.font_size != self.paper.standard.font_size \
       or self.font_family != self.paper.standard.font_family \
       or self.line_color != self.paper.standard.line_color:
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != self.paper.standard.line_color:
        font.setAttribute( 'color', self.line_color)
    a.setAttribute( 'name', self.symbol)
    if self.show_hydrogens:
      a.setAttribute('hydrogens', on_off[self.show_hydrogens])
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
    # multiplicity
    if self.multiplicity != 1:
      a.setAttribute( 'multiplicity', str( self.multiplicity))
    # valency
    a.setAttribute( 'valency', str( self.valency))
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
    ret = PT.formula_dict( self.symbol)
    if self.free_valency > 0:
      ret['H'] = self.free_valency
    return ret





  # overrides special_parents.drawable_chem_vertex method
  def _set_mark_helper( self, mark, sign=1):
    drawable_chem_vertex._set_mark_helper( self, mark, sign=sign)
    mark, _ = self._mark_to_name_and_class( mark)
    if mark == 'plus':
      self.charge += 1*sign
    elif mark == 'minus':
      self.charge -= 1*sign
    elif mark == "radical":
      self.multiplicity += 1*sign
    elif mark == "biradical":
      self.multiplicity += 2*sign
    



  def update_after_valency_change( self):
    if self.free_valency <= 0:
      self.raise_valency_to_senseful_value()
    if self.show_hydrogens:
      self.redraw()




  def __str__( self):
    return self.id



  def get_charge_from_marks( self):
    res = 0
    for m in self.marks:
      if m.__class__.__name__ == 'plus':
        res += 1
      elif m.__class__.__name__ == "minus":
        res -= 1
    return res





  def generate_marks_from_cheminfo( self):
    if self.charge == 1 and not self.get_marks_by_type( 'plus'):
      self.create_mark( 'plus', draw=0)
    elif self.charge == -1 and not self.get_marks_by_type( 'minus'):
      self.create_mark( 'minus', draw=0)
    if self.multiplicity == 2 and not self.get_marks_by_type( 'radical'):
      self.create_mark( 'radical', draw=0)
    elif self.multiplicity == 3 and not (self.get_marks_by_type( 'biradical') or len( self.get_marks_by_type( 'radical')) == 2):
      self.create_mark( 'biradical', draw=0)
  




  def set_valency_from_name( self):
    for val in PT.periodic_table[ self.symbol]['valency']:
      self.valency = val
      try:
        fv = self.free_valency
      except:
        return  # this happens on read
      if fv >= 0:
        return

    

  def bbox( self, substract_font_descent=False):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    if self.show:
      return drawable_chem_vertex.bbox( self, substract_font_descent=substract_font_descent)
    else:
      if self.item:
        return self.paper.bbox( self.item)
      else:
        # we have to calculate it, the atoms was not drawn yet
        return self.x, self.y, self.x, self.y



  ##LOOK  (make static)
  def split_element_and_charge( self, txt):
    """returns tuple of (element, charge) or None if the text does not match this pattern"""
    ### this could be a static method
    # Handle both string and bytes input
    if isinstance(txt, bytes):
      txt = txt.decode('utf-8')
    
    splitter = re.compile("^([a-z]+)([0-9]*)([+-]?)$")
    matcher = re.compile( "^([a-z]+)([0-9]*[+-])?$")
    if not matcher.match( txt.lower()):
      return None
    match = splitter.match( txt.lower())
    if match:
      if match.group(1).capitalize() not in PT.periodic_table or 'query' in PT.periodic_table[ match.group(1).capitalize()].keys():
        return None
      if match.group(3) == '+':
        charge = match.group(2) and int( match.group(2)) or 1
      elif match.group(3) == '-':
        charge = match.group(2) and -int( match.group(2)) or -1
      else:
        charge = 0
      return (match.group(1).capitalize(), charge)
    else:
      return None


  def after_undo( self):
    """this is run after undo"""
    self._clean_cache()
