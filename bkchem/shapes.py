#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#     Copyright (C) 2002-2009 Beda Kosata <beda@zirael.org>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     Complete text of GNU GPL can be found in the file gpl.txt in the
#     main directory of the program
#
#--------------------------------------------------------------------------

"""shape classes - rectangle, ellipse, line

Based on ChemCanvas features - adds drawing shapes to BKChem.
"""

from .parents import drawable, interactive, top_level, line_colored
from .singleton_store import Screen
from . import dom_extensions
import xml.dom.minidom as dom


class Shape(drawable, line_colored, interactive, top_level):
  """Base class for shapes - rectangle, ellipse, line"""
  
  object_type = 'shape'
  meta__undo_properties = ('line_color', 'fill_color', 'line_width')
  meta__undo_copy = ('points',)
  
  def __init__(self, paper, points=None, package=None):
    drawable.__init__(self)
    line_colored.__init__(self)
    
    self.paper = paper
    self.points = points or []
    self.items = []
    self.line_width = 1.0
    self.fill_color = None
    
    if package:
      self.read_package(package)
  
  def set_colors(self, line_color=None, fill_color=None):
    """Set line and fill colors"""
    if line_color:
      self.line_color = line_color
    if fill_color is not None:
      self.fill_color = fill_color
  
  def draw(self):
    """Draw the shape - to be implemented by subclasses"""
    pass
  
  def redraw(self):
    """Redraw the shape"""
    if self.items:
      for item in self.items:
        self.paper.delete(item)
      self.items = []
    self.draw()
  
  def delete(self):
    """Delete the shape and all its canvas items"""
    for item in self.items:
      self.paper.delete(item)
    self.items = []
  
  def move(self, dx, dy):
    """Move the shape by dx, dy"""
    self.points = [(p[0] + dx, p[1] + dy) for p in self.points]
    self.redraw()
  
  def bbox(self):
    """Return bounding box [x1, y1, x2, y2]"""
    if not self.points:
      return [0, 0, 0, 0]
    xs = [p[0] for p in self.points]
    ys = [p[1] for p in self.points]
    return [min(xs), min(ys), max(xs), max(ys)]
  
  def focus(self):
    """Highlight when focused"""
    pass
  
  def unfocus(self):
    """Remove highlight"""
    pass
  
  def select(self):
    """Select the shape"""
    pass
  
  def unselect(self):
    """Unselect the shape"""
    pass
  
  def read_package(self, package):
    """Read shape from XML package"""
    if package.getAttribute('id'):
      self.id = package.getAttribute('id')
    self.line_width = float(package.getAttribute('width') or 1.0)
    self.line_color = package.getAttribute('color') or '#000000'
    self.fill_color = package.getAttribute('fill') or None
    for p in package.getElementsByTagName('point'):
      x = float(p.getAttribute('x'))
      y = float(p.getAttribute('y'))
      self.points.append((x, y))
  
  def get_package(self, doc):
    """Get XML package representing this shape"""
    shape = doc.createElement('shape')
    shape.setAttribute('id', getattr(self, 'id', ''))
    shape.setAttribute('type', self.object_type)
    dom_extensions.setAttributes(shape, (
      ('width', str(self.line_width)),
      ('color', str(self.line_color)),
      ('fill', str(self.fill_color) if self.fill_color else ''),
    ))
    for p in self.points:
      pt = doc.createElement('point')
      pt.setAttribute('x', str(p[0]))
      pt.setAttribute('y', str(p[1]))
      shape.appendChild(pt)
    return shape


class Rectangle(Shape):
  """Rectangle shape with optional fill"""
  
  object_type = 'rectangle'
  
  def draw(self):
    """Draw rectangle on canvas"""
    if len(self.points) < 2:
      return
    
    x1, y1 = self.points[0]
    x2, y2 = self.points[1]
    
    # Normalize (x1,y1 should be top-left, x2,y2 bottom-right)
    nx1, nx2 = min(x1, x2), max(x1, x2)
    ny1, ny2 = min(y1, y2), max(y1, y2)
    
    # Draw rectangle
    item = self.paper.create_rectangle(
      nx1, ny1, nx2, ny2,
      outline=self.line_color,
      fill=self.fill_color,
      width=self.line_width,
      tags='shape'
    )
    self.items = [item]
    self.paper.register_id(item, self)


class Ellipse(Shape):
  """Ellipse/circle shape with optional fill"""
  
  object_type = 'ellipse'
  
  def draw(self):
    """Draw ellipse on canvas"""
    if len(self.points) < 2:
      return
    
    x1, y1 = self.points[0]
    x2, y2 = self.points[1]
    
    # Normalize
    nx1, nx2 = min(x1, x2), max(x1, x2)
    ny1, ny2 = min(y1, y2), max(y1, y2)
    
    # Draw ellipse (oval)
    item = self.paper.create_oval(
      nx1, ny1, nx2, ny2,
      outline=self.line_color,
      fill=self.fill_color,
      width=self.line_width,
      tags='shape'
    )
    self.items = [item]
    self.paper.register_id(item, self)


class Line(Shape):
  """Simple line shape"""
  
  object_type = 'line'
  
  def draw(self):
    """Draw line on canvas"""
    if len(self.points) < 2:
      return
    
    x1, y1 = self.points[0]
    x2, y2 = self.points[1]
    
    # Draw line
    item = self.paper.create_line(
      x1, y1, x2, y2,
      fill=self.line_color,
      width=self.line_width,
      tags='shape'
    )
    self.items = [item]
    self.paper.register_id(item, self)


# Available shape types for UI
available_shapes = [
  ('rectangle', 'Rectangle'),
  ('ellipse', 'Ellipse'),
  ('line', 'Line'),
]
