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

"""the Splash class resides here"""

import tkinter
from . import messages
from . import os_support

class Splash( tkinter.Toplevel):

  def __init__( self):
    tkinter.Toplevel.__init__( self)

    self.title(_('BKChem is starting...'))

    # splash image
    splash_image_path = 'logo.ppm'
    try:
      self.splash_image = tkinter.PhotoImage( file = os_support.get_path( splash_image_path, 'image'))
    except:
      self.splash_image = None

    text = tkinter.Label( self,
                          font=('Helvetica', 12, 'normal'),
                          relief = 'raised',
                          borderwidth = 2,
                          padx=50, pady=50,
                          image = self.splash_image,
                          text = messages.splash_text
                          )
    text.pack(fill = 'both', expand = 1)

