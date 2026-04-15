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


"""checks whether all important imports are available"""

__all__ = ['PIL_available','Pmw_available','PIL_state','PIL_prefix',
           'oasa_available','python_version_ok','python_version']


Pmw_available = 1
try:
  import Pmw
except ImportError:
  Pmw_available = 0

PIL_available = 1
PIL_state = 'normal'  # for buttons its callbacks rely on PIL
PIL_prefix = 0   # whether PIL has the PIL prefix
try:
  import Image, ImageDraw, ImageTk
except ImportError:
  try:
    import PIL.Image, PIL.ImageDraw, PIL.ImageTk
    PIL_prefix = 1
  except ImportError:
    PIL_available = 0
    PIL_state = 'disabled'


oasa_available = 1
try:
  from bkchem import oasa
except ImportError:
  oasa_available = 0


python_version_ok = 1
import sys
if not (sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] >= 5)):
  python_version_ok = 0

python_version = "%d.%d.%d" % sys.version_info[0:3]
