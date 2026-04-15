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


"""home of the bond class"""


import math
from . import misc
from .oasa import geometry
from warnings import warn
from .ftext import ftext
from . import dom_extensions
import xml.dom.minidom as dom
import operator
import copy
from .parents import meta_enabled, line_colored, drawable, with_line, interactive, child_with_paper
from . import debug

from . import oasa

from .singleton_store import Store, Screen
from functools import reduce


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


# class BOND--------------------------------------------------
class bond( meta_enabled, line_colored, drawable, with_line, interactive, child_with_paper, oasa.bond):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'bond'
  # these values will be automaticaly read from paper.standard on __init__
  # bond_width couldn't be because it has sign that is important
  # widths need to be calculated therefore are also not here (to be fixed)
  meta__used_standard_values = ['line_color','double_length_ratio']
  # undo related metas
  meta__undo_properties = line_colored.meta__undo_properties + \
                          with_line.meta__undo_properties + \
                          ('molecule', 'type', 'order', 'atom1', 'atom2',
                           'center', 'bond_width','double_length_ratio', 'wedge_width',
                           'simple_double','auto_bond_sign')




  def __init__( self, standard=None, atoms=(), package=None, molecule=None, type='n', order=1,
                simple_double=1):
    # initiation
    self.molecule = molecule
    oasa.bond.__init__( self, order=order, vs=atoms, type=type)
    meta_enabled.__init__( self, standard=standard)
    line_colored.__init__( self)
    drawable.__init__( self)
    with_line.__init__( self)
    # 
    self.type = type
    self.order = order
    self.item = None
    self.second = []
    self.third = []
    self.items = []
    if atoms:
      self.atom1, self.atom2 = atoms
    self.selector = None

    # implicit values
    self.center = None
    self.auto_bond_sign = 1
    self.simple_double = simple_double
    self.equithick = 0

    if package:
      self.read_package( package)



  ## ------------------------------ PROPERTIES ------------------------------


  # dirty
  # override of drawable.dirty
  def _get_dirty( self):
    return self.__dirty # or self.atom1.dirty or self.atom2.dirty

  def _set_dirty( self, dirty):
    self.__dirty = dirty

  dirty = property( _get_dirty, _set_dirty)


  # molecule
  def _get_molecule( self):
    return self.__molecule

  def _set_molecule( self, mol):
    self.__molecule = mol

  molecule = property( _get_molecule, _set_molecule)


  # type
  def _get_type( self):
    return self.__type

  def _set_type( self, mol):
    self.__type = mol
    self.__dirty = 1

  type = property( _get_type, _set_type)


  # order
  def _get_order( self):
    return self.get_order()

  def _set_order( self, mol):
    self.set_order( mol)
    self.__dirty = 1

  order = property( _get_order, _set_order)


  # atom1
  def _get_atom1( self):
    try:
      return self._vertices[0]
    except IndexError:
      return None

  def _set_atom1( self, mol):
    try:
      self._vertices[0] = mol
    except IndexError:
      self._vertices = [mol, None]
    self.__dirty = 1

  atom1 = property( _get_atom1, _set_atom1)


  # atom2
  def _get_atom2( self):
    try:
      return self._vertices[1]
    except IndexError:
      return None

  def _set_atom2( self, mol):
    try:
      self._vertices[1] = mol
    except IndexError:
      self._vertices = [None, mol]
    self.__dirty = 1

  atom2 = property( _get_atom2, _set_atom2)


  # atoms
  def _get_atoms( self):
    return self._vertices

  def _set_atoms( self, mol):
    self._vertices = mol
    self.__dirty = 1

  atoms = property( _get_atoms, _set_atoms)


  # center
  def _get_center( self):
    return self.__center

  def _set_center( self, mol):
    self.__center = mol
    self.__dirty = 1

  center = property( _get_center, _set_center)


  # bond_width
  def _get_bond_width( self):
    return self.__bond_width

  def _set_bond_width( self, mol):
    self.__bond_width = mol
    self.__dirty = 1

  bond_width = property( _get_bond_width, _set_bond_width)


  # wedge_width
  def _get_wedge_width( self):
    return self.__wedge_width

  def _set_wedge_width( self, mol):
    self.__wedge_width = mol
    self.__dirty = 1

  wedge_width = property( _get_wedge_width, _set_wedge_width)


  # simple_double
  def _get_simple_double( self):
    return self.__simple_double

  def _set_simple_double( self, mol):
    self.__simple_double = mol
    self.__dirty = 1

  simple_double = property( _get_simple_double, _set_simple_double)


  # double_length_ratio
  def _get_double_length_ratio( self):
    return self.__double_length_ratio

  def _set_double_length_ratio( self, mol):
    self.__double_length_ratio = mol
    self.__dirty = 1

  double_length_ratio = property( _get_double_length_ratio, _set_double_length_ratio)


  # auto_bond_sign
  def _get_auto_bond_sign( self):
    return self.__auto_bond_sign

  def _set_auto_bond_sign( self, mol):
    self.__auto_bond_sign = mol
    self.__dirty = 1

  auto_bond_sign = property( _get_auto_bond_sign, _set_auto_bond_sign)



  # parent
  def _get_parent( self):
    return self.molecule

  def _set_parent( self, par):
    self.molecule = par

  parent = property( _get_parent, _set_parent, None,
                     "returns self.molecule")




  ## // ------------------------------ END OF PROPERTIES --------------------





  def read_standard_values( self, standard, old_standard=None):
    meta_enabled.read_standard_values( self, standard, old_standard=old_standard)
    # wedge width
    if not old_standard or (standard.wedge_width != old_standard.wedge_width):
      self.wedge_width = Screen.any_to_px( standard.wedge_width)
    # line width
    if not old_standard or (standard.line_width != old_standard.line_width):
      self.line_width = Screen.any_to_px( standard.line_width)
    # bond width
    if not old_standard or (standard.bond_width != old_standard.bond_width):
      if hasattr( self, 'bond_width'):
        self.bond_width = misc.signum( self.bond_width) * Screen.any_to_px( standard.bond_width)
      else:
        self.bond_width = Screen.any_to_px( standard.bond_width)




  def draw( self, automatic="none"):
    """call the appropriate draw method, automatic specifies what to automatically compute -
    all, sign, none (sign is often needed to retain the look after transformation)"""
    if self.item:
      warn( "drawing bond that is probably drawn already", UserWarning, 2)
    method = "_draw_%s%d" % (self.type, self.order or 1)
    if (automatic != "none" or self.center == None) and self.order == 2:
      sign, center = self._compute_sign_and_center()
      self.bond_width = self.auto_bond_sign * sign * abs( self.bond_width)
      if automatic == "both":
        self.center = center
    # the following lines ensure proper drawing in case 3D coordinates are involved
    transform = None
    self._transform = oasa.transform3d.transform3d()
    if self.order != 1 or self.type != 'n':
      for n in self.atom1.neighbors + self.atom2.neighbors:
        # self.atom1 and self.atom2 are in this list as well
        if n.z != 0:
          # engage 3d transform prior to detection of where to draw
          transform = self._get_3dtransform_for_drawing()
          break
      if transform:
        for n in self.molecule.atoms:
          n.transform( transform)
        self._transform = transform.get_inverse()
    # / end of 3D
    # we call the draw method
    self.__class__.__dict__[ method]( self)
    # we have to cleanup after 3D stuff
    if self._transform:
      # if transform was used, we need to transform back
      for n in self.molecule.atoms:
        n.transform( self._transform)
      self._transform = None


  # THE DRAW HELPER METHODS

  def _where_to_draw_from_and_to( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    # at first check if the bboxes are not overlapping
    bbox1 = list( misc.normalize_coords( self.atom1.bbox( substract_font_descent=True)))
    bbox2 = list( misc.normalize_coords( self.atom2.bbox( substract_font_descent=True)))
    if geometry.do_rectangles_intersect( bbox1, bbox2):
      return None
    # then we continue with computation
    if self.atom1.show:
      x1, y1 = geometry.intersection_of_line_and_rect( (x1,y1,x2,y2), bbox1, round_edges=0)
    if self.atom2.show:
      x2, y2 = geometry.intersection_of_line_and_rect( (x1,y1,x2,y2), bbox2, round_edges=0)

    if geometry.point_distance( x1, y1, x2, y2) <= 1.0:
      return None
    else:
      return (x1, y1, x2, y2)



  # normal bond

  def _draw_n1( self):
    where = self._where_to_draw_from_and_to()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where
    # decide the capstyle
    if self.atom1.show or self.atom2.show:
      capstyle = "butt"
    else:
      capstyle = "round"
    # draw the item
    self.item = self._create_line_with_transform( (x1, y1, x2, y2), tags=('bond',), width=self.line_width, fill=self.line_color, capstyle=capstyle)
    # draw helper items
    self.second = self.third = []
    self.paper.register_id( self.item, self)
    return x1,y1,x2,y2

  def _draw_n2( self):
    where = self._draw_n1()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where

    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      self.paper.itemconfig( self.item, fill='')
      # d = int( round( d/3)) #MB#
      d = round(d*.4) #MB#+
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    self.second = self._draw_second_line( [x, y, x0, y0])
    if self.center:
      self.third = self._draw_second_line( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_n3( self):
    where = self._draw_n1()
    if not where:
      # the bond is too short to draw it
      return None
    if self.atom1.show and self.atom2.show:
      # both atoms are shown - we don't want round edges at the ends of the central bond
      # and we don't want to apply shortening of other lines
      self.paper.itemconfig( self.item, capstyle="butt")
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
      
    x1, y1, x2, y2 = where
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d*3/4)
    self.second = self._draw_second_line( [x, y, x0, y0])
    self.third = self._draw_second_line( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))



  def _draw_h1( self):
    where = self._draw_n1()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where
    # main item
    self.paper.itemconfig( self.item, fill='')
    # the small lines
    self.items = self._draw_hatch( (x1,y1,x2,y2))
    return x1,y1,x2,y2    

  def _draw_h2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      where = self._draw_n1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      where = self._draw_h1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where

    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_hatch
    self.second = _second_draw_method( (x,y,x0,y0))
    if self.center:
      self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_h3( self):
    where = self._draw_h1()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where

    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_hatch
    self.second = _second_draw_method( (x,y,x0,y0))
    self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_hatch( self, coords):
    """returns list items"""
    if not hasattr( self, 'equithick'): 
      self.equithick = 0                
    x1, y1, x2, y2 = coords
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.wedge_width/2.0)
    xa, ya, xb, yb = geometry.find_parallel( x1, y1, x2, y2, self.line_width/2.0) 
    d = math.sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    if d == 0:  
      return []  # to prevent division by zero
    dx1 = (x0 - xa)/d 
    dy1 = (y0 - ya)/d 
    dx2 = (2*x2 -x0 -2*x1 +xa)/d 
    dy2 = (2*y2 -y0 -2*y1 +ya)/d 
    # params for equithick	
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 
    ddx = x - x1 
    ddy = y - y1 

    # we have to decide if the first line should be at the position of the first atom
    draw_start = 0  # is index not boolean
    if not self.atom1.show and self.atom1.occupied_valency > 1:
      draw_start = 1
    draw_end = 1     # is added to index not boolean
    if not self.atom2.show and self.atom2.occupied_valency > 1:
      draw_end = 0

    # djust the step length
    step_size = 2*(self.line_width+1)
    ns = round( d / step_size) or 1
    step_size = d / ns

    # now we finally draw
    items = []
    for i in range( draw_start, int( round( d/ step_size)) +draw_end):
      if self.equithick: 
        coords = [x1 + i*step_size*dx + ddx, y1 + i*step_size*dy + ddy, x1 + i*step_size*dx - ddx, y1 + i*step_size*dy - ddy]
        if coords[0] == coords[2] and coords[1] == coords[3]: 
          if (dx1+dx2) > (dy1+dy2):  
            coords[0] += 1 
          else: 
            coords[1] += 1 
      else: # real wedge, not "equithick" 
        coords = [xa+dx1*i*step_size, ya+dy1*i*step_size, 2*x1-xa+dx2*i*step_size, 2*y1-ya+dy2*i*step_size] 
        if coords[0] == coords[2] and coords[1] == coords[3]:
          if (dx1+dx2) > (dy1+dy2): 
            coords[0] += 1
          else:
            coords[1] += 1
      items.append( self._create_line_with_transform( coords, width=self.line_width, fill=self.line_color))

    return items


  # dashed bond

  def _draw_d1( self):
    where = self._draw_n1()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where
    # main item
    self.paper.itemconfig( self.item, fill='')
    # the small lines
    self.items = self._draw_dash( (x1,y1,x2,y2))
    return x1,y1,x2,y2    

  def _draw_d2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      where = self._draw_n1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where

      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      if self.simple_double:
        where = self._draw_n1()
        if not where:
          # the bond is too short to draw it
          return None
        x1, y1, x2, y2 = where
      else:
        where = self._draw_d1()
        if not where:
          # the bond is too short to draw it
          return None
        x1, y1, x2, y2 = where
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # shortening of the second bond
    dx = x-x0
    dy = y-y0
    if self.center:
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
    self.second = self._draw_dash(( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy))
    if self.center:
      self.third = self._draw_dash(( 2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_d3( self):
    if self.simple_double:
      where = self._draw_n1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
    else:
      where = self._draw_d1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # we don't want to shorten the bonds (yet)
    _k = (1-self.double_length_ratio)/2
    _k = 0
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d*3/4)
    dx = x-x0
    dy = y-y0
    self.second = self._draw_dash(( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy))
    self.third = self._draw_dash(( 2*x1-x-_k*dx, 2*y1-y-_k*dy, 2*x2-x0+_k*dx, 2*y2-y0+_k*dy))


  def _draw_dash( self, coords):
    """returns list items"""
    x1, y1, x2, y2 = coords
    # main item
    dashing = (5, 5) # pixels full, pixels empty
    d = math.sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    # we adjust the dashing lengths
    _d = dashing[0]
    while not _d > d:
      _d += sum( dashing)
    dashing = list(map( lambda x: x * d/_d, dashing))
    # //
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 

    # now we finally draw
    items = []
    x = x1
    y = y1
    while min(x1,x2) <= x <= max(x1, x2) and min(y1,y2) <= y <= max(y1,y2):
      xn = x + dx*dashing[0]
      yn = y + dy*dashing[0]
      coords = (x, y, xn, yn)
      items.append( self._create_line_with_transform( coords, width=self.line_width, fill=self.line_color))
      x = xn + dx*dashing[1]
      y = yn + dy*dashing[1]
    return items


  def _draw_second_line( self, coords):
    my_x1, my_y1 = self.atom1.get_xy()
    my_x2, my_y2 = self.atom2.get_xy()
    my_coords = (my_x1,my_y1,my_x2,my_y2)
    x, y, x0, y0 = coords
    # shortening of the second bond
    dx = x-x0
    dy = y-y0
    if self.center:
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
    x, y, x0, y0 = x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy
    # shift according to the bonds arround
    side = geometry.on_which_side_is_point( my_coords, (x,y))
    for atom in (self.atom1,self.atom2):
      second_atom = atom is self.atom1 and self.atom2 or self.atom1
      neighs = [n for n in atom.neighbors if geometry.on_which_side_is_point( my_coords, n.get_xy())==side and n is not second_atom]
      for n in neighs:
        dist2 = _k*geometry.point_distance(*my_coords)*geometry.on_which_side_is_point((atom.x, atom.y, n.x, n.y), (second_atom.x, second_atom.y))
        xn1, yn1, xn2, yn2 = geometry.find_parallel( atom.x, atom.y, n.x, n.y, dist2)
        xp,yp,parallel,online = geometry.intersection_of_two_lines( x,y,x0,y0,xn1,yn1,xn2,yn2)
        if not parallel:
          if not geometry.is_point_beween_points_of_line( (x,y,x0,y0),(xp,yp)):
            # only shorten the line - do not elongate it
            continue
          if geometry.point_distance( atom.x,atom.y,x,y) < geometry.point_distance( atom.x,atom.y,x0,y0):
            x,y = xp, yp
          else:
            x0,y0 = xp, yp
        else:
          # parallel
          pass
    return [self._create_line_with_transform( (x, y, x0, y0), width=self.line_width, fill=self.line_color)]



  def _get_3dtransform_for_drawing( self):
    """this is a helper method that returns a transform3d which rotates
    self to coincide with the x-axis and rotates neighbors to be in (x,y)
    plane."""
    x1,y1,z1 = self.atom1.get_xyz()
    x2,y2,z2 = self.atom2.get_xyz()
    t = geometry.create_transformation_to_coincide_point_with_z_axis( [x1,y1,z1],[x2,y2,z2])
    x,y,z = t.transform_xyz( x2,y2,z2)
    # now rotate to make the plane of neighbor atoms coincide with x,y plane
    angs = []
    for n in self.atom1.neighbors + self.atom2.neighbors:
      if n is not self.atom1 and n is not self.atom2:
        nx,ny,nz = t.transform_xyz( *n.get_xyz())
        ang = math.atan2( ny, nx)
        if ang < -0.00001:
          ang += math.pi
        angs.append( ang)
    if angs:
      ang = sum( angs) / len( angs)
    else:
      ang = 0
    t.set_rotation_z( ang + math.pi/2.0)
    t.set_rotation_y( math.pi/2.0)
    return t

  # wedge bonds

  def _draw_w1( self):
    where = self._where_to_draw_from_and_to()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where

    self.item = self._draw_wedge( (x1,y1,x2,y2))[0]
    self.paper.addtag_withtag( "bond", self.item)
    # draw helper items
    self.second = self.third = []
    self.paper.register_id( self.item, self)
    return x1,y1,x2,y2

  def _draw_w2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      where = self._draw_n1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      where = self._draw_w1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_wedge
    self.second = _second_draw_method( (x,y,x0,y0))
    if self.center:
      self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_w3( self):
    where = self._draw_w1()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where

    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_wedge
    self.second = _second_draw_method( (x,y,x0,y0))
    self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))
    
    
  def _draw_wedge( self, coords):
    """returns the polygon item"""
    x1, y1, x2, y2 = coords
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.wedge_width/2.0)
    xa, ya, xb, yb = geometry.find_parallel( x1, y1, x2, y2, self.line_width/2.0) 
    return [self._create_polygon_with_transform( (xa, ya, x0, y0, 2*x2-x0, 2*y2-y0, 2*x1-xa, 2*y1-ya), width=0, fill=self.line_color, joinstyle="miter")] 


  def _draw_a1( self):
    where = self._where_to_draw_from_and_to()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where
    # main item
    self.item = self._draw_adder( (x1,y1,x2,y2))[0]
    self.paper.addtag_withtag( "bond", self.item)
    # draw helper items
    self.second = self.third = []
    self.paper.register_id( self.item, self)
    return x1,y1,x2,y2

  def _draw_a2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      where = self._draw_n1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      where = self._draw_a1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_adder
    self.second = _second_draw_method( (x,y,x0,y0))
    if self.center:
      self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))


  def _draw_a3( self):
    where = self._draw_a1()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where

    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_adder
    self.second = _second_draw_method( (x,y,x0,y0))
    self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))


  def _draw_adder( self, coords):
    """returns list items"""
    if not hasattr( self, 'equithick'): 
      self.equithick = 0                
    x1, y1, x2, y2 = coords
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.wedge_width/2.0)
    d = math.sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    if self.equithick:
      step_size = 1.8*self.line_width
    else:
      step_size = self.line_width+1

    dx1 = (x0 - x1)/d 
    dy1 = (y0 - y1)/d 
    dx2 = (2*x2 -x0 -x1)/d 
    dy2 = (2*y2 -y0 -y1)/d 
    # params for equithick	
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 
    ddx = x - x1 
    ddy = y - y1 

    coords2 = []
    coords2.extend((x1, y1))
    for i in range( 0, int( round( d/ step_size))+1):
      if self.equithick: 
        coords = [x1+dx*i*step_size+ddx, y1+dy*i*step_size+ddy, x1+dx*i*step_size-ddx, y1+dy*i*step_size-ddy] 
      else:
        coords = [x1+dx1*i*step_size, y1+dy1*i*step_size, x1+dx2*i*step_size, y1+dy2*i*step_size]
      if (coords[0] == coords[2] and coords[1] == coords[3]) and not self.equithick:
        if (dx1+dx2) > (dy1+dy2): 
          coords[0] += 1
        else:
          coords[1] += 1
      if i % 2:
        coords2.extend((coords[0], coords[1]))
      else:
        coords2.extend((coords[2], coords[3]))
    coords2.extend((x2, y2)) 
    if self.equithick:
      return [self._create_line_with_transform( coords2, width=self.line_width, fill=self.line_color, smooth=1)]
    else:
      return [self._create_line_with_transform( coords2, width=self.line_width, fill=self.line_color)]

  def _draw_b1( self):
    where = self._draw_n1()
    if not where:
      # the bond is too short to draw it
      return None
    self.paper.itemconfigure( self.item, width = self.wedge_width)

  def _draw_b2( self):
    self._draw_n2()
    if self.simple_double and not self.center:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third
    [self.paper.itemconfigure( item, width = self.wedge_width) for item in items]

  def _draw_b3( self):
    self._draw_n3()
    if self.simple_double:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third
    [self.paper.itemconfigure( item, width = self.wedge_width) for item in items]



  # dotted bonds

  def _draw_o1( self):
    where = self._draw_n1()
    if not where:
      # the bond is too short to draw it
      return None
    x1, y1, x2, y2 = where
    # main item
    self.paper.itemconfig( self.item, fill='')
    # the small lines
    self.items = self._draw_dotted( (x1,y1,x2,y2))
    return x1,y1,x2,y2    


  def _draw_o2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      where = self._draw_n1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where

      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      if self.simple_double:
        where = self._draw_n1()
        if not where:
          # the bond is too short to draw it
          return None
        x1, y1, x2, y2 = where
      else:
        where = self._draw_o1()
        if not where:
          # the bond is too short to draw it
          return None
        x1, y1, x2, y2 = where
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # shortening of the second bond
    dx = x-x0
    dy = y-y0
    if self.center:
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
    self.second = self._draw_dotted(( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy))
    if self.center:
      self.third = self._draw_dotted(( 2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))



  def _draw_o3( self):
    if self.simple_double:
      where = self._draw_n1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
    else:
      where = self._draw_o1()
      if not where:
        # the bond is too short to draw it
        return None
      x1, y1, x2, y2 = where
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # we don't want to shorten the bonds (yet)
    _k = (1-self.double_length_ratio)/2
    _k = 0
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d*3/4)
    dx = x-x0
    dy = y-y0
    self.second = self._draw_dotted(( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy))
    self.third = self._draw_dotted(( 2*x1-x-_k*dx, 2*y1-y-_k*dy, 2*x2-x0+_k*dx, 2*y2-y0+_k*dy))

    

  def _draw_dotted( self, coords):
    """returns list items"""
    x1, y1, x2, y2 = coords
    # main item
    diameter = self.line_width
    spacing = 2*self.line_width
    d = math.sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    # we adjust the spacing
    _d = spacing + diameter
    i = 1.0
    while not _d > d:
      _d += spacing + diameter
      i += 1.0
    spacing += (_d - d) / i
    # //
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 

    # now we finally draw
    items = []
    x = x1
    y = y1
    x += dx*( diameter + 0.5*spacing)
    y += dy*( diameter + 0.5*spacing)

    radius = 0.5*diameter
    while min(x1,x2) <= x <= max(x1, x2) and min(y1,y2) <= y <= max(y1,y2):
      coords = (x-radius, y-radius, x+radius, y+radius)
      items.append( self._create_oval_with_transform( coords, width=self.line_width, fill=self.line_color))
      x += dx*( diameter + spacing)
      y += dy*( diameter + spacing)
    return items




  ## // DRAW HELPER METHODS

  def redraw( self, recalc_side=0):
    if not self.__dirty:
      pass
      #print "redrawing non-dirty bond"
    sel = self.selector
    if self.item:
      self.delete()
    self.draw( automatic=recalc_side and "both" or "none")
    # reselect
    if sel:
      self.select()
    self.__dirty = 0




  def simple_redraw( self):
    """very fast redraw that draws only a simple line instead of the bond,
    used in 3d rotation only (as for BKChem 0.5.0)"""
    [self.paper.delete( i) for i in self.second]
    self.second = []
    [self.paper.delete( i) for i in self.third]
    self.third = []
    if self.items:
      map( self.paper.delete, self.items)
      self.items = []
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    x1, y1, x2, y2 = map( round, [x1, y1, x2, y2])
    if self.item and not self.paper.type( self.item) == "line":
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None
    if not self.item:
      # the bond might not be drawn because it was too short
      self.item = self.paper.create_line( (x1,y1,x2,y2))
      self.paper.register_id( self.item, self)
    else:
      self.paper.coords( self.item, x1, y1, x2, y2)
    self.paper.itemconfig( self.item, width = self.line_width, fill=self.line_color)
    




  def focus( self):
    # all the items of the bond
    if self.simple_double and not self.center:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third

    if self.type in 'na':
      [self.paper.itemconfig( item, width = self.line_width+2) for item in items]
    elif self.type == 'b':
      [self.paper.itemconfig( item, width = self.wedge_width+2) for item in items]
    elif self.type in 'ho':
      self.paper.itemconfig( self.item, fill="black")
    elif self.type == 'd':
      if self.simple_double and not self.center and not self.order == 1:
        [self.paper.itemconfig( item, width = self.line_width+2) for item in items]
      else:
        [self.paper.itemconfig( item, width = self.line_width + 2) for item in self.items+self.second+self.third]
    elif self.type == 'w':
      if self.center:
        items.remove( self.item)
      [self.paper.itemconfigure( item, fill='white', outline='black', width=1) for item in items]
      




  def unfocus( self):
    # all the items of the bond
    if self.simple_double and not self.center:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third

    if self.type in 'na':
      if not self.item:
        return
      [self.paper.itemconfig( item, width = self.line_width) for item in items]
    elif self.type == 'b':
      [self.paper.itemconfig( item, width = self.wedge_width) for item in items]
    elif self.type in 'ho':
      self.paper.itemconfig( self.item, fill = "")
    elif self.type == 'd':
      if self.simple_double and not self.center and not self.order == 1:
        [self.paper.itemconfig( item, width = self.line_width) for item in items]
      else:
        [self.paper.itemconfig( item, width = self.line_width) for item in self.items+self.second+self.third]
    elif self.type == 'w':
      if self.center:
        items.remove( self.item)
      [self.paper.itemconfigure( item, fill=self.line_color, width=0) for item in items]




  def select( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    x = ( x1 + x2) / 2
    y = ( y1 + y2) / 2
    if self.selector:
      self.paper.coords( self.selector, x-2, y-2, x+2, y+2)
    else:
      self.selector = self.paper.create_rectangle( x-2, y-2, x+2, y+2)
    self.paper.lower( self.selector)




  def unselect( self):
    self.paper.delete( self.selector)
    self.selector = None




  def move( self, dx, dy):
    """moves object with his selector (when present)"""
    items = list(filter( None, [self.item] + self.second + self.third + self.items))
    if self.selector:
      items.append( self.selector)
    [self.paper.move( o, dx, dy) for o in items]
      



  def delete( self):
    self.unselect()
    items = [self.item] + self.second + self.third + self.items
    if self.item:
      self.paper.unregister_id( self.item)
    self.item = None
    self.second = []
    self.third = []
    self.items = []
    map( self.paper.delete, items)
    return self





  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    b = ['no', 'yes']
    type = package.getAttribute( 'type')
    if type:
      self.type = type[0]
      self.order = int( type[1])
    else:
      self.type = 'n'
      self.order = 1
    self.id = package.getAttribute( 'id')
    # implied
    if package.getAttribute( 'bond_width'):
      self.bond_width = float( package.getAttribute( 'bond_width')) * self.paper.real_to_screen_ratio()
    #else:
    #  self.bond_width = None
    if package.getAttribute( 'line_width'):
      self.line_width = float( package.getAttribute( 'line_width'))
    if package.getAttribute( 'wedge_width'):
      self.wedge_width = float( package.getAttribute( 'wedge_width'))
    if package.getAttribute( 'center'):
      self.center = b.index( package.getAttribute( 'center'))
    else:
      self.center = None
    if package.getAttribute( 'color'):
      self.line_color = package.getAttribute( 'color')
    if package.getAttribute( 'double_ratio'):
      self.double_length_ratio = float( package.getAttribute( 'double_ratio'))
    if package.getAttribute( 'simple_double'):
      self.simple_double = int( package.getAttribute( 'simple_double'))
    if package.getAttribute( 'auto_sign'):
      self.auto_bond_sign = int( package.getAttribute( 'auto_sign'))
    if package.getAttribute( 'equithick'):
      self.equithick = int( package.getAttribute( 'equithick'))
    else:
      self.equithick = 0
    # end of implied
    self.atom1 = Store.id_manager.get_object_with_id( package.getAttribute( 'start'))
    self.atom2 = Store.id_manager.get_object_with_id( package.getAttribute( 'end'))




  def post_read_analysis( self):
    """this method is called by molecule after the *whole* molecule is
    read to perform a post-load analysis of double bond positioning"""
    # after read analysis
    if self.order == 2:
      sign, center = self._compute_sign_and_center()
      if self.bond_width and self.bond_width * sign < 0:
        self.auto_bond_sign = -1
      
  



  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    b = ['no', 'yes']
    bnd = doc.createElement('bond')
    dom_extensions.setAttributes( bnd, (('type', "%s%d" % (self.type, self.order)),
                                        ('line_width', str( self.line_width)),
                                        ('start', self.atom1.id),
                                        ('end', self.atom2.id),
                                        ('id', str( self.id)),
                                        ('double_ratio', str( self.double_length_ratio))))
    if hasattr( self, 'equithick') and self.equithick:
      bnd.setAttribute( 'equithick', str(1))
    if self.order != 1:
      bnd.setAttribute( 'bond_width', str( self.bond_width * self.paper.screen_to_real_ratio()))
      if self.order == 2:
        bnd.setAttribute( 'center', b[ int( self.center)])
        if self.auto_bond_sign != 1:
          bnd.setAttribute( 'auto_sign', str( self.auto_bond_sign))
    if self.type != 'n':
      bnd.setAttribute( 'wedge_width', str( self.wedge_width * self.paper.screen_to_real_ratio())) 
    if self.line_color != '#000':
      bnd.setAttribute( 'color', self.line_color)
    if self.type != 'n' and self.order != 1:
      bnd.setAttribute( 'simple_double', str( int( self.simple_double)))
    return bnd





  def toggle_type( self, only_shift = 0, to_type='n', to_order=1, simple_double=1):
    # just simply use the simple_double value
    self.simple_double = simple_double
    if not only_shift:
      if to_type != self.type:
        # if type was changed simply apply the change
        self.switch_to_type( to_type)
        self.switch_to_order( to_order)
      elif to_order == 1 and to_type in 'nd':
        # we want to treat order=1, type='n' as special in order to support the s=>d d=>t t=>s behaviour
        # but only in case the type is 'n'
        v1 = self.atom1.free_valency
        v2 = self.atom2.free_valency
        if not v1 or not v2:
          # it is not possible to increase the order
          self.switch_to_order( 1)
        else:
          self.switch_to_order( (self.order % 3) + 1)
      elif to_order != self.order:
        # if order was changed we do the same
        self.switch_to_order( to_order)
      else:
        # here comes the interesting stuff, type and order are the same
        if to_type in "ha":
          # the types for which side matters
          if self.equithick:
            self.equithick = 0
            self.atom1, self.atom2 = self.atom2, self.atom1
          else:
            self.equithick = 1

        if to_type in "w":
          self.atom1, self.atom2 = self.atom2, self.atom1
          # if the side is switched for double bond we need to change the sing of the bond_width
          if not self.center:
            self.bond_width = -self.bond_width
        elif to_order == 2:
          # we will shift the position of the second bond
          if self.center:
            self.bond_width = -self.bond_width
            self.auto_bond_sign = -self.auto_bond_sign
            self.center = 0
          elif self.bond_width > 0:
            self.bond_width = -self.bond_width
            self.auto_bond_sign = -self.auto_bond_sign
          else:
            self.center = 1
        else:
          # we do just nothing
          pass
    elif self.order == 2:
      # we will shift the position of the second bond
      if self.center:
        self.bond_width = -self.bond_width
        self.auto_bond_sign = -self.auto_bond_sign
        self.center = 0
      elif self.bond_width > 0:
        self.bond_width = -self.bond_width
        self.auto_bond_sign = -self.auto_bond_sign
      else:
        self.center = 1
    else:
      # we ignore it when shift only appears for non-double bonds
      pass
    self.redraw()





  def switch_to_type( self, type):
    if type in "wha" and self.type not in "wha":
      # get the standard width only if the changes is not within the "wha" group
      self.wedge_width = Screen.any_to_px( self.paper.standard.wedge_width)
    elif type not in "wha" and self.type in "wha":
      # when both are outside the 'wha' do the similar
      self.bond_width = Screen.any_to_px( self.paper.standard.bond_width)
    self.type = type





  def switch_to_order( self, order):
    self.order = order
    if self.order == 3:
      self.center = 0
    if self.order > 1:
      self._decide_distance_and_center()
    



  def _decide_distance_and_center( self):
    """according to molecular geometry decide what bond.center and bond.bond_width should be"""
    line = self.atom1.get_xy() + self.atom2.get_xy()
    if not self.bond_width:
      self.bond_width = self.standard.bond_width
      #length = sqrt((line[0]-line[2])**2  + (line[1]-line[3])**2)
      #self.bond_width = round( length / 5, 1)
    # does not need to go further if the bond is not double
    if self.order != 2:
      return 
    sign, center = self._compute_sign_and_center()
    self.bond_width = self.auto_bond_sign * sign * abs( self.bond_width)
    self.center = center



  def _compute_sign_and_center( self):
    """returns tuple of (sign, center) where sign is the default sign of the self.bond_width"""
    # check if we need to transform 3D before computation
    transform = None
    for n in self.atom1.neighbors + self.atom2.neighbors:
      # self.atom1 and self.atom2 are in this list as well
      if n.z != 0:
        # engage 3d transform prior to detection of where to draw
        transform = self._get_3dtransform_for_drawing()
        break
    if transform:
      for n in self.atom1.neighbors + self.atom2.neighbors:
        n.transform( transform)
    # /end of check
    line = self.atom1.get_xy() + self.atom2.get_xy()
    atms = self.atom1.get_neighbors() + self.atom2.get_neighbors()
    atms = misc.difference( atms, [self.atom1, self.atom2])
    coords = [a.get_xy() for a in atms]
    # searching for circles
    circles = 0
    for ring in self.molecule.get_smallest_independent_cycles_dangerous_and_cached():
      if self.atom1 in ring and self.atom2 in ring:
        on_which_side = lambda xy: geometry.on_which_side_is_point( line, xy)
        circles += reduce( operator.add, map( on_which_side, [a.get_xy() for a in ring if a not in self.atoms]))
    if circles:
      side = circles
    else:
      sides = [geometry.on_which_side_is_point( line, xy, threshold=0.1) for xy in coords]
      side = reduce( operator.add, sides, 0)
    # on which side to put the second line
    if side == 0 and (len( self.atom1.get_neighbors()) == 1 or
                      len( self.atom2.get_neighbors()) == 1):
      # maybe we should center, but this is usefull only when one of the atoms has no other substitution
      ret = (1 ,1)
    else:
      ret = None
      if not circles:
        # we center when both atoms have visible symbol and are not in circle
        if self.atom1.show and self.atom2.show:
          ret = (1, 1)
        # recompute side with weighting of atom types
        else:
          for i in range( len( sides)):
            if sides[i] and atms[i].__class__.__name__ == "atom":
              if atms[i].symbol == 'H':
                sides[i] *= 0.1 # this discriminates H
              elif atms[i].symbol != 'C':
                sides[i] *= 0.2 # this makes "non C" less then C but more then H
            side = reduce( operator.add, sides, 0)
      if not ret:
        if side < 0:
          ret = (-1, 0)
        else:
          ret = (1, 0)
    # transform back if necessary
    if transform:
      inv = transform.get_inverse()
      for n in self.atom1.neighbors + self.atom2.neighbors:
        n.transform( inv)
    # /end of back transform
    return ret
    




  def get_atoms( self):
    return self.get_vertices()




  def change_atoms( self, a1, a2):
    """used in overlap situations, it replaces reference to atom a1 with
    reference to atom a2"""
    if self.atom1 == a1:
      self.atom1 = a2
    elif self.atom2 == a1:
      self.atom2 = a2
    else:
      warn("not bonds' atom in bond.change_atoms(): "+str( a1), UserWarning, 2)



  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.paper.bbox( self.item)





  def delete( self):
    """deletes the bond from the paper"""
    if self.selector:
      self.unselect()
    # Delete all canvas items associated with this bond
    for item in self.items:
      if item:
        self.paper.delete( item)
    self.items = []
    for item in self.second:
      if item:
        self.paper.delete( item)
    self.second = []
    for item in self.third:
      if item:
        self.paper.delete( item)
    self.third = []
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None
    return self


  def lift( self):
    [self.paper.lift( i) for i in self.items]
    if self.selector:
      self.paper.lift( self.selector)
    if self.second:
      [self.paper.lift( o) for o in self.second]
    if self.third:
      [self.paper.lift( o) for o in self.third]
    if self.item:
      self.paper.lift( self.item)





  def transform( self, tr):
    if not self.item:
      return 
    for i in [self.item] + self.second + self.third + self.items:
      coords = self.paper.coords( i)
      tr_coords = tr.transform_xy_flat_list( coords)
      self.paper.coords( i, tuple( tr_coords))
    if self.selector:
      self.unselect()
      self.select()
    # we need to check if the sign of double bond width has not changed
    # this happens during 3d rotation
    if self.order == 2 and not self.center:
      line = list( self.atom1.get_xy())
      line += self.atom2.get_xy()
      x, y = self.paper.coords( self.second[0])[0:2]
      sign = geometry.on_which_side_is_point( line, (x,y))
      if sign * self.bond_width < 0:
        self.bond_width *= -1



  def get_exportable_items( self):
    """helper function for exporters,
    it returns a tuple in form of (line_items, items) where
    line_items are items that are exported as lines,
    items are items that are exported according to the bond type;
    as this code is a ugly mix of conditionals it makes sense to put it into one
    place co that the exporters do not have to reinvent it themself."""
    # items to be exported
    if self.type == 'd':
      # d is a little bit twisted
      if self.simple_double and not self.center and not self.order in (0,1):
        line_items = [self.item]
        items = self.second + self.third
      else:
        line_items = self.items
        items = self.second + self.third
    elif self.type == 'o':
      # o is a little bit twisted, too
      if self.simple_double and not self.center and not self.order in (0,1):
        line_items = [self.item]
        items = self.second + self.third
      else:
        line_items = []
        items = self.items + self.second + self.third
    else:
      if self.type == 'h':
        items = self.items
      else:
        if self.center:
          items = []
        else:
          items = [self.item]
      # simple doubles?
      if self.type == 'n' or (not self.simple_double and not self.center):
        items += self.second
        items += self.third
        line_items = []
      else:
        line_items = self.second + self.third
    return line_items, items


  def _create_line_with_transform( self, coords, **kw):
    """this is a private method intended to pass things to self.paper.create_line,
    but ensuring that a proper transformation takes place in case it is needed.
    It is used during drawing of bonds in 3D"""
    if self._transform:
      coords = self._transform.transform_xy_flat_list( coords)
    return self.paper.create_line( coords, **kw)

  def _create_oval_with_transform( self, coords, **kw):
    """this is a private method intended to pass things to self.paper.create_oval,
    but ensuring that a proper transformation takes place in case it is needed.
    It is used during drawing of bonds in 3D"""
    if self._transform:
      coords = self._transform.transform_xy_flat_list( coords)
    return self.paper.create_oval( coords, **kw)

  def _create_polygon_with_transform( self, coords, **kw):
    """this is a private method intended to pass things to self.paper.create_polygon,
    but ensuring that a proper transformation takes place in case it is needed.
    It is used during drawing of bonds in 3D"""
    if self._transform:
      coords = self._transform.transform_xy_flat_list( coords)
    return self.paper.create_polygon( coords, **kw)

