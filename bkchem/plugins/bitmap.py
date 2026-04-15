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


from . import plugin
from piddle import piddlePIL
from .tk2piddle import tk2piddle


class bitmap_exporter( plugin.exporter):

  def __init__( self, paper):
    self.paper = paper


  def on_begin( self):
    dx = self.paper._paper_properties['size_x']
    dy = self.paper._paper_properties['size_y']
    self.canvas = piddlePIL.PILCanvas( size=(72*dx/25.4, 72*dy/25.4))
    self.converter = tk2piddle()
    return 1

  def write_to_file( self, name):
    self.converter.export_to_piddle_canvas( self.paper, self.canvas)
    self.canvas.save( name, "png")


# PLUGIN INTERFACE SPECIFICATION
name = "PNG"
extensions = [".png"]
exporter = bitmap_exporter
