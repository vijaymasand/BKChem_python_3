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

"""The Store class which is a manager for application wide singletons resides here"""


import types
from . import misc




class Store:

  """Store class is used as a central point where all the application wide singleton
  objects are stored.
  Making them class attributes allows to loosen the coupling in the system by
  avoiding explicit linking of other objects to these singletons."""
  
  app = None          # the application
  tm = None           # the template manager
  utm = None          # uset templates manager
  gm = None           # the group manager
  pm = None           # the preferences manager
  logger = None       # the logger
  log = None          # the log method of the logger (usually)
  id_manager = None   # the id manager

  # attrs
  lang = "en"
  
  # recently unused
  clipboard = None    # the clipboard

  



class Screen:

  """Config stores values that are determined on startup"""

  dpi = 0  # this should be set on startup



  def cm_to_px( self, cm):
    """transforms coord from cm to px"""
    return self.dpi * cm / 2.54

  cm_to_px = classmethod( cm_to_px)



  def in_to_px( self, inch):
    """transforms coord from in to px"""
    return self.dpi * inch

  in_to_px = classmethod( in_to_px)




  def mm_to_px( self, mm):
    """transforms coord from mm to px"""
    return self.dpi * mm / 25.4

  mm_to_px = classmethod( mm_to_px)
  




  def read_xml_point( self, point):
    x = point.getAttribute( 'x')
    y = point.getAttribute( 'y')
    z = point.getAttribute( 'z')
    return map( self.any_to_px, (x,y,z))

  read_xml_point = classmethod( read_xml_point)

  
    

  def any_to_px( self, xyz):
    if type( xyz) == tuple or type( xyz) == list:
      return [self.any_to_px( i) for i in xyz]
    a, au = misc.split_number_and_unit( xyz)
    if au:
      if au == 'cm':
        a = self.cm_to_px( a)
      elif au == 'mm':
        a = self.mm_to_px( a)
      elif au == 'in':
        a = self.in_to_px( a)
      if au == 'px':
        return a
    return a

  any_to_px = classmethod( any_to_px)





  def px_to_cm( self, px):
    """transforms coord from px to cm"""
    return self.px_to_unit( px, unit='cm')

  px_to_cm = classmethod( px_to_cm)





  def px_to_unit( self, xyz, unit='cm', round_to=3):
    # handle sets of values
    if type( xyz) == tuple or type( xyz) == list:
      return [self.px_to_unit( i, unit=unit, round_to=round_to) for i in xyz]
    # handle empty queries
    if xyz == None:
      return None
    # different units
    if unit == 'cm':
      dots_per_unit = self.dpi / 2.54
    elif unit == 'mm':
      dots_per_unit = self.dpi / 25.4
    elif unit == 'in':
      dots_per_unit = self.dpi
    else:
      warn( "unknown unit passed to Screen.px_to_unit")
      return None
    # round or not round and return
    if round_to == None:
      return xyz/dots_per_unit
    else:
      return round( xyz/dots_per_unit, round_to)
  
  px_to_unit = classmethod( px_to_unit)

  


  def px_to_text_with_unit( self, xyz, unit='cm', round_to=3):
    # handle sets of values
    if type( xyz) == tuple or type( xyz) == list:    
      return [self.px_to_text_with_unit( i, unit=unit, round_to=round_to) for i in xyz]
    # round or not round and return
    if round_to == None:
      return '%f%s' % (self.px_to_unit( xyz, unit=unit, round_to=round_to), unit)
    else:
      return ('%.'+str( round_to)+'f%s') % (self.px_to_unit( xyz, unit=unit, round_to=round_to), unit)

  px_to_text_with_unit = classmethod( px_to_text_with_unit)
