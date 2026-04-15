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

"""provides external_data_manager class, which takes care of reading external data
specification, stores the references between objects and data and saves the data
to CDML"""


from .atom import atom
from .bond import bond
from .textatom import textatom
from .queryatom import queryatom
from .group import group
from .molecule import molecule
import types
from . import dom_extensions as dom_ext
import xml.dom.minidom as dom
import os.path
from . import os_support

from .singleton_store import Store



class external_data_manager( object):

  types = {'atom': (atom,group,textatom,queryatom),
           'bond': (bond,),
           'molecule': (molecule,),
           'int': (int,),
           #'toplevel': ('molecule', 'arrow', 'plus', 'text', 'rect', 'oval', 'polygon', 'circle', 'square', 'reaction','polyline')
           }
           

  reference_types = ("atom", "molecule", "bond")


  def __init__( self):
    self.records = {}
    self.definitions = {}


  def load_available_definitions( self):
    dir = os_support.get_bkchem_private_dir()
    dir = os.path.join( dir, 'definitions')
    if not os.path.isdir( dir):
      return []
    for name in os.listdir( dir):
      base, ext = os.path.splitext( name)
      if ext == ".xml":
        #try:
        self.read_data_definition( os.path.join( dir, name))
        #except:
        #  Store.log( "could not load definition file: %s", message_type="error")
        

    return self.definitions.keys()



  def read_data_definition( self, filename):
    doc = dom.parse( filename)
    root = doc.childNodes[0]
    for ecls in dom_ext.simpleXPathSearch( root, "class"):
      cls = ecls.getAttribute( 'name')
      self.definitions[ cls] = {}
      for eobj in dom_ext.simpleXPathSearch( ecls, "object"):
        obj = eobj.getAttribute( 'type')
        self.definitions[ cls][ obj] = {}
        for evalue in dom_ext.simpleXPathSearch( eobj, "value"):
          vname = evalue.getAttribute( 'name')
          vtype = evalue.getAttribute( 'type')
          # try to decode list style types
          if vtype.startswith( "[") and vtype.endswith( "]"):
            try:
              vtype = eval( vtype)
            except ValueError:
              pass
          text = dom_ext.getAllTextFromElement( dom_ext.getFirstChildNamed( evalue, "text"))
          self.definitions[ cls][ obj][ vname] = {'type': vtype,
                                                  'text': text }

    self.records[ cls] = {}



  def get_definitions_for_class_and_type( self, def_class, item_type):
    dclass = self.definitions.get( def_class, None)
    if dclass:
      return dclass.get( item_type, None)
    else:
      return None


  def get_definition_classes( self):
    return self.definitions.keys()



  def set_data( self, dclass, obj, category, value):
    """sets the data into the internal dictionary"""
    if self.value_matches_definition( dclass, obj, category, value):
      if not obj in self.records[ dclass]:
        self.records[ dclass][ obj] = {}
      # the type should be...
      t = self.definitions[ dclass][ obj.object_type][ category]['type']
      try:
        self.records[ dclass][ obj][ category] = self.convert_to_type( value, t)
      except ValueError:
        raise ValueError("the value '%s' type does not match the definition." % str( value))
    else:
      raise ValueError("the value '%s' type does not match the definition." % str( value))
    


  def get_data( self, dclass, obj, category):
    """gets data for an object from the internal dictionary,
    returns None if such data are not available for that object"""
    if dclass in self.records:
      if obj in self.records[ dclass]:
        if category in self.records[ dclass][ obj]:
          return self.records[ dclass][ obj][ category]
        elif category in self.definitions[dclass][obj.object_type]:
          return None
        else:
          raise ValueError("wrong category '%s' for type '%s' in dclass '%s'" % ( category, obj.object_type, dclass))
      elif obj.object_type in self.definitions[dclass].keys():
        return None
      else:
        raise ValueError("wrong object type '%s' for dclass '%s'" % ( obj.object_type, dclass))
    raise ValueError("not registered dclass: %s" % dclass)
      


  def value_matches_definition( self, dclass, obj, category, value):
    """checks if the value is of the type provided in definition""" 
    if not dclass in self.records.keys():
      raise ValueError("not registered dclass: %s" % dclass)
    if not obj.object_type in self.definitions[dclass].keys():
      raise ValueError("wrong object type '%s' for dclass '%s'" % ( obj.object_type, dclass))
    if not category in self.definitions[dclass][obj.object_type].keys():
      raise ValueError("wrong category '%s' for type '%s' in dclass '%s'" % ( category, obj.object_type, dclass))

    t = self.definitions[ dclass][ obj.object_type][ category]['type']
    if self.conforms_to_type( value, t):
      return True
    else:
      return False
    

  def conforms_to_type( self, value, t):
    if type( t) == list:
      for v2 in t:
        if value == v2:
          return True
      return False

    v = self.convert_to_type( value, t)
    if t in self.types:
      if filter( None, [isinstance( v, tt) for tt in self.types[t]]):
        return True
      else:
        return False
    else:
      return isinstance( value, t)
    



  def expand_type( self, t):
    return self.types[ t]



  def get_package( self, doc):
    if not self.records or sum( map( len, self.records.values())) == 0:
      return None
    e = doc.createElement( 'external-data')
    for dclass in self.records:
      if self.records[ dclass]:
        ecls = dom_ext.elementUnder( e, "class", (("name", dclass),))
        for obj in self.records[ dclass]:
          eobj = dom_ext.elementUnder( ecls, "object", (("ref", obj.id),("type", obj.object_type)))
          for cat in self.records[ dclass][ obj]:
            val = self.get_data( dclass, obj, cat)
            if hasattr( val, 'id'):
              val = val.id
            ecat = dom_ext.elementUnder( eobj, "value", (("category", cat),
                                                         ("value", str( val))))
    return e


  def read_package( self, root):
    """reads the data from xml (CDML) format. Is not intended for reading of definition
    files, use read_data_definition instead"""
    for ecls in dom_ext.simpleXPathSearch( root, "class"):
      cls = ecls.getAttribute( 'name')
      if not cls in self.records.keys():
        self.records[ cls] = {}
      for eobj in dom_ext.simpleXPathSearch( ecls, "object"):
        obj = Store.id_manager.get_object_with_id( eobj.getAttribute( 'ref'))
        for evalue in dom_ext.simpleXPathSearch( eobj, "value"):
          vcat = evalue.getAttribute( 'category')
          vvalue = evalue.getAttribute( 'value')
          self.set_data( cls, obj, vcat, vvalue)




  def convert_to_type( self, value, vtype):
    if type( vtype) == list:
      return value
    if vtype in types.__dict__:
      t = self.expand_type( vtype)[0]
      return t( value)
    else:
      v = Store.id_manager.get_object_with_id_or_none( value)
      if v:
        return v
      else:
        return value





from tkinter import Entry
import Pmw


class ExternalDataEntry( Entry, object):

  def __init__( self, parent, type, type_class, **kw):
    Entry.__init__( self, parent, kw)
    self.arrow = None
    self.type_class = type_class  # is one of ("internal", "reference")
    self.type = type
    #self.value = None


  def _set_value( self, value):
    self.delete( 0, last='end')
    if value != None:
      self._value = value
      self.insert( 0, str( self._value))

  def _get_value( self):
    return self.get()

  value = property( _get_value, _set_value, None, "value of the Entry, str() is run on it when displaying")



  def cleanup( self, paper):
    if self.arrow:
      paper.delete( self.arrow)
      self.arrow = None
    


class ExternalDataList( Pmw.OptionMenu, object):

  def __init__( self, parent, type, **kw):
    Pmw.OptionMenu.__init__( self, parent, **kw)
    self.type_class = "reference"
    self.arrow = None
    self.type = type

  def _set_value( self, value):
    if value:
      self.setvalue( value)
    else:
      self.setvalue( "")

  def _get_value( self):
    return self.getvalue()

  value = property( _get_value, _set_value, None, "value of the List")


  def cleanup( self, paper):
    if self.arrow:
      paper.delete( self.arrow)
      self.arrow = None
    


class ExternalDataListSelection( Pmw.RadioSelect, object):
  
  def __init__( self, parent, type, **kw):
    Pmw.RadioSelect.__init__( self, parent, **kw)
    for t in type:
      self.add( t)
    self.type_class = "internal"
    self.arrow = None
    self.type = type

  def _set_value( self, value):
    if value:
      self.invoke( value)


  def _get_value( self):
    return self.getvalue()

  value = property( _get_value, _set_value, None, "value of the List")


  def cleanup( self, paper):
    if self.arrow:
      paper.delete( self.arrow)
      self.arrow = None
