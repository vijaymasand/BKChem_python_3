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


from .cairo_lowlevel import cairo_exporter
from .tk2cairo import tk2cairo
import cairo
import gettext
_ = gettext.gettext


class png_cairo_exporter( cairo_exporter):
  """Exports PNG files via the Cairo (pycairo) library. The output is usually quite good, with unicode
support and antialiased fonts. The output should look the same as the PDF (Cairo) export."""

  doc_string = _("Exports PNG files via the Cairo (pycairo) library. The output is usually quite good, with unicode support and antialiased fonts. The output should look the same as the PDF (Cairo) export.")

  def __init__( self, paper):
    cairo_exporter.__init__( self, paper, converter_class=tk2cairo)
    self.background_color = (1,1,1,1)


  def init_surface( self):
    w, h = map( int, map( round, self.pagesize))
    surface = cairo.ImageSurface( cairo.FORMAT_ARGB32, w, h)
    return surface


  def init_context( self):
    """to be overriden; should be called after init_surface"""
    context = cairo.Context( self.surface)
    context.set_source_rgba( *self.background_color)
    context.rectangle( 0, 0, self.pagesize[0], self.pagesize[1])
    context.fill()
    return context


  def get_scaling( self, x, y):
    if self.interactive:
      d = scale_dialog( self.paper, x, y)
      if d.result:
        self.background_color = d.background_color
        return d.result
      else:
        return None, None
    else:
      return 1.0, 1.0



  def save( self):
    self.surface.write_to_png(self.filename)
    self.surface.finish()



# PLUGIN INTERFACE SPECIFICATION
name = "PNG (Cairo)"
extensions = [".png"]
exporter = png_cairo_exporter
local_name = _("PNG (Cairo)")



import Pmw
import tkinter
from ..singleton_store import Screen


class scale_dialog:
  """dialog used to get ratio for scaling in percent"""
  def __init__( self, parent, x, y):
    self.orig_x = int( x)
    self.orig_y = int( y)
    

    self.dialog = Pmw.Dialog( parent,
                              buttons=(_('OK'), _('Cancel')),
                              defaultbutton=_('OK'),
                              title=_('PNG resolution and background color'),
                              command=self.done)

    tkinter.Label(self.dialog.interior(), text=_("Set the PNG picture resolution and background color using one of the criteria below.")).pack( pady=10, anchor="w", expand="1", padx=5)


    # X RATIO
    self.entryx = Pmw.Counter( self.dialog.interior(),
                               labelpos = 'w',
                               label_text=_("Scale X (in %):"),
                               entryfield_value = 100,
                               entryfield_validate={ 'validator':'real', 'min':0, 'max':10000},
                               entry_width = 5,
                               entryfield_modifiedcommand = self._scalex_changed,
                               increment = 10,
                               datatype = 'real')
    self.entryx.pack(pady=3, anchor='n', padx=10)
    # Y RATIO
    self.entryy = Pmw.Counter( self.dialog.interior(),
                               labelpos = 'w',
                               label_text=_("Scale Y (in %):"),
                               entryfield_value = 100,
                               entryfield_validate={ 'validator':'real', 'min':0, 'max':10000},
                               entry_width = 5,
                               entryfield_modifiedcommand = self._scaley_changed,
                               increment = 10,
                               datatype = 'real')
    self.entryy.pack(pady=3, anchor='n', padx=10)

    tkinter.Label(self.dialog.interior(), text=" ").pack( pady=1, anchor="w", expand="1")


    # X RES
    self.entry_resx = Pmw.Counter( self.dialog.interior(),
                               labelpos = 'w',
                               label_text=_("Size X (in px):"),
                               entryfield_value = self.orig_x,
                               entryfield_validate={ 'validator':'integer', 'min':0, 'max':100000},
                               entry_width = 5,
                               entryfield_modifiedcommand = self._resx_changed,
                               increment = 10,
                               datatype = 'integer')
    self.entry_resx.pack(pady=3, anchor='n', padx=10)
    # Y RES
    self.entry_resy = Pmw.Counter( self.dialog.interior(),
                               labelpos = 'w',
                               label_text=_("Size Y (in px):"),
                               entryfield_value = self.orig_y,
                               entryfield_validate={ 'validator':'integer', 'min':0, 'max':100000},
                               entry_width = 5,
                               entryfield_modifiedcommand = self._resy_changed,
                               increment = 10,
                               datatype = 'integer')
    self.entry_resy.pack(pady=3, anchor='n', padx=10)


    tkinter.Label(self.dialog.interior(), text=" ").pack( pady=1, anchor="w", expand="1")


    # DPI
    self.entry_dpi = Pmw.Counter( self.dialog.interior(),
                               labelpos = 'w',
                               label_text=_("Resolution (dpi):"),
                               entryfield_value = round( Screen.dpi),
                               entryfield_validate={ 'validator':'real', 'min':0, 'max':10000},
                               entry_width = 5,
                               entryfield_modifiedcommand = self._dpi_changed,
                               increment = 10,
                               datatype = 'real')
    self.entry_dpi.pack( pady=3, anchor='n', padx=10)


    tkinter.Label(self.dialog.interior(), text=" ").pack( pady=1, anchor="w", expand="1")

    self.background_color_button = Pmw.RadioSelect( self.dialog.interior(),
                                                    buttontype = 'radiobutton',
                                                    orient = 'vertical',
                                                    labelpos = "wn",
                                                    label_text=_("Background color"),
                                                    pady = 0)
    self.background_color_button.add( _("white"))
    self.background_color_button.add( _("transparent"))
    self.background_color_button.invoke( 0)
    self.background_color_button.pack(pady=3, anchor='n', padx=10)

    self.dialog.activate()



  def done( self, button):
    """called on dialog exit"""
    if not button or button == _('Cancel'):
      self.result = None
    else:
      self.result = (float( self.entryx.get())/100.0, float( self.entryy.get())/100.0)
    self.background_color = self.background_color_button.getvalue() == _("white") and (1,1,1,1) or (0,0,0,0)
    self.dialog.deactivate()


  def _set_value( self, entry, value):
    entry.component('entry').delete( 0, tkinter.END)
    entry.component('entry').insert( 0, value)



  def _set_values( self, rx, ry, x, y, dpi):
    if rx: self._set_value( self.entryx, rx)
    if ry: self._set_value( self.entryy, ry)
    if x: self._set_value( self.entry_resx, int( x))
    if y: self._set_value( self.entry_resy, int( y))
    if dpi: self._set_value( self.entry_dpi, round( dpi))


  def _scalex_changed( self):
    scale = float( self.entryx.get())
    res_x = self.orig_x * scale * 0.01
    res_y = self.orig_y * scale * 0.01
    dpi = Screen.dpi * scale * 0.01
    self._set_values( False, scale, res_x, res_y, dpi)


  def _scaley_changed( self):
    scale = float( self.entryy.get())
    res_x = self.orig_x * scale * 0.01
    res_y = self.orig_y * scale * 0.01
    dpi = Screen.dpi * scale * 0.01
    self._set_values( scale, False, res_x, res_y, dpi)


  def _resx_changed( self):
    res_x = int( self.entry_resx.get())
    scale = 100.0 * res_x / self.orig_x
    res_y = self.orig_y * scale * 0.01
    dpi = Screen.dpi * scale * 0.01
    self._set_values( scale, scale, False, res_y, dpi)


  def _resy_changed( self):
    res_y = int( self.entry_resy.get())
    scale = 100.0 * res_y / self.orig_y
    res_x = self.orig_x * scale * 0.01
    dpi = Screen.dpi * scale * 0.01
    self._set_values( scale, scale, res_x, False, dpi)



  def _dpi_changed( self):
    dpi = float( self.entry_dpi.get())
    scale = 100.0 * dpi / Screen.dpi
    res_x = self.orig_x * scale * 0.01
    res_y = self.orig_y * scale * 0.01
    self._set_values( scale, scale, res_x, res_y, False)

    

