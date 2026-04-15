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

"""PostScript Export plugin"""

from . import plugin

class PS_exporter( plugin.exporter):
  """Exports Encapsulated PostScript files. It uses a builtin (Tk) functions for PS export.
The results vary with the system, problems are usually font-related.""" 

  doc_string = _("Exports Encapsulated PostScript files. It uses builtin (Tk) functions for PS export. The results vary with the system, problems are usually font-related.")

  def __init__( self, paper):
    #plugin.exporter.__init__( self, paper)
    self.paper = paper

  def on_begin( self):
    return 1

  def write_to_file( self, name):
    self.paper.unselect_all()
    if self.paper.get_paper_property( 'crop_svg'):
      items = list( self.paper.find_all())
      items.remove( self.paper.background)
      x1, y1, x2, y2 = self.paper.list_bbox( items)
      margin = self.paper.get_paper_property( 'crop_margin')
      h = y2 -y1 +2*margin
      w = x2 -x1 +2*margin
      x = x1 - margin
      y = y1 - margin
      self.paper.postscript ( file=name, rotate=0, height=h, width=w, x=x, y=y)
    else:
      width = self.paper.get_paper_property( 'size_x')
      height = self.paper.get_paper_property( 'size_y')
      self.paper.postscript( file=name, rotate=0, height='%dm'%height, width='%dm'%width, x=0, y=0)



name = "PostScript (builtin)"
extensions = ['.eps','.ps']
exporter = PS_exporter
local_name = _("PostScript (builtin)")
