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


"""set of basic vector graphics classes such as rect, oval etc."""

from . import helper_graphics as hg
from . import dom_extensions
from . import misc
from . import classes
import operator
from .parents import meta_enabled, drawable, interactive, area_colored, container, with_line, top_level, line_colored

from .singleton_store import Screen
from functools import reduce


class vector_graphics_item( meta_enabled, drawable, interactive, with_line, top_level):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'vector'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color']
  # undo related metas
  meta__undo_properties = with_line.meta__undo_properties
  meta__undo_copy = ('coords',)


  
  def __init__( self, paper, coords=(), package=None, width=1):
    self.paper = paper
    meta_enabled.__init__( self, standard=paper.standard)
    self.selector = None
    self.item = None
    self.coords = []
    if coords:
      self.coords = coords
    if package:
      self.read_package( package)

  def read_standard_values( self, standard, old_standard=None):
    meta_enabled.read_standard_values( self, standard, old_standard=old_standard)
    if not old_standard or (self.paper.standard.line_width != old_standard.line_width):
      self.line_width = Screen.any_to_px( self.paper.standard.line_width)    

  def draw( self):
    pass

  def delete( self):
    self.paper.delete( self.item)
    self.paper.unregister_id( self.item) 
    self.item = None
    if self.selector:
      self.selector.delete()
      self.selector = None
    
  def focus( self):
    pass

  def unfocus( self):
    pass

  def select( self):
    self.selector = hg.selection_rect( self.paper, self, coords=tuple( self.coords), resize_event=self.resize, move_event=self.move)

  def unselect( self):
    if self.selector:
      self.selector.delete()
      self.selector = None
  
  def resize( self, coords, fix=()):
    self.coords = misc.normalize_coords( coords)
    self.paper.coords( self.item, self.coords)

  def move( self, dx, dy):
    self.paper.move( self.item, dx, dy)
    c = self.coords
    self.coords = ( c[0]+dx, c[1]+dy, c[2]+dx, c[3]+dy)
    if self.selector:
      self.selector.move( dx, dy)

  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pass
                           
  def read_package( self, pack):
    """reads the dom element pack and sets internal state according to it"""
    pass

  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.coords

  def lift( self):
    if self.item:
      self.paper.lift( self.item)
    if self.selector:
      self.selector.lift()


# RECTANGLE
class rect( vector_graphics_item, area_colored):

  object_type = 'rect'

  meta__undo_properties = vector_graphics_item.meta__undo_properties + \
                          area_colored.meta__undo_properties

  def __init__( self, paper, coords=(), package=None, width=1):
    vector_graphics_item.__init__( self, paper, coords=coords, package=package, width=width)

  def draw( self):
    self.item = self.paper.create_rectangle( tuple( self.coords),
                                             fill = self.area_color,
                                             outline = self.line_color,
                                             width = self.line_width,
                                             tags=("rect","vector"))
    self.paper.register_id( self.item, self)

  def redraw( self):
    if not self.item:
      self.draw()
    else:
      self.paper.coords( self.item, tuple( self.coords))
      self.paper.itemconfig( self.item, width=self.line_width, fill=self.area_color, outline=self.line_color)
    
  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pack = doc.createElement( 'rect')
    x1, y1, x2, y2 = Screen.px_to_text_with_unit( self.paper.screen_to_real_coords( self.coords))
    dom_extensions.setAttributes( pack, (('x1', x1),
                                         ('y1', y1),
                                         ('x2', x2),
                                         ('y2', y2),
                                         ('area_color', self.area_color),
                                         ('line_color', self.line_color),
                                         ('width', str( self.line_width))))
    return pack
                           
  def read_package( self, pack):
    """reads the dom element pack and sets internal state according to it"""
    self.coords = self.paper.real_to_screen_coords( map( Screen.any_to_px,
                                                         dom_extensions.getAttributes( pack, ['x1', 'y1', 'x2', 'y2'])))
    for attr in ("area_color", "line_color"):
      if pack.getAttributeNode( attr):
        setattr( self, attr, pack.getAttribute( attr))

    w = pack.getAttribute( 'width')
    if w:
      self.line_width = float( w)
    else:
      self.line_width = 1.0

# SQUARE
class square( rect):

  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pack = doc.createElement( 'square')
    x1, y1, x2, y2 = Screen.px_to_text_with_unit( self.paper.screen_to_real_coords( self.coords))
    dom_extensions.setAttributes( pack, (('x1', x1),
                                         ('y1', y1),
                                         ('x2', x2),
                                         ('y2', y2),
                                         ('area_color', self.area_color),
                                         ('line_color', self.line_color),
                                         ('width', str( self.line_width))))
    return pack
                           
  def select( self):
    self.selector = hg.selection_square( self.paper, self, coords=tuple( self.coords))

  def resize( self, coords, fix=()):
    if not fix:
      x1, y1, x2, y2 = misc.normalize_coords( coords)
      dx = x2 - x1
      dy = y2 - y1
      d = (abs( dx) + abs( dy))/2
      self.coords = (x1, y1, x1+d, y1+d)
    else:
      x1, y1, x2, y2 = coords
      dx = (fix[0] - x1) or (fix[0] - x2)
      dy = (fix[1] - y2) or (fix[1] - y1)
      d = (abs( dx) + abs( dy))/2
      self.coords = misc.normalize_coords( (fix[0], fix[1], x1-(d*misc.signum( dx) or d), y1-( d*misc.signum( dy) or d)))
    self.paper.coords( self.item, self.coords)


# OVAL
class oval( vector_graphics_item):

  object_type = 'oval'

  meta__undo_properties = vector_graphics_item.meta__undo_properties + \
                          area_colored.meta__undo_properties


  def __init__( self, paper, coords=(), package=None):
    vector_graphics_item.__init__( self, paper, coords=coords, package=package)

  def draw( self):
    self.item = self.paper.create_oval( tuple( self.coords),
                                        fill = self.area_color,
                                        outline = self.line_color,
                                        width = self.line_width,
                                        tags=("oval","vector"))
    self.paper.register_id( self.item, self)

  def redraw( self):
    if not self.item:
      self.draw()
    else:
      self.paper.coords( self.item, tuple( self.coords))
      self.paper.itemconfig( self.item, width=self.line_width, fill=self.area_color, outline=self.line_color)
      
  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pack = doc.createElement( 'oval')
    x1, y1, x2, y2 = Screen.px_to_text_with_unit( self.paper.screen_to_real_coords( self.coords))
    dom_extensions.setAttributes( pack, (('x1', x1),
                                         ('y1', y1),
                                         ('x2', x2),
                                         ('y2', y2),
                                         ('area_color', self.area_color),
                                         ('line_color', self.line_color),
                                         ('width', str( self.line_width))))
    return pack
                           
  def read_package( self, pack):
    """reads the dom element pack and sets internal state according to it"""
    self.coords = self.paper.real_to_screen_coords( map( Screen.any_to_px,
                                                         dom_extensions.getAttributes( pack, ['x1', 'y1', 'x2', 'y2'])))

    for attr in ("area_color", "line_color"):
      if pack.getAttributeNode( attr):
        setattr( self, attr, pack.getAttribute( attr))

    w = pack.getAttribute( 'width')
    if w:
      self.line_width = float( w)
    else:
      self.line_width = 1.0

  
# CIRCLE
class circle( oval):

  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pack = doc.createElement( 'circle')
    x1, y1, x2, y2 = Screen.px_to_text_with_unit( self.paper.screen_to_real_coords( self.coords))
    dom_extensions.setAttributes( pack, (('x1', x1),
                                         ('y1', y1),
                                         ('x2', x2),
                                         ('y2', y2),
                                         ('area_color', self.area_color),
                                         ('line_color', self.line_color),
                                         ('width', str( self.line_width))))
    return pack
                           
  def select( self):
    self.selector = hg.selection_square( self.paper, self, coords=tuple( self.coords), resize_event=self.resize, move_event=self.move)

  def resize( self, coords, fix=()):
    if not fix:
      x1, y1, x2, y2 = misc.normalize_coords( coords)
      dx = x2 - x1
      dy = y2 - y1
      d = (abs( dx) + abs( dy))/2
      self.coords = (x1, y1, x1+d, y1+d)
    else:
      x1, y1, x2, y2 = coords
      dx = (fix[0] - x1) or (fix[0] - x2)
      dy = (fix[1] - y2) or (fix[1] - y1)
      d = (abs( dx) + abs( dy))/2
      self.coords = misc.normalize_coords( (fix[0], fix[1], x1-(d*misc.signum( dx) or d), y1-( d*misc.signum( dy) or d)))
    self.paper.coords( self.item, self.coords)





# POLYGON
class polygon( vector_graphics_item, container, area_colored):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'polygon'
  # undo related metas
  meta__undo_properties = vector_graphics_item.meta__undo_properties + \
                          area_colored.meta__undo_properties

  meta__undo_copy = ('points',)
  meta__undo_children_to_record = ('points',)



  def __init__( self, paper, coords=(), package=None, width=1):
    area_colored.__init__( self)
    vector_graphics_item.__init__( self, paper, coords=coords, package=package, width=width)
    del self.coords # polygon does use points for storage of coord information
    if not package:
      self.points = []
      for i in range( 0, len( coords), 2):
        x = coords[i]
        y = coords[i+1]
        self.points.append( classes.point( self.paper, xy=( x, y), arrow=self))
    

  def draw( self):
    [p.draw() for p in self.points]
    coords = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
    self.item = self.paper.create_polygon( tuple( coords),
                                           fill=self.area_color,
                                           outline=self.line_color,
                                           width=self.line_width,
                                           tags=("polygon","vector"))
    self.paper.register_id( self.item, self)

  def move( self, dx, dy):
    [p.move( dx, dy) for p in self.points]
    self.paper.move( self.item, dx, dy)

  def redraw( self):
    if not self.item:
      self.draw()
    else:
      coords = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
      self.paper.coords( self.item, tuple( coords))
      self.paper.itemconfig( self.item, width=self.line_width, fill=self.area_color, outline=self.line_color)

  def select( self):
    #self.selector = hg.selection_square( self.paper, self, coords=tuple( self.bbox()))
    [o.select() for o in self.points]

  def unselect( self):
    [o.unselect() for o in self.points]

  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.paper.bbox( self.item)

  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pack = doc.createElement( 'polygon')
    dom_extensions.setAttributes( pack, (('area_color', self.area_color),
                                         ('line_color', self.line_color),
                                         ('width', str( self.line_width))))
    for p in self.points:
      pack.appendChild( p.get_package( doc))
    return pack

  def read_package( self, pack):
    """reads the dom element pack and sets internal state according to it"""
    self.points = []
    for p in pack.getElementsByTagName( 'point'):
      self.points.append( classes.point( self.paper, arrow=self, package=p))

    for attr in ("area_color", "line_color"):
      if pack.getAttributeNode( attr):
        setattr( self, attr, pack.getAttribute( attr))

    w = pack.getAttribute( 'width')
    if w:
      self.line_width = float( w)
    else:
      self.line_width = 1.0
      
  def lift( self):
    if self.selector:
      self.selector.lift()
    if self.item:
      self.paper.lift( self.item)
    [o.lift() for o in self.points]

  def delete_point( self, pnt):
    try:
      self.points.remove( pnt)
    except IndexError:
      warn( "trying to remove nonexisting point from polygon")
    pnt.delete()

  def is_empty_or_single_point( self):
    return len( self.points) < 3 

  def delete( self):
    [o.delete() for o in self.points]
    self.points = []
    self.paper.delete( self.item)
    self.paper.unregister_id( self.item)
    self.item = None



  # shape_defining_points
  def _get_shape_defining_points( self):
    return self.points

  shape_defining_points = property( _get_shape_defining_points, None, None,
                                    "should give list of point_drawable instances")






# Polyline
class polyline( vector_graphics_item, container, line_colored):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'polyline'
  # undo related metas
  meta__undo_properties = vector_graphics_item.meta__undo_properties + \
                          line_colored.meta__undo_properties + \
                          ('spline',)

  meta__undo_copy = ('points',)
  meta__undo_children_to_record = ('points',)



  def __init__( self, paper, coords=(), package=None, width=1, spline=False):
    self.spline = spline
    line_colored.__init__( self)
    vector_graphics_item.__init__( self, paper, coords=coords, package=package, width=width)
    del self.coords # polygon does use points for storage of coord information
    if not package:
      self.points = []
      for i in range( 0, len( coords), 2):
        x = coords[i]
        y = coords[i+1]
        self.points.append( classes.point( self.paper, xy=( x, y), arrow=self))
    


  def draw( self):
    [p.draw() for p in self.points]
    coords = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
    self.item = self.paper.create_line( tuple( coords),
                                        fill=self.line_color,
                                        width=self.line_width,
                                        tags=("polyline","vector"),
                                        smooth=self.spline)
    self.paper.register_id( self.item, self)


  def move( self, dx, dy):
    [p.move( dx, dy) for p in self.points]
    self.paper.move( self.item, dx, dy)


  def redraw( self):
    if not self.item:
      self.draw()
    else:
      coords = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
      self.paper.coords( self.item, tuple( coords))
      self.paper.itemconfig( self.item, width=self.line_width, fill=self.line_color, smooth=self.spline)


  def select( self):
    #self.selector = hg.selection_square( self.paper, self, coords=tuple( self.bbox()))
    [o.select() for o in self.points]


  def unselect( self):
    [o.unselect() for o in self.points]


  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.paper.bbox( self.item)


  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    pack = doc.createElement( 'polyline')
    dom_extensions.setAttributes( pack, (('line_color', self.line_color),
                                         ('width', str( self.line_width)),
                                         ('spline', str( int( self.spline))),
                                         ))
    for p in self.points:
      pack.appendChild( p.get_package( doc))
    return pack


  def read_package( self, pack):
    """reads the dom element pack and sets internal state according to it"""
    self.points = []
    for p in pack.getElementsByTagName( 'point'):
      self.points.append( classes.point( self.paper, arrow=self, package=p))

    for attr in ("line_color",):
      if pack.getAttributeNode( attr):
        setattr( self, attr, pack.getAttribute( attr))

    w = pack.getAttribute( 'width')
    if w:
      self.line_width = float( w)
    else:
      self.line_width = 1.0
    spline = pack.getAttribute( 'spline')
    if spline:
      self.spline = bool( int( spline))
    else:
      self.spline = False

      
  def lift( self):
    if self.selector:
      self.selector.lift()
    if self.item:
      self.paper.lift( self.item)
    [o.lift() for o in self.points]


  def delete_point( self, pnt):
    try:
      self.points.remove( pnt)
    except IndexError:
      warn( "trying to remove nonexisting point from polyline")
    pnt.delete()


  def is_empty_or_single_point( self):
    return len( self.points) < 2


  def delete( self):
    [o.delete() for o in self.points]
    self.points = []
    self.paper.delete( self.item)
    self.paper.unregister_id( self.item)
    self.item = None



  # shape_defining_points
  def _get_shape_defining_points( self):
    return self.points

  shape_defining_points = property( _get_shape_defining_points, None, None,
                                    "should give list of point_drawable instances")
