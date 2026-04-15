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

"""template manager resides here"""

import math
try:
  from .oasa.oasa.transform import transform
except ImportError:
  from .oasa.transform import transform
from .molecule import molecule
import xml.dom.minidom as dom
from warnings import warn
from . import config
import os.path
from . import os_support
import xml.sax
from . import misc

from .singleton_store import Store, Screen


class template_manager:
  templates = []

  def __init__( self):
    self.templates = []
    self._prepared_templates = []


  def add_template_from_CDML( self, file):
    original_file = file
    if not os.path.isfile( file):
      file = os_support.get_path( file, "template")
      if not file:
        warn( "template file %s does not exist - ignoring" % original_file)
        return
    try:
      doc = dom.parse( file).getElementsByTagName( 'cdml')[0]
    except xml.sax.SAXException: 
      warn( "template file %s cannot be parsed - ignoring" % file)
      return
    # when loading old versions of CDML try to convert them, but do nothing when they cannot be converted
    from . import CDML_versions
    CDML_versions.transform_dom_to_version( doc, config.current_CDML_version)
    added = []
    if Store.app.paper:
      Store.app.paper.onread_id_sandbox_activate()
    for tmp in doc.getElementsByTagName('molecule'):
      self.templates.append( tmp)
      if Store.app.paper:
        m = molecule( Store.app.paper, package=tmp)
        self._prepared_templates.append( m)
        added.append( m)
    if Store.app.paper:
      Store.app.paper.onread_id_sandbox_finish( apply_to=[]) # just switch the id_managers, no id mangling

  def get_template( self, n):
    return self.templates[n]

  def get_templates_valency( self, name):
    return self._prepared_templates[ name].next_to_t_atom.occupied_valency -1

  def get_template_names( self):
    # If templates aren't prepared yet, prepare them now
    if not self._prepared_templates and self.templates and Store.app and Store.app.paper:
      Store.app.paper.onread_id_sandbox_activate()
      for tmp in self.templates:
        try:
          m = molecule( Store.app.paper, package=tmp)
          self._prepared_templates.append( m)
        except:
          pass
      Store.app.paper.onread_id_sandbox_finish( apply_to=[])
    
    if self._prepared_templates:
      return [o.name for o in self._prepared_templates]
    elif self.templates:
      # Fallback to template names from XML if not prepared
      names = []
      for tmp in self.templates:
        name = tmp.getAttribute('name') or 'unnamed'
        names.append(name)
      return names
    return []

  def get_transformed_template( self, n, coords, type='empty', paper=None):
    """type is type of connection - 'bond', 'atom1'(for single atom), 'atom2'(for atom with more than 1 bond), 'empty'"""
    pap = paper or Store.app.paper
    pap.onread_id_sandbox_activate() # must be here to mangle the ids
    current = molecule( pap, package=self.templates[n])
    pap.onread_id_sandbox_finish( apply_to= [current]) # id mangling
    current.name = ''
    self._scale_ratio = 1
    trans = transform()
    # type empty - just draws the template - no conection
    if type == 'empty':
      xt1, yt1 = current.t_atom.get_xy()
      xt2, yt2 = current.next_to_t_atom.get_xy()
      x1, y1 = coords
      bond_length = Screen.any_to_px( Store.app.paper.standard.bond_length)
      current.delete_items( [current.t_atom], redraw=0, delete_single_atom=0)
      trans.set_move( -xt2, -yt2)
      trans.set_scaling( bond_length / math.sqrt( (xt1-xt2)**2 + (yt1-yt2)**2))
      trans.set_move( x1, y1)
    #type atom
    elif type == 'atom1' or type == 'atom2':
      xt1, yt1 = current.t_atom.get_xy()
      xt2, yt2 = current.next_to_t_atom.get_xy()
      x1, y1, x2, y2 = coords
      trans.set_move( -xt2, -yt2)
      trans.set_scaling( math.sqrt( (x1-x2)**2 + (y1-y2)**2) / math.sqrt( (xt1-xt2)**2 + (yt1-yt2)**2))
      trans.set_rotation( math.atan2( xt1-xt2, yt1-yt2) - math.atan2( x1-x2, y1-y2))
      trans.set_move( x2, y2)
    #type bond
    elif type == 'bond':
      if not (current.t_bond_first and current.t_bond_second):
        warn( "this template is not capable to be added to bond - sorry.")
        return None
      current.delete_items( [current.t_atom], redraw=0, delete_single_atom=0)
      xt1, yt1 = current.t_bond_first.get_xy()
      xt2, yt2 = current.t_bond_second.get_xy()
      x1, y1, x2, y2 = coords
      self._scale_ratio = math.sqrt( (x1-x2)**2 + (y1-y2)**2) / math.sqrt( (xt1-xt2)**2 + (yt1-yt2)**2) # further needed for bond.bond_width transformation
      trans.set_move( -xt1, -yt1)
      trans.set_rotation( math.atan2( xt1-xt2, yt1-yt2) - math.atan2( x1-x2, y1-y2))
      trans.set_scaling( self._scale_ratio)
      trans.set_move( x1, y1)
    self.transform_template( current, trans)
    #remove obsolete info from template
    if type == 'atom1':
      current.delete_items( [current.t_atom], redraw=0, delete_single_atom=0)
    elif type == 'atom2':
      current.t_atom.x = x1
      current.t_atom.y = y1
    current.t_atom = None
    current.t_bond_first = None
    current.t_bond_second = None
    #return ready template
    return current 
  
  def transform_template( self, temp, trans):
    for a in temp.atoms:
      a.x, a.y = trans.transform_xy( a.x, a.y)
      a.scale_font( self._scale_ratio)
    for b in temp.bonds:
      if b.order != 1:
        b.bond_width *= self._scale_ratio
    # update template according to current default values
    Store.app.paper.apply_current_standard( [temp], template_mode=1)
    # return the ready template
    return temp


