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


"""images for buttons all over BKChem"""

from . import import_checker
from . import os_support
import tkinter


__all__ = ['images']


class images_dict( dict):
  """if asked about an pixmap it looks to the filesystem and
  adds the path into itself if found"""

  def __getitem__( self, item):
    # try if we need to recode the name
    try:
      item = name_recode_map[ item]
    except KeyError:
      pass
    try:
      return dict.__getitem__( self, item)
    except:
      try:
        i = tkinter.PhotoImage( file = os_support.get_path( item+'.gif', 'pixmap'))
        self.__setitem__( item, i)
        return i
      except ValueError:
        raise KeyError


  def __contains__( self, item):
    # try if we need to recode the name
    try:
      item = name_recode_map[ item]
    except KeyError:
      pass

    if dict.__contains__( self, item):
      return 1
    else:
      try:
        self.__setitem__( item, tkinter.PhotoImage( file = os_support.get_path( item+'.gif', 'pixmap')))
        return 1
      except:
        #print "pixmap not found: " + item
        return 0


# images for which the name and file name differs
name_recode_map = { #'vector': 'oval',
                    'fixed': 'fixed_length',
                    # Arrow type mappings to GIF files
                    'curved-electron': 'curved arrow_1',
                    'dashed': 'dashed arrow_1',
                    'fishhook': 'fishHook arrow_1',
                    'harpoon-left': 'harpoon arrow_1',
                    'resonance': 'resonance arrow_1',
                    'circular': 'round arrow_1'
                    }


images = images_dict()


