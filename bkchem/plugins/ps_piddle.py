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


from .piddle_lowlevel import piddle_exporter
from .tk2piddle import tk2piddle_ps
from piddle import piddlePS


class ps_exporter( piddle_exporter):
  """Exports Encapsulated PostScript files via the Piddle library. Usually gives better results
than the builtin method, but does not support unicode and the texts might be slightly misplaced.""" 

  doc_string = _("Exports Encapsulated PostScript files via the Piddle library. Usually gives better results than the builtin method, but does not support unicode and the texts might be slightly misplaced.")

  def __init__( self, paper):
    piddle_exporter.__init__( self, paper, converter_class=tk2piddle_ps)


  def init_canvas( self, pagesize=None):
    return piddlePS.PSCanvas( size=pagesize)



# PLUGIN INTERFACE SPECIFICATION
name = "PostScript (Piddle)"
extensions = [".eps",".ps"]
exporter = ps_exporter
local_name = _("PostScript (Piddle)")
