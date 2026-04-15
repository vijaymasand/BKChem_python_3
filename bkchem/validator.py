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

"""provides validator class that checks chemistry"""

import types
from .atom import atom
from .group import group
from .textatom import textatom
from . import molecule
from . import misc


class validator:

  def __init__( self):
    self.report = None

  def start_new_report( self):
    self.report = validator_report()

  def validate( self, o):
    self.start_new_report()
    self.validate_object( o)

  def validate_object( self, o):
    if type( o) == list:
      self.validate_list( o)
    elif misc.isinstance_of_one( o, (atom,group,textatom)):
      self.validate_atom( o)
    elif isinstance( o, molecule.molecule):
      self.validate_molecule( o)

  def validate_atom( self, a):
    if isinstance( a, textatom):
      self.report.text_atoms.append( a)
    elif isinstance( a, group):
      self.report.group_atoms.append( a)
    else:
      fval = a.free_valency
      if fval < 0:
        self.report.exceeded_valency.append( a)

  def validate_bond( self, b):
    if b.order == 0:
      self.report.zero_order_bonds.append( b)


  def validate_molecule( self, mol):
    map( self.validate_atom, mol.atoms)
    map( self.validate_bond, mol.bonds)

  def validate_list( self, objs):
    [self.validate_object( o) for o in objs]


class validator_report:

  def __init__( self):
    #self._report_text = ""
    self.text_atoms = []
    self.group_atoms = []
    self.exceeded_valency = []
    self.zero_order_bonds = []

  def get_text_report( self):
    pass

  def get_summary( self):
    out = ""
    if self.text_atoms:
      out += ngettext(
        "%d text only atom (chemical interpretation is unknown)",
        "%d text only atoms (chemical interpretation is unknown)",
        len(self.text_atoms)) % len(self.text_atoms)
      out += "\n"
    if self.exceeded_valency:
      out += ngettext("%d atom with exceeded valency",
                      "%d atoms with exceeded valency",
                      len(self.exceeded_valency)) % len(self.exceeded_valency)
      out += "\n"
    if self.group_atoms:
      out += ngettext(
        "%d group(s) (groups need to be expanded for some export formats)",
        "%d group(s) (groups need to be expanded for some export formats)",
        len(self.group_atoms)) % len(self.group_atoms)
      out += "\n"
    if self.zero_order_bonds:
      out += ngettext(
        "%d zero order bond "
        "(such bond will not be exported into chemical formats)",
        "%d zero order bonds "
        "(such bonds will not be exported into chemical formats)",
        len(self.zero_order_bonds)) % len(self.zero_order_bonds)
    if not out:
      out = _("OK")
    return out
