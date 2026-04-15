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


__all__ = []
_names = ['CML','CML2','openoffice','ps_builtin','molfile','pdf_piddle','ps_piddle','pdf_cairo','png_cairo',"odf", "svg_cairo",'ps_cairo','CDXML','image_export']
# 'bitmap' and 'gtml' were removed for the release

import sys

for _name in _names:
  #import importlib; _mod = importlib.import_module('.' + _name, package=__name__); globals()[_name] = _mod
  try:
    import importlib; _mod = importlib.import_module('.' + _name, package=__name__); globals()[_name] = _mod
    __all__.append( _name)
  except Exception as e:
    # Suppress module loading warnings to reduce console noise
    pass

del _name
del _names
