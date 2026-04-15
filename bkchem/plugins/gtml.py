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


"""GTML import-export plugin"""

from . import plugin
from molecule import molecule
from atom import atom
from bond import bond
from classes import plus, arrow
from reaction import reaction
from .oasa.oasa.transform import transform

import math
import xml.sax
from io import StringIO
import dom_extensions as dom_ext
import xml.dom.minidom as dom
from xml import xpath



gtml_to_bkchem_bond_order_remap = ['empty','single','double','triple']


## DEFINITIONS

class gtml_importer:

  gives_molecule = 1
  gives_cdml = 0



  def __init__( self, paper):
    self.paper = paper
    self._atom_id_remap = {}
    self._mol_ids = {}
    self._reactions = []
    self._xshift = 20


  def on_begin( self):
    """this method is called before every import"""
    return 1




  def get_molecules( self, file_name):
    self.molecules = []

    # prepare the file to resolve entities
    f = StringIO()
    f.write( "<!DOCTYPE item [")
    entities = file( 'mathmlentities.ent')
    f.write( entities.read())
    entities.close()
    f.write( "<!ENTITY epsilon '&#x3B5;'><!ENTITY nevim '&amp;nevim;'>]>")

    the_file = file( file_name)
    f.write( the_file.read())
    the_file.close()
    f.seek(0)
    
    doc = dom.parse( f)
    f.close()


    for ch in xpath.Evaluate( "//graph[@type='molecule']", doc):
      m = self._read_molecule( ch)
      self.molecules.append( m)

    # reactions
    self.process_reactions( doc)

    # placing the molecules
    self.place_molecules()

    # things that have to be done after the whole molecule is read and placed
    for m in self.molecules:
      if isinstance( m, molecule):
        [a.generate_marks_from_cheminfo() for a in m.atoms]

    return self.molecules





  def _read_molecule( self, el):
    m = molecule( self.paper)
    for v in xpath.Evaluate( "vertex", el):
      a2 = self._read_atom( v, m)
      m.insert_atom( a2)
      # bonds
      bond_lengths = []
    for b in xpath.Evaluate("edge", el):
      b2 = self._read_bond( b)
      b2.molecule = m
      m.add_edge( b2.atom1, b2.atom2, b2)

    self._mol_ids[ el.getAttribute( 'id')] = m
    return m




  def _read_atom( self, at, mol):
    a = atom( self.paper, molecule=mol)
    a.set_name( dom_ext.getAllTextFromElement( dom_ext.getFirstChildNamed( at, "symbol")))
    coords = dom_ext.getFirstChildNamed( at, "coordinates")
    a.x = float( dom_ext.getAllTextFromElement( dom_ext.getFirstChildNamed( coords, "x")))
    a.y = float( dom_ext.getAllTextFromElement( dom_ext.getFirstChildNamed( coords, "y")))
    a.z = float( dom_ext.getAllTextFromElement( dom_ext.getFirstChildNamed( coords, "z")))
    a.show_hydrogens = int( a.name != 'C')
    # charge
    chel = dom_ext.getFirstChildNamed( at, "charge")
    if chel:
      a.charge = int( dom_ext.getAllTextFromElement( chel))
    # multiplicity
    radical = dom_ext.getFirstChildNamed( at, "radical")
    if radical:
      a.multiplicity = 1 + int( dom_ext.getAllTextFromElement( radical))
    # remap of ids
    self._atom_id_remap[ at.getAttribute( 'id')] = a
    return a



  def _read_bond( self, bo):
    b = bond( self.paper)
    b.order = gtml_to_bkchem_bond_order_remap.index( dom_ext.getAllTextFromElement( xpath.Evaluate("bond", bo)[0]))
    ids = [i.nodeValue for i in xpath.Evaluate( "end/@idref", bo)]
    b.atoms = [self._atom_id_remap[ i] for i in ids]
    return b



  def place_molecules( self):
    last_anchor_x = 80
    last_anchor_y = 200
    # data for rescaling
    if self._reactions:
      for react in self._reactions:
        reactants, products = react  # these are ids
        plus_objs = []
        for part in (reactants, products):
          for id in part:
            m = self._mol_ids[ id]
            last_anchor_x = self._scale_and_move_molecule( m, last_anchor_x, last_anchor_y)
            last_anchor_x += self._xshift
            if id != part[-1]:
              # we add some pluses
              p = plus( self.paper, xy=(last_anchor_x, last_anchor_y))
              plus_objs.append( p)
              self.molecules.append( p)
              bbox = p.bbox()
              dx = (bbox[0] - bbox[2])
              p.move( dx / 2, 0)
              last_anchor_x += self._xshift + dx
          if part == reactants:
            arr = arrow( self.paper)
            # first point
            arr.create_new_point( last_anchor_x, last_anchor_y)
            last_anchor_x += self.paper.any_to_px( self.paper.standard.arrow_length)
            # second point
            arr.create_new_point( last_anchor_x, last_anchor_y)
            last_anchor_x += self._xshift
            # adding the reaction information into the arrow.reaction
            arr.reaction.reactants.extend( [self._mol_ids[m] for m in reactants])
            arr.reaction.products.extend( [self._mol_ids[m] for m in products])
            arr.pluses = plus_objs
            self.molecules.append( arr)
          
    else:
      for m in self.molecules:
        last_anchor_x = self._scale_and_move_molecule( m, last_anchor_x, last_anchor_y)
        last_anchor_x += self._xshift


  def _scale_and_move_molecule( self, m, anchor_x, anchor_y):
    bbox, bl = m.get_geometry()
    maxx, maxy, minx, miny = m.bbox()

    if bl:
      scale = self.paper.any_to_px( self.paper.standard.bond_length) / bl
    else:
      scale = 1

    # at first we scale to the standard bond length
    tr = transform()
    tr.set_move( -minx, -miny)
    tr.set_scaling( scale)
    m.transform( tr)

    # then we recalculate the bbox and position the molecule
    #    we need to decide pos first, it is vital for bbox calculation and normaly done on draw
    [a.decide_pos() for a in m.atoms]
    maxx, maxy, minx, miny = m.bbox()
    m.move( anchor_x-minx, anchor_y - (maxy-miny)/2 - miny)

    #import graphics
    #self.molecules.append( graphics.rect( self.paper, coords = m.bbox()))                                       
    #self.molecules.append( graphics.rect( self.paper, coords = (anchor_x + (maxx), 100, anchor_x + (maxx) + 2, 300)))

    return anchor_x + maxx - minx




  def process_reactions( self, doc):
    for react in xpath.Evaluate( "//graph[@type='reaction']", doc):
      reactants = []
      products = []
      for e in xpath.Evaluate( "edge/end[@type='initial']", react):
        id = e.getAttribute( 'idref')
        if id not in reactants:
          reactants.append( id)
      for e in xpath.Evaluate( "edge/end[@type='terminal']", react):
        id = e.getAttribute( 'idref')
        if id not in products:
          products.append( id)
      self._reactions.append( (reactants,products))
          



class gtml_exporter:

  def __init__( self, paper):
    pass

  
# PLUGIN INTERFACE SPECIFICATION
name = "GTML"
extensions = [".gtml",".xml"]
importer = gtml_importer
exporter = gtml_exporter






## PRIVATE CLASSES AND FUNCTIONS



