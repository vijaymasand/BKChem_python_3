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

import xml.dom.minidom as dom
from . import dom_extensions
import os, sys


# Python 3 type names (as written by write_to_dom, i.e. type(value).__name__)
# mapped to the callable used to restore the value, plus the Python 2 names
# (StringType etc., from the types module) that old prefs.xml files may use.
# types.__dict__ no longer contains str/int/... in Python 3, so looking the
# names up there -- as the original code did -- raises KeyError on read and
# never matches on write.
_TYPE_CONVERTERS = {
  'str': str, 'StringType': str, 'unicode': str, 'UnicodeType': str,
  'int': int, 'IntType': int, 'long': int, 'LongType': int,
  'float': float, 'FloatType': float,
  'bool': bool, 'BooleanType': bool,
}

# Types stored as their repr() and restored with eval().
_CONTAINER_TYPES = ("list", "tuple", "dict",
                    "ListType", "TupleType", "DictType")


def _convert_value( converter, text):
  # bool("False") is True, so bool needs an explicit parse.
  if converter is bool:
    return text.strip().lower() in ("1", "true", "yes")
  return converter( text)



class pref_manager( object):



  def __init__( self, file_names=None):
    self.data = {}
    if file_names:
      for file_name in file_names:
        self.read_pref_file( file_name)




  def add_preference( self, name, value):
    self.data[ name] = value


  def remove_preference( self, name):
    if name in self.data:
      del self.data[ name]


  def get_preference( self, name):
    if name in self.data:
      return self.data[ name]
    else:
      return None



  def has_preference( self, name):
    return name in self.data



  def read_pref_file( self, name):
    if name and os.path.exists( name):
      try:
        doc = dom.parse( name)
      except:
        #print "corrupt preference file %s" % name
        return 
      self.read_from_dom( doc)



  def read_from_dom( self, doc):
    tops = doc.getElementsByTagName( "bkchem-prefs")
    if not tops:
      return
    top = tops[0]
    for child in dom_extensions.childNodesWithoutEmptySpaces( top):
      name = child.nodeName
      text = dom_extensions.getAllTextFromElement( child)
      # A missing type attribute means a plain string. Unknown type names
      # also fall back to str instead of raising KeyError and losing
      # every preference in the file.
      itype = child.getAttribute( 'type') or 'str'
      try:
        if itype in _CONTAINER_TYPES:
          value = eval( text)
        else:
          value = _convert_value( _TYPE_CONVERTERS.get( itype, str), text)
      except:
        print("Preference manager: ignoring value %s of type %s" % (text, itype), file=sys.stderr)
        # Skip only this value; the original 'break' discarded all
        # preferences stored after a single bad one.
        continue
      self.add_preference( name, value)




  def write_to_dom( self, doc=None):
    if not doc:
      doc = dom.Document()

    top = doc.createElement( "bkchem-prefs")
    doc.appendChild( top)

    for k, v in self.data.items():
      # Python 3: the type name is simply type(v).__name__ ('str', 'int',
      # 'bool', ...). str has no .decode() in Python 3 -- calling it was
      # what made every save fail with AttributeError.
      itype = type( v).__name__
      text = repr( v) if isinstance( v, (list, tuple, dict)) else str( v)
      el = dom_extensions.textOnlyElementUnder( top, k, text,
                                                attributes = (("type", itype),))
    return doc


  def write_to_file( self, f):
    try:
      data = self.write_to_dom().toxml().encode('utf-8')
      try:
        f.write( data)
      except TypeError:
        # Caller opened the file in text mode (save_configuration() uses
        # get_opened_config_file(..., mode="w")): write str, not bytes.
        f.write( data.decode('utf-8'))
    except:
      print("failed to write to the personal preference file")
