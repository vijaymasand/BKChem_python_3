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


"""home of the molecule class"""



from math import atan2, sin, cos, pi, sqrt
import operator
from . import misc
import time
from .oasa import geometry
from warnings import warn
from . import dom_extensions
import xml.dom.minidom as dom
from .oasa import periodic_table as PT
from . import groups_table as GT
import copy
from . import helper_graphics as hg
from .parents import container, top_level, id_enabled, with_paper
from .bond import bond
from .atom import atom
from .group import group
from .textatom import textatom
from .queryatom import queryatom
from .fragment import fragment
from . import bkchem_exceptions





from . import oasa

from .singleton_store import Store, Screen
from functools import reduce



class molecule( container, top_level, id_enabled, oasa.molecule, with_paper):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ
  
  object_type = 'molecule'
  # other meta infos
  meta__is_container = 1
  # undo meta infos
  meta__undo_simple = ('name',)
  meta__undo_properties = ('id',)
  meta__undo_copy = ('atoms', 'bonds', 'fragments')
  meta__undo_children_to_record = ('atoms','bonds','fragments')
  
  def __init__( self, paper=None, package = None):
    oasa.molecule.__init__( self)
    id_enabled.__init__( self)
    container.__init__( self)

    self.paper = paper
    self.sign = 1
    self.user_data = []

    self._last_used_atom = None 
    self.name = ''
    self._iterator = 0
    self.t_bond_first = None  # template
    self.t_bond_second = None
    self.t_atom = None
    self.display_form = ''  # this is a (html like) text that defines how to present the molecule in linear form
    self.fragments = set()
    if package:
      self.read_package( package)


  def __iter__( self):
    return self.children_generator()

  def children_generator( self):
    for a in self.atoms:
      yield a
    for a in self.bonds:
      yield a


  ### PROPERTIES

  # shape_defining_points
  def _get_shape_defining_points( self):
    return self.atoms

  shape_defining_points = property( _get_shape_defining_points, None, None,
                                    "returns list of atoms")


  # children
  def _get_children( self):
    return self.atoms + list( self.bonds)

  children = property( _get_children, None, None,
                       "returns list of atoms and bonds")



  ### // PROPERTIES


  ## OVERRIDES THE OASA.GRAPH METHODS

  def create_graph( self):
    return molecule( paper=self.paper)


  def create_vertex( self, vertex_class=None):
    if not vertex_class:
      vertex_class = atom
    std = self.paper and self.paper.standard or Store.app.paper.standard
    return vertex_class( standard=std)


  def create_edge( self):
    std = self.paper and self.paper.standard or Store.app.paper.standard
    return bond( standard=std)


  def add_vertex( self, v=None):
    x = oasa.molecule.add_vertex( self, v=v)
    x.molecule = self
    return x


  def add_edge( self, v1, v2, e=None):
    x = oasa.molecule.add_edge( self, v1, v2, e=e)
    x.molecule = self
    return x


  ## LOOK
  def eat_molecule( self, mol):
    "transfers everything from mol to self, now only calls feed_data"
    self.insert_a_graph( mol)
    for v in mol.children:
      v.molecule = self


  def add_atom_to( self, a1, bond_to_use=None, pos=None):
    """adds new atom bound to atom id with bond, the position of new atom can be specified in pos or is
    decided calling find_place(), if x, y is specified and matches already existing atom it will be
    used instead of creating new one """
    if pos != None:
      x, y = pos
    else:
      if bond_to_use:
        x, y = self.find_place( a1, Screen.any_to_px( self.paper.standard.bond_length), added_order=bond_to_use.order)
      else:
        x, y = self.find_place( a1, Screen.any_to_px( self.paper.standard.bond_length))
    a2 = None # the new atom
    if pos:
      # try if the coordinates are the same as of another atom
      for at in self.atoms:
        if abs( at.x - x) < 2 and abs( at.y - y) < 2 and not at == a1:
          a2 = at
          break
    if not a2:
      a2 = self.create_new_atom( x, y)
    b = bond_to_use or bond( self.paper.standard, order=1, type='n')
    self.add_edge( a1, a2, e=b)
    b.molecule = self
    b.draw()
    return a2, b


  def find_place( self, a, distance, added_order=1):
    """tries to find accurate place for next atom around atom 'id',
    returns x,y and list of ids of 'items' found there for overlap, those atoms are not bound to id"""
    ids_bonds = a.neighbors
    if len( ids_bonds) == 0:
      x = a.x + cos( pi/6) *distance
      y = a.y - sin( pi/6) *distance
    elif len( ids_bonds) == 1:
      neigh = ids_bonds[0]
      if a.neighbor_edges[0].order != 3 and added_order != 3:
        # we add a normal bond to atom with one normal bond
        if a == self._last_used_atom or len( neigh.neighbors) != 2:
          # the user has either deleted the last added bond and wants it to be on the other side
          # or it is simply impossible to define a transoid configuration
          self.sign = -self.sign
          x = a.x + cos( self.get_angle( a, ids_bonds[0]) +self.sign*2*pi/3) *distance
          y = a.y + sin( self.get_angle( a, ids_bonds[0]) +self.sign*2*pi/3) *distance
        else:
          # we would add the new bond transoid
          neighs2 = neigh.neighbors
          neigh2 = (neighs2[0] == a) and neighs2[1] or neighs2[0]
          x = a.x + cos( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
          y = a.y + sin( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
          side = geometry.on_which_side_is_point( (neigh.x,neigh.y,a.x,a.y), (x,y))
          if side == geometry.on_which_side_is_point(  (neigh.x,neigh.y,a.x,a.y), (neigh2.x,neigh2.y)):
            self.sign = -self.sign
            x = a.x + cos( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
            y = a.y + sin( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
          self._last_used_atom = a
      else:
        x = a.x + cos( self.get_angle( a, ids_bonds[0]) + pi) *distance
        y = a.y + sin( self.get_angle( a, ids_bonds[0]) + pi) *distance
    else:
      x, y = self.find_least_crowded_place_around_atom( a, range=distance)
    return x, y



  def get_angle( self, a1, a2):
    "what is the angle between horizontal line through i1 and i1-i2 line"
    a = a2.x - a1.x
    b = a2.y - a1.y
    return atan2( b, a)


    
  def delete_items( self, items, redraw=1, delete_single_atom=1):
    """deletes items and also makes cleaning of orphan bonds and atoms"""
    if not items:
      return items, []     # quick way to avoid costly evaluation
    deleted = copy.copy( items)
    for o in items:
      if o.object_type == 'atom':
        self.delete_atom( o)
      else:
        self.delete_bond( o)
    if self.atoms:
      # delete bonds that are not in connect anymore
      bonds_in_connect = set()
      for a in self.atoms:
        for (e,v) in a.get_neighbor_edge_pairs():
          if v in self.atoms:
            bonds_in_connect.add( e)
      deleted += [self.delete_bond( o) for o in (self.bonds - bonds_in_connect)]
      # delete also orphan atoms
      if delete_single_atom:
        atms = [o for o in self.atoms if len(o.neighbors) == 0]
        deleted += [self.delete_atom( o) for o in atms]
      # recalculation of second line of double bond position, optimized to do it only when realy
      # necessary, because its pretty expensive
      # check_integrity should be called before redrawing, because it moves atoms and bonds
      # to new molecules when the molecule is spit and avoids working on non-connected graph
      offspring = self.check_integrity()
      if redraw:
        bonds_to_redraw = []
        for b in deleted:
          if b.object_type == 'bond':
            for a in b.atoms:
              if a in self.atoms:
                bonds_to_redraw.extend( a.neighbor_edges)
        [o.redraw( recalc_side=1) for o in misc.filter_unique( bonds_to_redraw) if o.order == 2 and o.item]
        [o.decide_pos() for o in self.atoms if isinstance( o, atom)]
        [o.redraw() for o in self.atoms]
    else:
      offspring = self.check_integrity()
      deleted += map( self.delete_bond, copy.copy( self.bonds))
    return deleted, offspring

  def delete_bond( self, item):
    item.delete()
    self.disconnect_edge( item)
    return item
      
  def delete_atom( self, item):
    "remove links to atom from molecule records"
    self.vertices.remove( item)
    item.delete()
    if item == self.t_atom:
      t_atom = None
    if item == self.t_bond_first:
      t_bond_first = None
    if item == self.t_bond_second:
      t_bond_second = None
    return item

  def create_new_atom( self, x, y, name=None, vertex_class=None):
    a = self.create_vertex()
    a.coords = (x, y)
    self.insert_atom( a)
    if name:
      a.set_name( name)
    a.draw()
    return a

  def insert_atom( self, at):
    "inserts atom to molecule without any connections"
    self.atoms.append( at)
    at.molecule = self
  


  def check_integrity( self):
    """after deleting atoms or bonds it is important to see if it's needed to divide molecule to fragments
    and return them in form of list of new molecules"""
    if not self.atoms:
      return []
    # first distribute atoms to new_maps
    new_maps = list( self.get_connected_components())
    if len( new_maps) == 1:
      return []
    return [self.get_induced_subgraph_from_vertices( vs) for vs in new_maps]


  def is_empty( self):
    return not len( self.atoms)


  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    # the standard
    std = self.paper and self.paper.standard or None

    self.name = package.getAttribute( 'name')
    if package.getAttribute( 'id'):
      self.id = package.getAttribute( 'id')
    for name, cls in {'atom':atom, 'group':group, 'text': textatom, 'query': queryatom}.items():
      for a in dom_extensions.simpleXPathSearch( package, name):
        self.insert_atom( cls( standard=std, package=a, molecule=self))
      
    self._id_map = [a.id for a in self.atoms]
    for b in dom_extensions.simpleXPathSearch( package, 'bond'):
      bnd = bond( standard=std, package=b, molecule=self)
      self.add_edge( bnd.atom1, bnd.atom2, bnd)
    # template related attributes
    temp = package.getElementsByTagName('template')
    if temp:
      temp = temp[0]
      self.t_atom = Store.id_manager.get_object_with_id( temp.getAttribute( 'atom'))
      if temp.getAttribute('bond_first') and temp.getAttribute('bond_second'):
        self.t_bond_first = Store.id_manager.get_object_with_id( temp.getAttribute( 'bond_first'))
        self.t_bond_second = Store.id_manager.get_object_with_id( temp.getAttribute( 'bond_second'))
      self.next_to_t_atom = self.t_atom.neighbors[0]
    # display form
    df = package.getElementsByTagName('display-form')
    if df:
      df = df[0]
      self.display_form = ''.join( [e.toxml() for e in df.childNodes]).encode('utf-8')

    # fragments
    for fel in dom_extensions.simpleXPathSearch( package, "fragment"):
      f = fragment()
      try:
        f.read_package( fel)
      except bkchem_exceptions.bkchem_fragment_error:
        pass
      else:
        self.fragments.add( f)

    ud = dom_extensions.getChildrenNamed( package, "user-data")
    if ud:
      self.user_data = [u.cloneNode( True) for u in ud]

    # final check of atoms valecies
    [a.raise_valency_to_senseful_value() for a in self.vertices if isinstance( a, atom)]
    


  def get_package( self, doc, items=None):
    if not items:
      to_export = self.children
    else:
      to_export = items
    mol = doc.createElement('molecule')
    mol.setAttribute( 'name', self.name)
    mol.setAttribute( 'id', self.id)
    if self.display_form:
      mol.appendChild( dom.parseString( '<display-form>%s</display-form>' % self.display_form).childNodes[0])
    if self.t_atom:
      if self.t_bond_second and self.t_bond_first:
        dom_extensions.elementUnder( mol, 'template', ( ('atom', str( self.t_atom.id)),
                                                        ('bond_first', str( self.t_bond_first.id)),
                                                        ('bond_second', str( self.t_bond_second.id))))
      else:
        dom_extensions.elementUnder( mol, 'template', ( ('atom', str( self.t_atom.id)),))
    for i in to_export:
      mol.appendChild( i.get_package( doc))

    if 1: #not items:
      # (we do not save fragments if the molecule is not guaranteed to be saved whole) old
      # now the approach is - you must know what you do!
      self.check_fragments()
      [mol.appendChild( f.get_package( doc)) for f in self.fragments]

    for ud in self.user_data:
      mol.appendChild( ud)

    return mol



  def draw( self, automatic="none"):
    [a.draw() for a in self.atoms]
    [a.draw( automatic=automatic) for a in copy.copy( self.bonds)]
    self.lift()
    

  ##LOOK
  def bond_between( self, a1, a2):
    "returns id of bond between atoms a1 and a2"
    return self.get_edge_between( a1, a2)


  def gen_bonds_between( self, a1, a2):
    "yields all bonds between atoms a1 and a2"
    for e in a1.get_neighbor_edges():
      if e in a2.get_neighbor_edges():
        yield e


  def handle_overlap( self):
    "deletes one of overlaping atoms and updates the bonds"
    to_delete = []
    bonds_to_check = set() # this can speedup the following for b in bonds_to_check by factor of 10 for big mols
    for i in range( len( self.atoms)):
      for j in range( i+1, len( self.atoms)):
        a = self.atoms[i]
        b = self.atoms[j]
        if (abs( a.x-b.x) < 4) and (abs( a.y-b.y) <4):
          if a not in to_delete:
            for e,v in b.get_neighbor_edge_pairs():
              e.change_atoms( b, a)
              a.add_neighbor( v, e)
              v.add_neighbor( a, e)
              bonds_to_check.add( e)
            to_delete.append( b)
    deleted = misc.filter_unique( to_delete)
    [self.delete_atom( o) for o in deleted]
    # after all is done, find and delete orphan bonds and update the others
    to_redraw = []
    bonds = set( self.bonds)
    for b in bonds_to_check:
      if not b in self.bonds:
        #print b, "not in self.bonds"
        continue
      recent_b = None
      for recent_b in self.gen_bonds_between( b.atom1, b.atom2):
        if recent_b != b:
          break
      if recent_b and recent_b != b:
        self.delete_bond( b)
        deleted.append( b)
        to_redraw.append( recent_b) # we redraw the ones that remained
      elif not recent_b:
        b.atom1.add_neighbor( b.atom2, b)
        b.atom2.add_neighbor( b.atom1, b)
        to_redraw.append( b) # we redraw this also
    for b in to_redraw:
      b.redraw()

    return deleted


  def move( self, dx, dy):
    """moves the whole molecule"""
    for o in self.atoms:
      o.move( dx, dy)
    for o in self.bonds:
      o.move( dx, dy)


  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    items = []
    for a in self.atoms:
      items.append( a.item)
    if None in items:
      # the molecule was not drawn yet, we have to calculate it, huh
      bboxes = [a.bbox() for a in self.atoms]
      return misc.smallest_common_bbox( bboxes)
    else:
      return self.paper.list_bbox( items)


  def delete( self):
    """deletes the molecule from canvas by calling delete for its children"""
    [o.delete() for o in list(self.bonds)+self.atoms]



  def redraw( self, reposition_double=0):
    for o in self.bonds:
      if o.order == 2:
        o.redraw( recalc_side=reposition_double)
      else:
        o.redraw()
    [o.redraw() for o in self.atoms]  

    
  def get_formula_dict( self):
    """returns a formula dict as defined in the periodic_table.py::formula_dict"""
    comp = PT.formula_dict()
    for a in self.atoms:
      comp += a.get_formula_dict()
    return comp



  def expand_groups( self, atoms=[]):
    """expands all group atoms; optional atoms selects atoms to expand - all used if not present"""
    names = Store.gm.get_template_names()
    if not atoms:
      map = copy.copy( self.atoms) # need to do that because the self.atoms gets changed during the cycle
    else:
      map = atoms # only selected atoms
    for a in map:
      if isinstance( a, group):
        to_draw = a.expand() or []
        [o.draw() for o in to_draw]
        a.delete()
        # creating a fragment for implosion of the group
        edges = self.vertex_subgraph_to_edge_subgraph( to_draw)
        [e.draw() for e in edges]
        self.create_fragment( a.symbol, edges, to_draw, type="implicit")
    self.redraw()
    

  def move_bonds_between_atoms( self, a1, a2):
    """transfers all bonds from one atom to the other; both atoms must be in self"""
    for (e,v) in a1.get_neighbor_edge_pairs():
      a2.add_neighbor( v,e)
      v.add_neighbor( a2, e)
      e.change_atoms( a1, a2)


  def replace_vertices( self, old, new):
    """replaces the vertex old with the vertex new"""
    self.add_vertex( new)
    self.move_bonds_between_atoms( old, new)
    self.delete_vertex( old)
    # change the references to the vertex in fragments as well
    for f in self.fragments:
      if old in f.vertices:
        f.vertices.remove( old)
        f.vertices.add( new)



  def lift( self):
    [o.lift_selector() for o in self.atoms]
    [o.lift() for o in self.bonds]
    [o.lift() for o in self.atoms]

  def find_least_crowded_place_around_atom( self, a, range=10):
    atms = a.neighbors
    x, y = a.get_xy()
    if not atms:
      # single atom molecule
      if a.show_hydrogens and a.pos == "center-first":
        return x -range, y
      else:
        return x +range, y
    angles = [geometry.clockwise_angle_from_east( at.x-a.x, at.y-a.y) for at in atms]
    angles.append( 2*pi + min( angles))
    angles.sort()
    angles.reverse()
    diffs = misc.list_difference( angles)
    i = diffs.index( max( diffs))
    angle = (angles[i] +angles[i+1]) / 2
    return x +range*cos( angle), y +range*sin( angle)
    




  def flush_graph_to_file( self, name="/home/beda/oasa/oasa/mol.graph"):
    f = file( name, 'w')
    for a in self.atoms:
      f.write('%s ' % a.symbol)
    f.write('\n')
    for b in self.bonds:
      f.write('%d %d %d\n' % (b.order, self.atoms.index( b.atom1), self.atoms.index( b.atom2)))
    f.close()



  def transform( self, tr):
    """applies given transformation to its children"""
    for a in self.atoms:
      a.transform( tr)
    for b in self.bonds:
      b.transform( tr)



  def get_geometry( self):
    """returns a tuple of ((minx, miny, max, maxy), mean_bond_length)"""
    maxx, maxy, minx, miny = 4 * [None]
    for a2 in self.atoms:
      if not maxx or a2.x > maxx:
        maxx = a2.x
      if not minx or a2.x < minx:
        minx = a2.x
      if not miny or a2.y < miny:
        miny = a2.y
      if not maxy or a2.y > maxy:
        maxy = a2.y
    bond_lengths = []
    for b2 in self.bonds:
      bond_lengths.append( sqrt( (b2.atom1.x-b2.atom2.x)**2 + (b2.atom1.y-b2.atom2.y)**2))
    # rescale
    if bond_lengths:
      bl = sum( bond_lengths) / len( bond_lengths)
    else:
      bl = None
    return ((maxx,maxy,minx,miny),bl)



  def create_vertex_according_to_text( self, old, text, interpret=1):
    if not interpret:
      v = self.create_vertex( vertex_class=textatom)
      v.set_name( text)
      return v
    val = old and old.occupied_valency or 0
    # if it seems like a known group, try it first
    if val==1 and group.is_known_group( text):
      v = self.create_vertex( vertex_class=group)
      if v.set_name( text, occupied_valency=val):
        return v
    for cls in (atom, queryatom, group, textatom):
      v = self.create_vertex( vertex_class=cls)
      if v.set_name( text, occupied_valency=val):
        return v



  # fragment support

  def create_fragment( self, name, edges, vertices, type="explicit", strict=False):
    if (strict and self.defines_connected_subgraph_e( edges)) or not strict:
      nf = fragment( Store.id_manager.generate_id( "frag"), name=name, type=type)
      nf.edges = set( edges)
      nf.vertices = set( vertices)
      self.fragments.add( nf)
      return nf
    else:
      return None


  def check_fragments( self):
    """checks if all the fragments of this molecule are consistent and
    removes and returns the ones that are not"""
    todel = set()
    for f in self.fragments:
      if not f.is_consistent( self):
        todel.add( f)
    return todel


  def get_fragment_by_id( self, id):
    fs = [f for f in self.fragments if f.id == id]
    if fs:
      return fs[0]
    else:
      return None


  def delete_fragment( self, f):
    if f in self.fragments:
      self.fragments.remove( f)
      return True
    return False


  def get_fragments_with_vertex( self, v):
    fs = set()
    for f in self.fragments:
      if v in f.vertices:
        fs.add( f)
    return fs


  def get_fragments_with_edge( self, e):
    fs = set()
    for f in self.fragments:
      if e in f.edges:
        fs.add( f)
    return fs


  def check_linear_form_fragment( self, f):
    """checks the consistency of a linear_form - returns either True (consistent) or
    False (inconsistent).
    Consistent fragments are automatically redrawn"""
    from . import interactors
    if f.type == "linear_form":
      if f.edges - self.edges or f.vertices - set( self.vertices):
        # something from the fragment was deleted
        es = f.edges & self.edges
        vs = f.vertices & set( self.vertices)
        if es or vs:
          f.edges = es
          f.vertices = vs
        else:
          return False
      # the fragment should be redrawn
      try:
        interactors.atoms_to_linear_fragment( self, f.vertices, bond_length=f.properties.get( 'bond_length',0))
      except ValueError:
        # the remains of the fragment are not consistent
        return False
      else:
        return True
    return True




  # template support

  def mark_template_bond( self, b):
    if b in self.edges:
      atms = b.atom1.neighbors + b.atom2.neighbors
      atms = misc.difference( atms, [b.atom1, b.atom2])
      coords = [a.get_xy() for a in atms]
      line = b.atom1.get_xy() + b.atom2.get_xy()
      if reduce( operator.add, [geometry.on_which_side_is_point( line, xy) for xy in coords], 0) > 0:
        self.t_bond_first = b.atom1
        self.t_bond_second = b.atom2
      else:
        self.t_bond_first = b.atom2
        self.t_bond_second = b.atom1
    else:
      raise ValueError("submitted bond does not belong to this molecule")


  def mark_template_atom( self, v):
    if v in self.vertices:
      self.t_atom = v
    else:
      raise ValueError("submitted atom does not belong to this molecule")
