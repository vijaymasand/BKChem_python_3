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

"""provides export plugin to povray"""

from . import plugin
import operator
from io import StringIO

class POV_exporter( plugin.exporter):
  """export to POVRAY formate"""
  def __init__( self, paper):
    self.paper = paper

  def on_begin( self):
    import tkinter.messagebox as tkMessageBox
    yes = tkMessageBox.askyesno( _("Really export?"),
                                 _('This plugin is not finished and will probably not work correctly.') + ' ' +
                                 _('Proceed?'))
    return yes

  def fill_header( self):
    self.doc = StringIO()
    self.doc.write(  '''#include "colors.inc"\n#include "textures.inc"\n#include "shapes.inc"\n''')
    self.doc.write( '''global_settings { ambient_light rgb<1, 1, 1> }\n''')
    self.doc.write( '''#declare bond =  texture { 
                pigment { color Red }
                finish { phong 1
                         reflection .7
                         metallic
                         ambient .4
                         diffuse .3 }}\n''')
    self.doc.write( ''' light_source {
    <-20, 500, -800>
    color White
    area_light <100, 0, 0>, <0, 100, 0>, 10, 10
    adaptive 1
    jitter }\n''')
    self.doc.write( '''polygon { 4,
	<0,0,15>, <0,480,15>, <640,480,15>, <640,0,15>
	texture { pigment { color White
			    transmit 0 }
		  finish { phong .1
			   reflection .03
			   metallic
			   ambient .5
			   diffuse .5
			  roughness 0.001 } }
		}\n''')
    self.doc.write( '''camera {
    location <550, 200, -450>
    look_at <380,240,0>
    }\n''')
    return 1

  def fill_image( self):
    for item in self.paper.find_all():
      if self.paper.type( item) == "line":
        a = map( int, self.paper.coords( item))
        t = float( self.paper.itemcget( item, 'width'))
        if not (a[0]==a[2] and a[1]==a[3]): 
          self.doc.write( '''cylinder {<%d, %d, 0>, <%d, %d, 0>, %1.1f\n texture { bond }}\n''' % ( a[0], 480-a[1], a[2], 480-a[3], t))
      elif self.paper.type( item) == "text":
        a = self.paper.bbox( item)
        x, y = a[0], 480-a[1]
        text = self.paper.itemcget( item, 'text')
        font = self.paper.itemcget( item, 'font')
        size = round( int( font.split()[1]) / 0.75)
        y -= size * 0.75
        self.doc.write( '''text { ttf "timrom.ttf" "%s" %1.3f, 0\n texture { bond }\n scale %d\n translate <%d, %d, 0>}\n''' % (text, 1.0/size, size, x, y))
    
  def write_to_file( self, name):
    self.fill_header()
    self.fill_image()
    f = open( name, 'w')
    f.write( self.doc.getvalue())
    f.close()
    self.doc.close()
    
## HEADER

name = "Povray"
extensions = ['.pov']
exporter = POV_exporter
