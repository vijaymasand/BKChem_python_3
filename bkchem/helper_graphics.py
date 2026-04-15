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
#
#
#
#--------------------------------------------------------------------------

"""set of helper graphics items such as selection rects etc."""

from . import misc
import copy

class selection_rect:
  """used to draw rectangle around an object with hanldes on sides and in corners;
  provides user interaction for resizing, moving etc."""

  def __init__( self, paper, obj, resize_event=None, move_event=None, coords=()):
    self.object_type = 'selection_rect'
    self.paper = paper
    self.object = obj
    self._active_item = None
    self.color = 'grey'
    if coords:
      self.set_coords( coords)
      self.draw()
    if resize_event:
      self.resize_event = resize_event
    if move_event:
      self.move_event = move_event

  def set_coords( self, coords):
    self.coords = list( coords)

  def draw( self):
    if not self.coords:
      return
    x1, y1, x2, y2 = self.coords
    xm = round( (x1 + x2)/2.0)
    ym = round( (y1 + y2)/2.0)
    self._rect = self.paper.create_rectangle( self.coords, fill='', outline=self.color, tags=('helper_rect'))
    self._lt = self.paper.create_rectangle( (x1, y1, x1+2, y1+2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._mt = self.paper.create_rectangle( (xm-1, y1, xm+1, y1+2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._rt = self.paper.create_rectangle( (x2-2, y1, x2, y1+2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._lm = self.paper.create_rectangle( (x1, ym-1, x1+2, ym+1), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._rm = self.paper.create_rectangle( (x2-2, ym-1, x2, ym+1), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._lb = self.paper.create_rectangle( (x1, y2-2, x1+2, y2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._mb = self.paper.create_rectangle( (xm-1, y2-2, xm+1, y2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._rb = self.paper.create_rectangle( (x2-2, y2-2, x2, y2), outline=self.color, fill=self.color, tags=('helper_rect'))
    [self.paper.register_id( i, self) for i in self.get_items()]

  def redraw( self):
    if not self._rect:
      self.draw()
      return
    x1, y1, x2, y2 = self.coords
    xm = round( (x1 + x2)/2.0)
    ym = round( (y1 + y2)/2.0)
    self.paper.coords( self._rect, tuple( self.coords))
    self.paper.coords( self._lt, (x1, y1, x1+2, y1+2))
    self.paper.coords( self._mt, (xm-1, y1, xm+1, y1+2))
    self.paper.coords( self._rt, (x2-2, y1, x2, y1+2))
    self.paper.coords( self._lm, (x1, ym-1, x1+2, ym+1))
    self.paper.coords( self._rm, (x2-2, ym-1, x2, ym+1))
    self.paper.coords( self._lb, (x1, y2-2, x1+2, y2))
    self.paper.coords( self._mb, (xm-1, y2-2, xm+1, y2))
    self.paper.coords( self._rb, (x2-2, y2-2, x2, y2))

  def get_items( self):
    return (self._rect, self._lt, self._mt, self._rt, self._lm, self._rm, self._lb, self._mb, self._rb)

  def delete( self):
    [self.paper.delete( i) for i in self.get_items()]

  def move( self, dx, dy):
    [self.paper.move( i, dx, dy) for i in self.get_items()]
    self.coords[0] += dx
    self.coords[2] += dx
    self.coords[1] += dy
    self.coords[3] += dy

  def get_cursor( self, x, y):
    return "cross"
  
  def focus( self, item=None):
    if item:
      if item == self._rect:
        self._active_item = self._rect
      elif item == self._lt:
        self.paper['cursor'] = "top_left_corner"
        self._active_item = self._lt
      elif item == self._mt:
        self.paper['cursor'] = "top_side"
        self._active_item = self._mt
      elif item == self._rt:
        self.paper['cursor'] = "top_right_corner"
        self._active_item = self._rt
      elif item == self._lm:
        self.paper['cursor'] = "left_side"
        self._active_item = self._lm
      elif item == self._rm:
        self.paper['cursor'] = "right_side"
        self._active_item = self._rm
      elif item == self._lb:
        self.paper['cursor'] = "bottom_left_corner"
        self._active_item = self._lb
      elif item == self._mb:
        self.paper['cursor'] = "bottom_side"
        self._active_item = self._mb
      elif item == self._rb:
        self.paper['cursor'] = "bottom_right_corner"
        self._active_item = self._rb

  def unfocus( self):
    self.paper['cursor'] = ''
    self._active_item = None

  def drag( self, x, y, fix=()):
    if self._active_item == self._rect and fix:
      # we drag the whole rectangle
      x2, y2 = fix
      dx = x - x2
      dy = y - y2
      if self.object:
        self.object.move( dx, dy)
      else:
        self.move( dx, dy)
      return True
    else:
      if self._active_item in (self._lt, self._lm, self._lb):
        self.coords[0] = x
      elif self._active_item in (self._rt, self._rm, self._rb):
        self.coords[2] = x
      if self._active_item in (self._lt, self._mt, self._rt):
        self.coords[1] = y
      elif self._active_item in (self._lb, self._mb, self._rb):
        self.coords[3] = y

      self.redraw()
      if self.object:
        self.object.resize( self.coords)
      return False

  def lift( self):
    [self.paper.lift( i) for i in self.get_items()]

  

class selection_square( selection_rect):
  """used to draw square around an object with hanldes in corners;
  provides user interaction for resizing, moving etc."""

  def draw( self):
    if not self.coords:
      return
    x1, y1, x2, y2 = self.coords
    xm = round( (x1 + x2)/2.0)
    ym = round( (y1 + y2)/2.0)
    self._rect = self.paper.create_rectangle( self.coords, fill='', outline=self.color, tags=('helper_rect'))
    self._lt = self.paper.create_rectangle( (x1, y1, x1+2, y1+2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._rt = self.paper.create_rectangle( (x2-2, y1, x2, y1+2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._lb = self.paper.create_rectangle( (x1, y2-2, x1+2, y2), outline=self.color, fill=self.color, tags=('helper_rect'))
    self._rb = self.paper.create_rectangle( (x2-2, y2-2, x2, y2), outline=self.color, fill=self.color, tags=('helper_rect'))
    [self.paper.register_id( i, self) for i in self.get_items()]
    
  def redraw( self):
    if not self._rect:
      self.draw()
      return
    x1, y1, x2, y2 = self.coords
    xm = round( (x1 + x2)/2.0)
    ym = round( (y1 + y2)/2.0)
    self.paper.coords( self._rect, tuple( self.coords))
    self.paper.coords( self._lt, (x1, y1, x1+2, y1+2))
    self.paper.coords( self._rt, (x2-2, y1, x2, y1+2))
    self.paper.coords( self._lb, (x1, y2-2, x1+2, y2))
    self.paper.coords( self._rb, (x2-2, y2-2, x2, y2))

  def get_items( self):
    return (self._rect, self._lt, self._rt, self._lb, self._rb)

  def focus( self, item=None):
    if item:
      if item == self._rect:
        self._active_item = self._rect
      elif item == self._lt:
        self.paper['cursor'] = "top_left_corner"
        self._active_item = self._lt
      elif item == self._rt:
        self.paper['cursor'] = "top_right_corner"
        self._active_item = self._rt
      elif item == self._lb:
        self.paper['cursor'] = "bottom_left_corner"
        self._active_item = self._lb
      elif item == self._rb:
        self.paper['cursor'] = "bottom_right_corner"
        self._active_item = self._rb

  def drag( self, x, y, fix=()):
    x1, y1, x2, y2 = fix + (x, y)
    if self.object:
      self.object.resize( (x1, y1, x2, y2), fix=fix)
      self.coords = list( self.object.coords)
    self.redraw()

  def get_fix( self):
    """returns the coords that should be fixed if we now start to drag the selected corner"""
    fix = [0,0]
    self.coords = misc.normalize_coords( self.coords)
    if self._active_item in (self._lt, self._lb):
      fix[0] = self.coords[2]
    else:
      fix[0] = self.coords[0]
    if self._active_item in (self._lt, self._rt):
      fix[1] = self.coords[3]
    else:
      fix[1] = self.coords[1]
    return fix
