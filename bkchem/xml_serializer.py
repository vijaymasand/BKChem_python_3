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


to_serialize = { 'paper': ('molecules',),
                 'molecule': ('atoms','bonds'),
                 'atom': ('x','y','name','type'),
                 'bond': ('type','order','atom1','atom2')
                 }

import types
import xml.dom.minidom as dom


def serialize( o, doc, parent_element):
  e = doc.createElement( o.object_type)
  parent_element.appendChild( e)
  if o.object_type in to_serialize:
    for i in to_serialize[ o.object_type]:
      # get the value
      if i in o.__dict__:
        v = o.__dict__[ i]
      elif i in o.__class__.__dict__:
        v = o.__class__.__dict__[ i].fget( o)
      # serialize it
      if type(v) == types.object: 
        serialize( v, doc, e)
      elif type(v) in (list, tuple):
        [serialize( j, doc, e) for j in v]
      else:
        e.setAttribute( i, str( v))
    
    
    
