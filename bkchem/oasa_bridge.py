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

oasa_available = 1
try:
  from . import oasa
except ImportError:
  oasa_available = 0

from functools import reduce
from . import molecule
from . import bond
from . import atom

import math
import operator

from .singleton_store import Screen
from .oasa import transform3d


def read_smiles( text, paper):
  mol = oasa.smiles.text_to_mol( text)
  oasa.coords_generator.calculate_coords( mol, bond_length=1.0, force=1)
  return oasa_mol_to_bkchem_mol( mol, paper)

def mol_to_smiles( mol):
  m = bkchem_mol_to_oasa_mol( mol)
  m.remove_unimportant_hydrogens()
  c = oasa.smiles.converter()
  text = c.mols_to_text([m])
  return text


def read_inchi( text, paper):
  mol = oasa.inchi.text_to_mol( text, calc_coords=1, include_hydrogens=False)
  #oasa.coords_generator.calculate_coords( mol, bond_length=1.0, force=1)
  m = oasa_mol_to_bkchem_mol( mol, paper)
  return m
  
def mol_to_inchi( mol, program):
  m = bkchem_mol_to_oasa_mol( mol)
  # we do not use mol_to_text because generate_inchi_and_inchikey returns extra warning messages
  _inchi, _key, _warnings = oasa.inchi.generate_inchi_and_inchikey( m, program=program, fixed_hs=False)
  return (_inchi, _key, _warnings)


def read_molfile( file, paper):
  mol = oasa.molfile.file_to_mol( file)
  if not mol.is_connected():
    mols = mol.get_disconnected_subgraphs()
    return [oasa_mol_to_bkchem_mol( mol, paper) for mol in mols]
  else:
    return [oasa_mol_to_bkchem_mol( mol, paper)]


def write_molfile( mol, file):
  m = bkchem_mol_to_oasa_mol( mol)
  oasa.molfile.mol_to_file( m, file)

  

# ==================================================
# OASA -> BKCHEM

def oasa_mol_to_bkchem_mol( mol, paper):
  m = molecule.molecule( paper)
  if None in reduce( operator.add, [[a.x, a.y] for a in mol.atoms], []):
    calc_position = 0
  else:
    calc_position = 1
    
  minx = None
  maxx = None
  miny = None
  maxy = None
  # atoms
  for a in mol.vertices:
    a2 = oasa_atom_to_bkchem_atom( a, paper, m)
    m.insert_atom( a2)
    if calc_position:
      # data for rescaling
      if not maxx or a2.x > maxx:
        maxx = a2.x
      if not minx or a2.x < minx:
        minx = a2.x
      if not miny or a2.y < miny:
        miny = a2.y
      if not maxy or a2.y > maxy:
        maxy = a2.y
  # bonds
  bond_lengths = []
  for b in mol.edges:
    b2 = oasa_bond_to_bkchem_bond( b, paper)
    aa1, aa2 = b.vertices
    atom1 = m.atoms[ mol.vertices.index( aa1)]
    atom2 = m.atoms[ mol.vertices.index( aa2)]
    m.add_edge( atom1, atom2, b2)
    b2.molecule = m
    if calc_position:
      bond_lengths.append( math.sqrt( (b2.atom1.x-b2.atom2.x)**2 + (b2.atom1.y-b2.atom2.y)**2))
  # rescale
  if calc_position:
    bl = sum( bond_lengths) / len( bond_lengths)
    scale = Screen.any_to_px( paper.standard.bond_length) / bl
    movex = (maxx+minx)/2
    movey = (maxy+miny)/2
    trans = transform3d.transform3d()
    trans.set_move( -movex, -movey, 0)
    trans.set_scaling( scale)
    trans.set_move( 320, 240, 0)
    for a in m.atoms:
      a.x, a.y, a.z = trans.transform_xyz( a.x, a.y, a.z)
  return m


def oasa_atom_to_bkchem_atom( a, paper, m):
  at = atom.atom( standard=paper.standard, molecule=m)
  at.x = a.x
  at.y = a.y
  at.z = a.z
  at.set_name( a.symbol, interpret=1)
  at.charge = a.charge
  at.number = a.properties_.get( 'inchi_number', None)
  at.show_number = False
  at.isotope = a.isotope
  at.valency = a.valency
  at.multiplicity = at.multiplicity
  return at

def oasa_bond_to_bkchem_bond( b, paper):
  bo = bond.bond( standard=paper.standard)
  bo.type = b.type
  bo.order = b.order
  return bo


# ==================================================
# BKCHEM -> OASA

def bkchem_mol_to_oasa_mol( mol):
  m = oasa.molecule()
  for a in mol.atoms:
    m.add_vertex( bkchem_atom_to_oasa_atom( a))
  for b in mol.bonds:
    b2 = bkchem_bond_to_oasa_bond( b)
    aa1, aa2 = b.atoms
    v1 = m.vertices[ mol.atoms.index( aa1)]
    v2 = m.vertices[ mol.atoms.index( aa2)]
    b2.vertices = (v1, v2)
    m.add_edge( v1, v2, b2)
  return m




def bkchem_atom_to_oasa_atom( a):
  s = a.symbol
  ret = oasa.atom( symbol=s)
  x, y, z = a.get_xyz()
  ret.x = x
  ret.y = y
  ret.z = z
  ret.charge = a.charge
  ret.multiplicity = a.multiplicity
  ret.valency = a.valency
  if hasattr(a,'isotope'):
    ret.isotope = a.isotope
  return ret

def bkchem_bond_to_oasa_bond( b):
  ret = oasa.bond( order=b.order, type=b.type)
  return ret



### TODO

# coordinates transformations
