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


from . import config
import sys
import inspect


def log( *args, **kw):
  """it takes an optional keyword arguments 'output' (output file-like)
  and 'levels' (stack levels to report)"""
  if 'output' in kw:
    out = kw['output']
  else:
    out = None
  if 'levels' in kw:
    levels = kw['levels']
  else:
    levels = []
  if config.debug:
    frames = inspect.getouterframes( inspect.currentframe(), 1)
    try:
      for i in levels:
        if i < len( frames):
          frame = frames[i][0]
          print("  %s:%d -> %s()" % (frame.f_globals.get('__file__'), frame.f_lineno, frame.f_code.co_name))
    finally:
      del frames
      try:
        del frame
      except:
        pass
    for arg in args:
      print(arg, end=" ", file=out)
    print(file=out)


  
