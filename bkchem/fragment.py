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



from . import dom_extensions as dom_ext
import xml.sax.saxutils
from .singleton_store import Store
from .parents import simple_parent
from .bkchem_exceptions import bkchem_fragment_error
import types


class fragment( simple_parent):

  meta__undo_properties = ('name', 'id')
  meta__undo_copy = ('edges', 'vertices', 'properties')
  meta__allowed_type = ('implicit', 'explicit', 'linear_form')
  # implicit - created by bkchem without users request - to mark expanded groups etc.
  # explicit - created by user
  # linear_form - used to track linear forms

  

  def __init__( self, id="", name="", type="explicit", strict=True):
    self.id = id
    self.name = name
    self.edges = set()
    self.vertices = set()
    self.strict = strict # strict fragment must be a continuos subgraph, otherwise it is just a mixture of vertices and edges
    self.type = type # type is one of "explicit", "implicit", "linear_form" or custom string
    self.properties = {}  # this is the place for information about an particular fragment
    

  # properties

  def _get_name( self):
    return self._name

  def _set_name( self, name):
    self._name = name

  name = property( _get_name, _set_name, None, "name of the fragment")


  def _get_id( self):
    return self._id

  def _set_id( self, id):
    self._id = id

  id = property( _get_id, _set_id, None, "id of the fragment")




  def is_consistent( self, molecule):
    for e in self.edges:
      if e not in molecule.edges:
        return False
    for v in self.vertices:
      if v not in molecule.vertices:
        return False
    return True
  


  def get_all_vertices( self):
    vs = set( self.vertices)
    #for e in self.edges:
    #  vs |= set( e.vertices)
    return vs

  # property for easier manipulation
  all_vertices = property( get_all_vertices, None, None, "the vertices associated with fragment bonds")



  def get_package( self, doc):
    el = doc.createElement( "fragment")
    el.setAttribute( "id", self.id)
    el.setAttribute( "type", self.type)
    dom_ext.textOnlyElementUnder( el, "name", xml.sax.saxutils.escape( self.name))
    for e in self.edges:
      dom_ext.elementUnder( el, "bond", (("id", e.id),))
    for v in self.vertices:
      dom_ext.elementUnder( el, "vertex", (("id", v.id),))
    for k, v in self.properties.items():
      itype = 'str'
      for tn in types.__dict__:
        if type( v) == types.__dict__[ tn]:
          itype = tn
          break
      dom_ext.elementUnder( el, "property", (("name",str( k)),
                                             ("value",str( v)),
                                             ("type", itype)))
    return el



  def read_package( self, doc):
    self.id = doc.getAttribute( "id")
    self.type = doc.getAttribute( "type") or "explicit"
    name = dom_ext.getFirstChildNamed( doc, "name")
    if name:
      self.name = dom_ext.getAllTextFromElement( name)
    for b in dom_ext.simpleXPathSearch( doc, "bond"):
      try:
        self.edges.add( Store.id_manager.get_object_with_id( b.getAttribute( "id")))
      except KeyError:
        raise bkchem_fragment_error( "inconsistent", "")

    for v in dom_ext.simpleXPathSearch( doc, "vertex"):
      try:
        self.vertices.add( Store.id_manager.get_object_with_id( v.getAttribute( "id")))
      except KeyError:
        raise bkchem_fragment_error( "inconsistent", "")

    for p in dom_ext.simpleXPathSearch( doc, "property"):
      k = p.getAttribute( "name")
      v = p.getAttribute( "value")
      t = p.getAttribute( "type")
      typ = types.__dict__[ t]
      self.properties[k] = typ( v)
