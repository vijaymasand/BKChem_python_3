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

"""CML2 import-export plugin"""

from . import plugin
from . import CML
import xml.dom.minidom as dom
from .. import dom_extensions as dom_ext
import gettext
_ = gettext.gettext

## DEFINITIONS

class CML2_importer( CML.CML_importer):
  """Imports a CML (Chemical Markup Language) document, uses version 2.0 of the CML standard."""
  doc_string = _("Imports a CML (Chemical Markup Language) document, uses version 2.0 of the CML standard.")

  def __init__( self):
    CML.CML_importer.__init__( self)
    self.CML_atom = CML2_atom
    self.CML_bond = CML2_bond


class CML2_exporter( CML.CML_exporter):
  """Exports a CML (Chemical Markup Language) document, uses version 2.0 of the CML standard."""
  doc_string = _("Exports a CML (Chemical Markup Language) document, uses version 2.0 of the CML standard.")

  def __init__( self, paper):
    CML.CML_exporter.__init__( self, paper)
    self.CML_atom = CML2_atom
    self.CML_bond = CML2_bond

  
# PLUGIN INTERFACE SPECIFICATION
name = "CML2"
extensions = [".cml",".xml"]
importer = CML2_importer
exporter = CML2_exporter
local_name = _("CML2")





## PRIVATE CLASSES AND FUNCTIONS



class CML2_atom( CML.CML_atom):

  def __init__( self, atom=None, cml=None, scaling=1.0):
    self._scaling = scaling
    self.id = None
    self.symbol = None
    self.x = None
    self.y = None
    self.z = None
    self.charge = 0
    if atom:
      self.read_atom( atom)
    elif cml:
      self.read_CML( cml)
    
  def get_CML_dom( self, doc):
    if self.not_enough_data():
      return None # raise cml_exception( "missing "+str( self.not_enough_data())+" in atom specification")
    out = doc.createElement( 'atom')
    #id
    if self.z == None:
      dom_ext.setAttributes( out, (('id', str( self.id)),
                                   ('x2', str( self.x)),
                                   ('y2', str( self.y)),
                                   ('elementType', self.symbol)))
    else:
      dom_ext.setAttributes( out, (('id', str( self.id)),
                                   ('x3', str( self.x)),
                                   ('y3', str( self.y)),
                                   ('z3', str( self.z)),
                                   ('elementType', self.symbol)))
    if self.charge:
      out.setAttribute( 'formalCharge', str( self.charge))
    return out

  #def not_enough_data( self):
  #  CML.CML_atom.not_enough_data( self)

  #def read_atom( self, atom):
  #  CML.CML_atom.read_atom( self, atom)

  def read_CML( self, cml):
    if cml.getAttribute( 'id'):
      self.id = cml.getAttribute( 'id')
    if cml.getAttribute( 'formalCharge'):
      self.charge = int( cml.getAttribute( 'formalCharge'))
    if cml.getAttribute( 'elementType'):
      self.symbol = cml.getAttribute( 'elementType')
    if cml.getAttribute( 'x3'):
      self.x = float( cml.getAttribute( 'x3'))
    if cml.getAttribute( 'y3'):
      self.y = float( cml.getAttribute( 'y3'))
    if cml.getAttribute( 'z3'):
      self.z = float( cml.getAttribute( 'z3'))
    if cml.getAttribute( 'x2'):
      self.x = float( cml.getAttribute( 'x2'))
    if cml.getAttribute( 'y2'):
      self.y = float( cml.getAttribute( 'y2'))



class CML2_bond( CML.CML_bond):

  def __init__( self, bond=None, cml=None):
    self.order = 1
    self.stereo = 'n'
    self.atom1 = None
    self.atom2 = None
    if bond:
      self.read_bond( bond)
    elif cml:
      self.read_CML( cml)

    
  def get_CML_dom( self, doc):
    if self.not_enough_data():
      return None
    out = doc.createElement( 'bond')
    out.setAttribute('order', str( self.order))    
    if self.stereo:
      dom_ext.textOnlyElementUnder( out, 'stereo', self.stereo)
    out.setAttribute( 'atomRefs2', '%s %s' % ( str( self.atom1), str( self.atom2)))

    return out

  def read_CML( self, cml):
    if cml.getAttribute( 'order'):
      self.order = cml.getAttribute( 'order')
      if self.order.isdigit():
        self.order = int( self.order)
      else:
        types = ['s','d','t']
        if self.order.lower() in types:
          self.order = types.index( self.order.lower()) + 1
        else:
          raise plugin.import_exception("unknown bond type %s" % self.order)
    if cml.getAttribute( 'atomRefs2'):
      atoms = cml.getAttribute( 'atomRefs2').split( ' ')
      if len( atoms) == 2:
        self.atom1, self.atom2 = atoms
    stereo = cml.getElementsByTagName( 'stereo')
    if stereo:
      stereo = stereo[0]
      text = dom_ext.getTextFromElement( stereo)
      if text.lower() in 'wh':
        self.stereo = text.lower()
      else:
        self.stereo = 'n'

class cml_exception( Exception):
  def __init__( self, value):
    self.value = value

  def __str__( self):
    return self.value

  
