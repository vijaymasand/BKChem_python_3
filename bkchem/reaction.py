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


from . import dom_extensions
import sys
    
from .singleton_store import Store



singulars = ['reactant', 'product', 'arrow', 'condition', 'plus']
plurals = ['reactants', 'products', 'arrows', 'conditions', 'pluses']



class reaction( object):


  def __init__( self):
    self.reactants = []
    self.products = []
    self.arrows = []
    self.conditions = []
    self.pluses = []



  def add_reactant( self, mol):
    self.reactants.append( mol)

    

  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    e = doc.createElement( 'reaction')
    for i in range( len( singulars)):
      for m in self.__dict__[ plurals[i]]:
        el = doc.createElement( singulars[i])
        el.setAttribute( 'idref', m.id)
        e.appendChild( el)

    return e


  def is_empty( self):
    for name in ('reactants','products','conditions', 'pluses'):
      if self.__dict__[ name]:
        return 0
    return 1


  def read_package( self, doc):
    for el in dom_extensions.childNodesWithoutEmptySpaces( doc):
      if el.nodeName in singulars:
        i = singulars.index( el.nodeName)
        self.__dict__[ plurals[ i]].append( Store.id_manager.get_object_with_id( el.getAttribute( 'idref')))

    

  def check_the_references( self, available):
    for name in ('reactants','products','conditions', 'pluses'):
      for obj in self.__dict__[ name]:
        if obj not in available:
          self.__dict__[ name].remove( obj)
