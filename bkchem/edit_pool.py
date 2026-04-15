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


"""the 'edit pool' widget resides here"""

from tkinter import Frame, Button, Entry
import tkinter
from . import config
import re, string
from .groups_table import groups_table
from . import misc
from .keysymdef import keysyms
import os
from xml.sax import saxutils

from .singleton_store import Store

# Internationalization
try:
    _
except NameError:
    _ = lambda x: x


class editPool( Frame):

  font_decorations = ('italic', 'bold', 'subscript', 'superscript')
  font_decorations_to_names = {'italic':_('italic'), 'bold':_('bold'), 'subscript':_('subscript'), 'superscript':_('superscript')}
  font_decorations_to_html = {'italic':'i', 'bold':'b', 'subscript':'sub', 'superscript':'sup'}


  def __init__( self, master, buttons=('interpret','asis'), **kw):
    Frame.__init__( self, master, **kw)
    self.text = ''
    self.interpret = 1
    self.editPool = Entry( self, width=50, state='disabled', font="Helvetica 12")
    self.editPool.pack( side='left')

    self.editPool.bind( '<Return>', self._interpretButtonPressed)
    self.editPool.bind( '<Escape>', self._cancel)

    self.editPool.bind( '<Control-s>', lambda e: self._tag_it( "sub"))
    self.editPool.bind( '<Control-S>', lambda e: self._tag_it( "sup"))
    self.editPool.bind( '<Control-i>', lambda e: self._tag_it( "i"))
    self.editPool.bind( '<Control-b>', lambda e: self._tag_it( "b"))

    self.editPool.bind("<KeyPress>", self._key)


    if 'interpret' in buttons:
      pix = Store.app.request( 'pixmap', name='interpret')
      self.interpretButton = Button( self,
                                     text=_('Interpret'),
                                     image=pix,
                                     command=self._interpretButtonPressed,
                                     state='disabled',
                                     bd=config.border_width)
      Store.app.balloon.bind( self.interpretButton, _('Interpret text (where applicable)'))
      self.interpretButton.pack( side='left')
    else:
      self.interpretButton = None

    if 'asis' in buttons:
      pix = Store.app.request( 'pixmap', name='asis')      
      self.setButton = Button( self,
                               image=pix,
                               text=_('As is'),
                               command=self._setButtonPressed,
                               state='disabled',
                               bd=config.border_width)
      Store.app.balloon.bind( self.setButton, _('Leave text as is - do not interpret'))
      self.setButton.pack( side='left')
    else:
      self.setButton = None


    pix = Store.app.request( 'pixmap', name='subnum')
    self.numbersToSubButton = Button( self,
                                      image=pix,
                                      text=_('Sub numbers'),
                                      command=self._numbersToSubButtonPressed,
                                      state='disabled',
                                      bd=config.border_width)
    Store.app.balloon.bind( self.numbersToSubButton, _('Convert numbers to subscript'))
    self.numbersToSubButton.pack( side='left')

    self.formulaButton = Button( self,
                                 text=_('Formula'),
                                 command=self._formulaButtonPressed,
                                 state='disabled',
                                 bd=config.border_width)
    Store.app.balloon.bind( self.formulaButton, _('Auto-format chemical formula'))
    self.formulaButton.pack( side='left')

    # text decoration
    decorFrame = Frame( self)
    decorFrame.pack( padx=5, side="left")
    for i in self.font_decorations:
      pix = Store.app.request( 'pixmap', name=i)
      self.__dict__[ i] = Button( self,
                                  image=pix,
                                  command=misc.lazy_apply( self._tag_it, (self.font_decorations_to_html[i],)),
                                  state='disabled',
                                  text=self.font_decorations_to_names[i],
                                  bd=config.border_width)
      Store.app.balloon.bind( self.__dict__[i], self.font_decorations_to_names[i])
      self.__dict__[ i].pack( side="left")

    # special characters
    pix = Store.app.request( 'pixmap', name='specialchar')
    self.specialCharButton = Button( self,
                                      image=pix,
                                      text=_('Special Character'),
                                      command=self._specialCharButtonPressed,
                                      state='disabled',
                                      bd=config.border_width)
    Store.app.balloon.bind( self.specialCharButton, _('Insert a special character'))
    self.specialCharButton.pack( side='left')
    self.active = False

      

  def _interpretButtonPressed( self, *e):
    t = self.editPool.get()
    if t.lower() in groups_table:
      self._setText( t)
      #self._setText( groups_table[t.lower()]['text'])
      #self.editPool.insert(0, self.text)
    else:
      self._setText( t)
      self.text = re.sub( "\\\\n", "\n", self.text)
    self._quit()

  def _setButtonPressed( self, *e):
    self._setText( self.editPool.get())
    self.interpret = 0
    self._quit()

  def _numbersToSubButtonPressed( self, *e):
    self._setText( re.sub( "\d+", '<sub>\g<0></sub>', self.editPool.get()))
    self._quit()

  def _formulaButtonPressed( self, *e):
    # Standard chemical formula logic: subscript digits following letters or closing brackets
    text = self.editPool.get()
    formatted = re.sub( r'(?<=[A-Za-z\]\)])(\d+)', r'<sub>\1</sub>', text)
    self._setText( formatted )
    self._quit()


  def _cancel( self, e):
    self._setText( None)
    self.active = False
    self._quit()

  def _quit( self):
    self.grab_release()
    self._disable()
    self._normaly_terminated = 1
    self.active = False
    self.quit()


  def _disable( self):
    if self.interpretButton: self.interpretButton.configure( state='disabled')
    self.numbersToSubButton.configure( state='disabled')
    self.formulaButton.configure( state='disabled')
    if self.setButton: self.setButton.configure( state='disabled')
    self.editPool.configure( state='disabled')
    self.italic.configure( state='disabled')
    self.bold.configure( state='disabled')
    self.superscript.configure( state='disabled')
    self.subscript.configure( state='disabled')
    self.specialCharButton.configure( state='disabled')
    
  def _enable( self):
    if self.interpretButton: self.interpretButton.configure( state='normal')
    self.numbersToSubButton.configure( state='normal')
    self.formulaButton.configure( state='normal')
    if self.setButton: self.setButton.configure( state='normal')
    self.editPool.configure( state='normal')
    self.italic.configure( state='normal')
    self.bold.configure( state='normal')
    self.superscript.configure( state='normal')
    self.subscript.configure( state='normal')
    self.specialCharButton.configure( state='normal')

  def _setText( self, text):
    self.text = text
    self._update()

  def _update( self):
    self.editPool.delete(0, last='end')
    if self.text:
      self.editPool.insert(0, self.text)

  def activate( self, text=None, select=1):
    """activates edit_pool and returns inserted value (None if cancel occured),
    if parameter text is None it preserves the old one, use text='' to delete old text"""
    self.active = True
    self.interpret = 1
    self.focus_set()
    self.grab_set()
    self._enable()
    # this is because I need to distinguish whether the mainloop was terminated "from inside"
    # or from outside (this most of the time means the application was killed and the widgets are no longer available)
    self._normaly_terminated = 0
    if text != None:
      self._setText( text)
    self.editPool.focus_set()
    if select:
      self.editPool.selection_range( 0, 'end')
    self.mainloop()
    if self._normaly_terminated:
      return self.text
    else:
      return None

  def _tag_it( self, tag):
    if self.editPool.selection_present():
      self.editPool.insert( tkinter.SEL_FIRST, '<%s>' % tag)
      self.editPool.insert( tkinter.SEL_LAST, '</%s>' % tag)
    else:
      self.editPool.insert( tkinter.INSERT, '<%s></%s>' % (tag, tag))
      self.editPool.icursor( self.editPool.index( tkinter.INSERT) - len( tag) - 3)
      

  def _key( self, event):
    if len(event.keysym) > 1 and event.keysym in keysyms:
      if self.editPool.selection_present():
        self.editPool.delete( "anchor", "insert")
      self.editPool.insert( 'insert', keysyms[ event.keysym])
      return "break"


  def _specialCharButtonPressed( self):
    dialog = special_character_menu( self._insertText)
    dialog.post( self.specialCharButton.winfo_rootx(), self.specialCharButton.winfo_rooty())


  def _insertText( self, text):
    if text != None:
      self.editPool.insert( tkinter.INSERT, text)
    self.grab_set()




class special_character_menu( tkinter.Menu):

  chars = {_("minus"): "&#8722;",
           _("arrow-left"): "&#x2190;",
           _("arrow-right"): "&#x2192;",
           _("arrow-up"): "&#x2191;",
           _("arrow-down"): "&#x2193;",
           _("new line"): "\\n",
           _("degree"): "&#x00B0;",
           _("angstrom"): "&#x00C5;",
           _("Delta"): "&#x0394;",
           _("Phi"): "&#x03A6;",
           _("alpha"): "&#x03B1;",
           _("beta"): "&#x03B2;",
           _("gamma"): "&#x03B3;",
           _("delta"): "&#x03B4;",
           _("epsilon"): "&#x03B5;",
           _("zeta"): "&#x03B6;",
           _("eta"): "&#x03B7;",
           _("theta"): "&#x03B8;",
           _("iota"): "&#x03B9;",
           _("kappa"): "&#x03BA;",
           _("lambda"): "&#x03BB;",
           _("mu"): "&#x03BC;",
           _("nu"): "&#x03BD;",
           _("xi"): "&#x03BE;",
           _("pi"): "&#x03C0;",
           _("rho"): "&#x03C1;",
           _("sigma"): "&#x03C3;",
           _("tau"): "&#x03C4;",
           _("upsilon"): "&#x03C5;",
           _("phi"): "&#x03C6;",
           _("chi"): "&#x03C7;",
           _("psi"): "&#x03C8;",
           _("omega"): "&#x03C9;",}

  def __init__( self, callback, **kw):
    self.callback = callback
    tkinter.Menu.__init__( self, Store.app, tearoff=0, **kw)
    keys = list(self.chars.keys())
    keys.sort()
    for k in keys:
      self.add_command( label=k, command=misc.lazy_apply( self.itemselected, (k,)))
    self.char = None


  def itemselected( self, k):
    self.callback( saxutils.unescape( self.chars[k]))


  def post( self, x, y):
    tkinter.Menu.post( self, x, y)
    if os.name != 'nt':
      self.grab_set()
