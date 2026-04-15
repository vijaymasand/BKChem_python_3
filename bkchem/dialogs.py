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

"""set of dialogs used by BKChem"""

import tkinter
import tkinter.font as tkFont
import tkinter.messagebox as tkMessageBox
import Pmw
from . import misc
from . import data
import re
from . import widgets
from . import classes
import os
from . import os_support
from .singleton_store import Store, Screen


## SCALE DIALOG

class scale_dialog:
  """dialog used to get ratio for scaling in percent"""
  def __init__( self, parent):
    self.dialog = Pmw.Dialog( parent,
                              buttons=(_('OK'), _('Cancel')),
                              defaultbutton=_('OK'),
                              title=_('Scale'),
                              command=self.done)
    # X RATIO
    self.entryx = Pmw.Counter( self.dialog.interior(),
                               labelpos = 'w',
                               label_text=_("Scale X (in %):"),
                               entryfield_value = 100,
                               entryfield_validate={ 'validator':'integer', 'min':0, 'max':100000},
                               entry_width = 5,
                               entryfield_modifiedcommand = self._scalex_changed,
                               increment = 10,
                               datatype = 'integer')
    self.entryx.pack(pady=10, anchor='w', padx=10)
    # Y RATIO
    self.entryy = Pmw.Counter( self.dialog.interior(),
                               labelpos = 'w',
                               label_text=_("Scale Y (in %):"),
                               entryfield_value = 100,
                               entryfield_validate={ 'validator':'integer', 'min':0, 'max':100000},
                               entry_width = 5,
                               entryfield_modifiedcommand = self._scaley_changed,
                               increment = 10,
                               datatype = 'integer')
    self.entryy.pack(pady=10, anchor='w', padx=10)

    self.preserve_ratio = tkinter.IntVar()
    self.preserve_ratio_entry = tkinter.Checkbutton( self.dialog.interior(),
                                                     text=_('Preserve aspect ratio?'),
                                                     variable = self.preserve_ratio,
                                                     command = self._preserve_ratio_changed)
    self.preserve_ratio_entry.pack( anchor="w")
    self.preserve_ratio.set( 1)

    self.preserve_centers = tkinter.IntVar()
    self.preserve_centers_entry = tkinter.Checkbutton( self.dialog.interior(),
                                                       text=_('Fix position of centers of objects?'),
                                                       variable = self.preserve_centers)
    self.preserve_centers_entry.pack( anchor="w")

    self.scale_fonts = tkinter.IntVar()
    self.scale_fonts_entry = tkinter.Checkbutton( self.dialog.interior(),
                                                       text=_('Scale font and mark sizes?'),
                                                       variable = self.scale_fonts)
    self.scale_fonts_entry.pack( anchor="w")
    self.scale_fonts.set( 1)
    

    self.dialog.activate()


  def done( self, button):
    """called on dialog exit"""
    if not button or button == _('Cancel'):
      self.result = None
    elif not (self.entryx.valid() and self.entryy.valid()) :
      self.result = ()
    else:
      self.result = (float( self.entryx.get()), float( self.entryy.get())) #, self.preserve_center.get())
      if self.preserve_ratio.get():
        # x is significant if ratio should be preserved
        self.result = (self.result[0], self.result[0])
    self.dialog.deactivate()

  def _scalex_changed( self):
    if self.preserve_ratio.get():
      if self.entryy.get() != self.entryx.get():
        self.entryy.setentry( self.entryx.get())

  def _scaley_changed( self):
    if self.preserve_ratio.get():
      if self.entryy.get() != self.entryx.get():
        self.entryx.setentry( self.entryy.get())

  def _preserve_ratio_changed( self):
    if self.preserve_ratio.get():
      if self.entryy.get() != self.entryx.get():
        if self.entryx.get() == '100':
          self.entryx.setentry( self.entryy.get())
        else:
          self.entryy.setentry( self.entryx.get())
    




## CONFIG DIALOG

class config_dialog:
  """items configuration"""
  def __init__( self, parent, items):
    self.items = items
    self.changes_made = 0
    self.parent = parent
    self.dialog = Pmw.Dialog( parent,
                              buttons=(_('OK'), _('Cancel')),
                              defaultbutton=_('OK'),
                              title=_('Configuration'),
                              command=self.done,
                              master='parent')
    #parent.bind_all( "<Button-1>", self.raise_me, add='+')
    self.pages = Pmw.NoteBook( self.dialog.interior())
    self.pages.pack( anchor='w', pady=0, padx=0, fill='both', expand=1)
    
    # create pages for different item types
    self.atom_page = None
    self.bond_page = None
    self.arrow_page = None
    self.text_page = None
    self.plus_page = None
    self.font_page = None
    self.common_page = None
    arrows = []
    for o in items:
      if o.object_type == 'point':
        items.remove( o)
        if o.arrow not in arrows:
          arrows.append( o.arrow)
    items += arrows
    types = misc.filter_unique( [o.object_type for o in items])

    if 'atom' in types:
      self.atom_page = self.pages.add(_('Atom'))
      # charge
      charges = misc.filter_unique( [o.charge for o in items if hasattr( o, 'charge')])
      if len( charges) == 1:
        charge = charges[0]
      else:
        charge = ''
      self.atom_charge = Pmw.Counter( self.atom_page,
                                      labelpos = 'w',
                                      label_text = _('Charge'),
                                      entryfield_value = charge,
                                      entryfield_validate={ 'validator':'integer', 'min':-4, 'max':4},
                                      entry_width = 3,
                                      increment = 1,
                                      datatype = 'integer')
      self.atom_charge.pack( anchor='nw', padx=10, pady=5)
      # show?
      shows = misc.filter_unique( [o.show for o in items if hasattr( o, 'show')])
      if len( shows) == 1:
        show = int( shows[0])
      else:
        show = 2 # means the show should be preserved as is
      self.atom_show = Pmw.OptionMenu( self.atom_page,
                                       labelpos = 'nw',
                                       label_text = _('Atom name'),
                                       items = (_("don't show"),_("show"),u""),
                                       initialitem = show)
      self.atom_show.pack( anchor = 'nw')
      # positioning
      poss = misc.filter_unique( [o.pos for o in items if o.object_type == 'atom'])
      if not poss:
        pos = None
      elif len( poss) == 1 and poss[0]:
        pos = ['center-first', 'center-last'].index( poss[0])
      else:
        pos = 2 # means the centering should be preserved as is
      if pos == None:
        self.atom_pos = None
      else:
        self.atom_pos = Pmw.OptionMenu( self.atom_page,
                                        labelpos = 'nw',
                                        label_text = _('Atom positioning'),
                                        items = (_("center first letter"),_("center last letter"), u""),
                                        initialitem = pos)

        self.atom_pos.pack( anchor = 'nw')
      # show hydrogens
      shows = misc.filter_unique( [o.show_hydrogens for o in items if o.object_type == 'atom'])
      if len( shows) == 1:
        show = shows[0]
      else:
        show = 2 # means the show should be preserved as is
      self.atom_show_h = Pmw.OptionMenu( self.atom_page,
                                         labelpos = 'nw',
                                         label_text = _('Hydrogens'),
                                         items = (_("off"),_("on"), u""),
                                         initialitem = show)

      self.atom_show_h.pack( anchor = 'nw')

      # marks
      #self.marks = widgets.GraphicalAngleChooser( self.atom_page, 270)
      #self.marks.pack()

    # BOND
    if 'bond' in types:
      self.bond_page = self.pages.add(_('Bond'))
      # bond_widths (former distances)
      dists = misc.filter_unique( map( abs, [o.bond_width for o in items if o.object_type == 'bond']))
      if len( dists) == 1:
        dist = dists[0]
      else:
        dist = ''
      if not misc.split_number_and_unit( dist)[1]:
        dist = str( dist) + 'px'
      self.bond_dist = widgets.WidthChooser( self.bond_page, dist, label=_('Bond width'))
      self.bond_dist.pack( anchor='ne', padx=10, pady=5)

      # wedge_widths
      dists = misc.filter_unique( map( abs, [o.wedge_width for o in items if o.object_type == 'bond']))
      if len( dists) == 1:
        dist = dists[0]
      else:
        dist = ''
      if not misc.split_number_and_unit( dist)[1]:
        dist = str( dist) + 'px'
      self.wedge_width = widgets.WidthChooser( self.bond_page, dist, label=_('Wedge/Hatch width'))
      self.wedge_width.pack( anchor='ne', padx=10, pady=5)


      # double bond length ratio
      ratios = misc.filter_unique( [o.double_length_ratio for o in items if o.object_type == 'bond'])
      if len( ratios) == 1:
        ratio = ratios[0]
      else:
        ratio = ''
      self.double_length_ratio = widgets.RatioCounter( self.bond_page,
                                                       ratio,
                                                       label=_('Double-bond length ratio'))
      self.double_length_ratio.pack( anchor='nw', padx=10, pady=5)



    # ARROW
    if 'arrow' in types:
      self.arrow_page = self.pages.add(_('Arrow'))
      self.arrow_end_changed = 0
      self.arrow_start_changed = 0
      arrow_items = [o for o in items if o.object_type == 'arrow']

      # arrow start pins
      arrow_starts = misc.filter_unique( [o.get_pins()[0] for o in arrow_items])
      self.arrow_start = tkinter.IntVar()
      if len( arrow_starts) == 1:
        self.arrow_start.set( arrow_starts[0])
      else:
        self.arrow_start.set( 0)
      self.arrow_start_entry = tkinter.Checkbutton( self.arrow_page,
                                                    text=_('Arrow-head on start'),
                                                    variable = self.arrow_start,
                                                    command = self._arrow_start_changed)
      self.arrow_start_entry.pack( anchor='w')

      # arrow end pins
      arrow_ends = misc.filter_unique( [o.get_pins()[1] for o in arrow_items])
      self.arrow_end = tkinter.IntVar()
      if len( arrow_ends) == 1:
        self.arrow_end.set( arrow_ends[0])
      else:
        self.arrow_end.set( 0)
      self.arrow_end_entry = tkinter.Checkbutton( self.arrow_page,
                                                  text=_('Arrow-head on end'),
                                                  variable = self.arrow_end,
                                                  command = self._arrow_end_changed)
      self.arrow_end_entry.pack( anchor='w')

      # spline?
      splines = misc.filter_unique( [o.spline for o in arrow_items])
      self.spline = tkinter.IntVar()
      if len( splines) == 1:
        self.spline.set( splines[0])
      else:
        self.spline.set( 0)
      self.spline_entry = tkinter.Checkbutton( self.arrow_page,
                                               text=_('Spline arrow'),
                                               variable = self.spline,
                                               command = self._spline_changed)
      self.spline_changed = 0
      self.spline_entry.pack( anchor='w')
      

    # TEXTS

    # PLUS

    # FONT
    font_items = filter( lambda x: hasattr( x, 'font_family'), items)
    if font_items:
      self.font_page = self.pages.add(_('Font'))

      sizes = misc.filter_unique( [o.font_size for o in font_items])
      if len( sizes) == 1:
        size = sizes[0]
      else:
        size = ''
      self.font_size = widgets.FontSizeChooser( self.font_page, size)
      self.font_size.pack( anchor = 'nw')

      used_families = misc.filter_unique( [o.font_family for o in font_items])
      if len( used_families) == 1:
        self.used_family = used_families[0]
      else:
        self.used_family = ''
      self.font_family = widgets.FontFamilyChooser( self.font_page, self.used_family)
      self.font_family.pack( anchor="nw", side = 'bottom')


    # COMMON
    self.common_page = self.pages.add(_('Common'))
    line_items = filter( lambda x: hasattr( x, 'line_width'), items)
    if line_items:
      widths = misc.filter_unique( [o.line_width for o in line_items])
      if len( widths) == 1:
        width = widths[0]
      else:
        width = ''
      if not misc.split_number_and_unit( width)[1]:
        width = str( width) + 'px'
      self.line_width = widgets.WidthChooser( self.common_page, width, label=_('Line width'))
      self.line_width.pack( anchor='nw', padx=10, pady=5)

    line_color_items = filter( lambda x: hasattr( x, 'line_color'), items)
    if line_color_items:
      lines = misc.filter_unique( [o.line_color for o in line_color_items])
      if len( lines) == 1:
        line = lines[0]
      else:
        line = None
      self.line_color = widgets.ColorButtonWithTransparencyChecker( self.common_page, color=line, text=_("Line color"))
      self.line_color.pack( anchor='nw', padx=10, pady=10)

    area_color_items = filter( lambda x: hasattr( x, 'area_color'), items)
    if area_color_items:
      areas = misc.filter_unique( [o.area_color for o in area_color_items])
      if len( areas) == 1:
        area = areas[0]
      else:
        area = None
      self.area_color = widgets.ColorButtonWithTransparencyChecker( self.common_page, color=area, text=_("Area color"))
      self.area_color.pack( anchor='nw', padx=10, pady=5)


    # RUN IT ALL
    self.pages.setnaturalsize()
    self.dialog.activate( globalMode=0)


  def done( self, button):
    """called on dialog exit"""
    self.dialog.deactivate()
    if button != _('OK'):
      pass
    else:
      #print self.marks.get()
      # apply changes
      for o in self.items:
        change = 0
        # ATOM
        if o.object_type == 'atom':
          a = self.atom_show.index( Pmw.SELECT)
          if a != 2:
            o.show = a
            change = 1
          # positionning
          a = self.atom_pos.index( Pmw.SELECT)
          if a != 2:
            o.pos = ('center-first', 'center-last')[ a]
            change = 1
          if self.atom_charge.get():
            a = int( self.atom_charge.get())
            if hasattr( o, 'charge') and o.charge != a:
              o.charge = a
            change = 1
          # hydrogens
          a = int( self.atom_show_h.index( Pmw.SELECT))
          if a != 2:
            o.show_hydrogens = a
            change = 1
          # font is in common now
        # BOND
        elif o.object_type == 'bond':
          # width is in common now
          # bond_width
          d = Screen.any_to_px( self.bond_dist.getvalue())
          if d:
            if d != abs( o.bond_width):
              o.bond_width = d * misc.signum( o.bond_width)
              change = 1
          # wedge_width
          d = Screen.any_to_px( self.wedge_width.getvalue())
          if d:
            if d != o.wedge_width:
              o.wedge_width = d
              change = 1
          # ratio
          ratio = self.double_length_ratio.getvalue()
          if ratio:
            ratio = float( self.double_length_ratio.getvalue())
            if ratio != o.double_length_ratio:
              o.double_length_ratio = ratio
              change = 1
            
        # ARROW - most is in common now
        elif o.object_type == 'arrow':
          if self.arrow_start_changed:
            o.set_pins( start = self.arrow_start.get())
            change = 1
          if self.arrow_end_changed:
            o.set_pins( end = self.arrow_end.get())
            change = 1
          if self.spline_changed:
            o.spline = self.spline.get()
            change = 1
            
        # TEXT - all is in common now
        # PLUS - all is in common now
        # VECTOR - all is in common now

        # COMMON PROPERTIES
        # LINE COLOR
        if hasattr( o, 'line_color') and self.line_color.color:
          if self.line_color.color != o.line_color:
            o.line_color = self.line_color.color
            change = 1
        # AREA COLOR
        if hasattr( o, 'area_color') and self.area_color.color:
          if self.area_color.color != o.area_color:
            o.area_color = self.area_color.color
            change = 1
        # LINE WIDTH
        if hasattr( o, 'line_width'):
          w = Screen.any_to_px( self.line_width.getvalue())
          if w:
            if w != o.line_width:
              o.line_width = w
              change = 1
        # FONT
        if hasattr( o, 'font_family'):
          if self.font_size.get():
            a = int( self.font_size.get())
            o.font_size = a
            change = 1
          if self.font_family.getcurselection() and self.font_family.getcurselection()[0] != self.used_family:
            a = self.font_family.getcurselection()[0]
            o.font_family = a
            change = 1
          
        # APPLY THE CHANGES
        if change:
          o.redraw()
          self.changes_made = 1
    self.cleanup()


  def _arrow_end_changed( self):
    self.arrow_end_changed = 1

  def _arrow_start_changed( self):
    self.arrow_start_changed = 1

  def _spline_changed( self):
    self.spline_changed = 1

  def raise_me( self, event):
    self.dialog.tkraise()

  def cleanup( self):
    pass
    #self.parent.unbind_all( "<Button-1>")


## -------------------- FILE PROPERTIES DIALOG --------------------

class file_properties_dialog:

  def __init__( self, parent, paper):
    self.parent = parent
    self.paper = paper
    self.dialog = Pmw.Dialog( parent,
                              buttons=(_('OK'), _('Cancel')),
                              defaultbutton=_('OK'),
                              title=_('Page Setup'),
                              command=self.done,
                              master='parent')
    self.draw()
    self.dialog.activate()

  def draw( self):
    paper_frame = tkinter.Frame( self.dialog.interior(),
                                 bd=2,
                                 relief="groove")
    paper_frame.pack( padx=10, pady=10, anchor="n", fill="x")

    # paper type
    if self.paper._paper_properties['type'] == 'custom':
      t = _('Custom')
    else:
      t = self.paper._paper_properties['type']
    paper_types = sorted(data.paper_types.keys())
    self.paper_type_chooser = Pmw.OptionMenu( paper_frame,
                                              items=paper_types, #+[_('Custom')],
                                              initialitem = t,
                                              labelpos = 'w',
                                              label_text = _('Paper size')+':',
                                              menubutton_width = 10)
    self.paper_type_chooser.pack( anchor='w', padx=5, pady=5)
    # paper orientation
    self.paper_orientation_chooser = Pmw.RadioSelect( paper_frame,
                                                      buttontype='radiobutton',
                                                      orient='vertical',
                                                      pady=0)
    self.paper_orientation_chooser.add(_('Portrait'))
    self.paper_orientation_chooser.add(_('Landscape'))
    self.paper_orientation_chooser.pack( anchor='w', padx=5, pady=5)
    if self.paper._paper_properties['orientation'] == 'portrait':
      i = 0
    else:
      i = 1
    self.paper_orientation_chooser.invoke( i)

    # full svg or just the filled part
    crop_frame = tkinter.Frame( self.dialog.interior(),
                                 bd=2,
                                 relief="groove")
    crop_frame.pack( padx=10, pady=10, anchor="n", fill="x")

    self.crop_paper_in_svg = tkinter.IntVar()
    self.crop_paper_in_svg.set( self.paper.get_paper_property( 'crop_svg'))
    crop = tkinter.Checkbutton( crop_frame,
                                anchor="n",
                                text=_('Auto crop image in SVG?\n(applies to some other exports as well)'),
                                variable=self.crop_paper_in_svg,
                                command=self.crop_paper_changed)
    crop.pack( anchor='w', padx=5, pady=5)
    # margin for cropping
    margin = self.paper.get_paper_property( 'crop_margin')
    self.margin_entry = Pmw.Counter( crop_frame,
                                     labelpos = 'w',
                                     label_text=_("Margin for cropped image (in pixels):"),
                                     entryfield_value = margin,
                                     entryfield_validate={ 'validator':'integer', 'min':0, 'max':1000},
                                     entry_width = 5,
                                     increment = 5,
                                     datatype = 'integer')
    self.margin_entry.pack( anchor='n', padx=5, pady=5)
    # use real minus ?
    minus_frame = tkinter.Frame( self.dialog.interior(),
                                 bd=2,
                                 relief="groove")
    minus_frame.pack( padx=10, pady=10, anchor="n", fill="x")

    self.use_real_minus = tkinter.IntVar()
    use_real_minus_button = tkinter.Checkbutton( minus_frame,
                                                 text=_('Use real minus character (instead of hyphen)?'),
                                                 variable = self.use_real_minus)
    self.use_real_minus.set( self.paper.get_paper_property( 'use_real_minus'))
    use_real_minus_button.pack( anchor='w', padx=5, pady=5)

    # replace hyphens with minuses in export?
    self.replace_minus = tkinter.IntVar()
    replace_minus_button = tkinter.Checkbutton( minus_frame,
                                                text=_('Replace hyphens with minus in SVG export?'),
                                                variable = self.replace_minus)
    self.replace_minus.set( self.paper.get_paper_property( 'replace_minus'))
    # ***HACK***
    #replace_minus_button.pack( anchor='w', padx=5, pady=5)




  def done( self, button):
    self.dialog.deactivate()
    if button == _('OK'):
      if self.paper_orientation_chooser.getvalue() == _('Portrait'):
        o = 'portrait'
      else:
        o = 'landscape'
      type = self.paper_type_chooser.getvalue()
      if type == _('Custom'):
        type = 'custom'
      self.paper.set_paper_properties( type=type,
                                       orientation=o,
                                       crop_svg=self.crop_paper_in_svg.get(),
                                       crop_margin=int( self.margin_entry.getvalue()),
                                       use_real_minus=int( self.use_real_minus.get()),
                                       replace_minus=int( self.replace_minus.get()))
      self.paper.changes_made = 1


  def crop_paper_changed( self):
    return 
    val = self.crop_paper_in_svg.get()
    if not val:
      self.margin_entry.configure( entry_state="disabled")
    else:
      self.margin_entry.configure( entry_state="normal")





##-------------------- STANDARD VALUES DIALOG --------------------

class standard_values_dialog:

  def __init__( self, parent, standard):
    self.parent = parent
    self.standard = standard
    self.dialog = Pmw.Dialog( parent,
                              buttons=(_('OK'), _('Cancel'), _('Save')),
                              defaultbutton=_('OK'),
                              title=_('Standard values'),
                              command=self.done,
                              master='parent')
    self.body = self.dialog.interior()
    #self.body.pack( fill='both', expand=1)
    self.draw()
    self.dialog.activate()

  def draw( self):
    self.pages = Pmw.NoteBook( self.body)
    self.pages.pack( anchor='w', pady=0, padx=0, fill='both', expand=1)
    # COMMON
    common_page = self.pages.add( _('Common'))
    # LINE
    line_group = Pmw.Group( common_page, tag_text=_('Line'))
    line_group.pack( fill='x')
    # line width
    self.line_width = widgets.WidthChooser( line_group.interior(), self.standard.line_width, label=_('Line width'))
    self.line_width.pack( anchor='nw', padx=10, pady=5)
    # COLORS
    color_group = Pmw.Group( common_page, tag_text=_('Color'))
    color_group.pack( fill='x')
    # line color
    self.line_color = widgets.ColorButtonWithTransparencyChecker( color_group.interior(), color=self.standard.line_color, text=_("Line color"))
    self.line_color.pack( side='left', padx=10, pady=5)
    # area color
    self.area_color = widgets.ColorButtonWithTransparencyChecker( color_group.interior(), color=self.standard.area_color, text=_("Area color"))
    self.area_color.pack( side='right', padx=10, pady=5)

    # ATOM
    atom_group = self.pages.add( _('Atom'))
    self.show_hydrogens = tkinter.IntVar()
    self.show_hydrogens.set( int( self.standard.show_hydrogens))
    sh = tkinter.Checkbutton( atom_group, text=_('Show hydrogens on visible atoms'), variable=self.show_hydrogens)
    sh.pack( anchor='w', padx=10, pady=10)

    # BOND
    bond_group = self.pages.add( _("Bond")) #Pmw.Group( self.body, tag_text=_('Bond'))
    # bond width
    self.bond_width = widgets.WidthChooser( bond_group, self.standard.bond_width, label=_('Bond width'))
    self.bond_width.pack( anchor='ne', padx=10, pady=5)
    # wedge bond width
    self.wedge_width = widgets.WidthChooser( bond_group, self.standard.wedge_width, label=_('Wedge/Hatch width'))
    self.wedge_width.pack( anchor='ne', padx=10, pady=5)
    # bond length
    self.bond_length = widgets.LengthChooser( bond_group, self.standard.bond_length, label=_('Bond length'))
    self.bond_length.pack( anchor='ne', padx=10, pady=5)
    # double bond length ratio
    self.double_length_ratio = widgets.RatioCounter( bond_group,
                                                     self.standard.double_length_ratio,
                                                     label=_('Double-bond length ratio'))
    self.double_length_ratio.pack( anchor='ne', padx=10, pady=5)

    # FONT
    font_group = self.pages.add( _('Font'))
    # font size
    self.font_size = widgets.FontSizeChooser( font_group, self.standard.font_size)
    self.font_size.pack( anchor = 'nw')
    # font family
    self.font_family = widgets.FontFamilyChooser( font_group, self.standard.font_family)
    self.font_family.pack( anchor="nw", side='bottom')

    # PAPER
    # paper type
    self.paper = self.parent.paper
    paper_group = self.pages.add(_('Paper'))
    if self.paper._paper_properties['type'] == 'custom':
      t = _('Custom')
    else:
      t = self.paper._paper_properties['type']
    paper_types = data.paper_types.keys()
    paper_types.sort()
    self.paper_type_chooser = Pmw.OptionMenu( paper_group,
                                              items=paper_types, #+[_('Custom')],
                                              initialitem = t,
                                              labelpos = 'w',
                                              label_text = _('Paper size')+':',
                                              menubutton_width = 10)
    self.paper_type_chooser.pack( anchor='w', padx=10, pady=10)
    # paper orientation
    self.paper_orientation_chooser = Pmw.RadioSelect( paper_group,
                                                      buttontype='radiobutton',
                                                      orient='vertical',
                                                      pady=0)
    self.paper_orientation_chooser.add(_('Portrait'))
    self.paper_orientation_chooser.add(_('Landscape'))
    self.paper_orientation_chooser.pack( anchor='w', padx=10, pady=10)
    if self.paper._paper_properties['orientation'] == 'portrait':
      i = 0
    else:
      i = 1
    self.paper_orientation_chooser.invoke( i)
    # full svg or just the filled part
    self.crop_paper_in_svg = tkinter.IntVar()
    self.crop_paper_in_svg.set( self.paper.get_paper_property( 'crop_svg'))
    crop = tkinter.Checkbutton( paper_group, text=_('Auto crop image in SVG?'), variable=self.crop_paper_in_svg)
    crop.pack( anchor='w', padx=10, pady=10)
    # crop margin
    margin = self.paper.get_paper_property( 'crop_margin')
    self.margin_entry = Pmw.Counter( paper_group,
                                     labelpos = 'w',
                                     label_text=_("Margin for cropped image (in pixels):"),
                                     entryfield_value = margin,
                                     entryfield_validate={ 'validator':'integer', 'min':0, 'max':1000},
                                     entry_width = 5,
                                     increment = 5,
                                     datatype = 'integer')
    self.margin_entry.pack( anchor='w', padx=10, pady=10)


    # DIALOG WIDE PART
    # how to apply?
    apply_group = Pmw.Group( self.body, tag_text=_('Apply'))
    apply_group.pack( fill='x', padx=5, pady=5)
    # apply all or only the changed ones? - it must be created before apply_button because
    # of the callback that operates on activity of apply_button2
    self.apply_button2 = Pmw.RadioSelect( apply_group.interior(),
                                         buttontype = 'radiobutton',
                                         orient = 'vertical',
                                         pady = 0)
    self.apply_button2.add( _("changed values only"))
    self.apply_button2.add( _("all values"))
    self.apply_button2.invoke( 0)
    # apply to current drawing?
    self.apply_button = Pmw.RadioSelect( apply_group.interior(),
                                         buttontype = 'radiobutton',
                                         command = self._apply_button_callback,
                                         orient = 'vertical',
                                         pady = 0)
    self.apply_button.add( _("to new drawings only"))
    self.apply_button.add( _("to selected and new drawings (no resize)"))
    self.apply_button.add( _("to the whole drawing (no resize)"))
    self.apply_button.invoke( 0)
    self.apply_button.pack( padx=0, pady=0, anchor='w')
    # we pack the button2 here to get a better organization
    self.apply_button2.pack( padx=0, pady=10, anchor='w')

    self.pages.setnaturalsize()


  def done( self, button):
    if button == _('Save'):
      a = self.parent.paper.save_personal_standard( self.get_the_standard())
      if a:
        tkMessageBox.showinfo( _("Standard saved"),
                               _("The standard was successfully saved as personal standard to %s\n\nIt is not automatically applied to the current drawing and will be activated after you restart BKChem.\nYou can still apply the changes to the current drawing from the dialog window.") % a)
      else:
        tkMessageBox.showerror( _("Standard not saved"),
                                _("For some reason the standard couldn't be saved. Probably the right location for personal profile couldn't be found or wasn't writable. Sorry for the inconvenience."))
      return 
    self.dialog.deactivate()
    if button == _('OK'):
      self.standard = self.get_the_standard()
      self.apply = self.apply_button.index( self.apply_button.getvalue())
      self.apply_all = self.apply_button2.index( self.apply_button2.getvalue())
      self.change = 1
    else:
      self.change = 0
      self.apply_all = 0

  def get_the_standard( self):
    st = classes.standard()
    st.bond_width = self.bond_width.getvalue()
    st.line_width = self.line_width.getvalue()
    st.wedge_width = self.wedge_width.getvalue()
    st.bond_length = self.bond_length.getvalue()
    st.double_length_ratio = float( self.double_length_ratio.getvalue())
    st.line_color = self.line_color.color
    st.area_color = self.area_color.color
    st.font_family = self.font_family.getcurselection() and self.font_family.getcurselection()[0] or ''
    st.font_size = int( self.font_size.get())
    st.show_hydrogens = int( self.show_hydrogens.get())
    # paper properties
    # type
    type = self.paper_type_chooser.getvalue()
    if type == _('Custom'):
      type = 'custom'
    st.paper_type = type
    # orientation
    if self.paper_orientation_chooser.getvalue() == _('Portrait'):
      self.paper_orientation = 'portrait'
    else:
      st.paper_orientation = 'landscape'
    # crop_svg
    st.paper_crop_svg = self.crop_paper_in_svg.get()
    # crop_margin
    st.paper_crop_margin = self.margin_entry.getvalue()
    return st

  def _apply_button_callback( self, tag):
    if self.apply_button.index( tag) != 0:
      self.apply_button2.invoke(0)
      self.apply_button2.configure( Button_state = 'normal')
    else:
      self.apply_button2.invoke(1)
      self.apply_button2.configure( Button_state = 'disabled')







##-------------------- PREFERENCES DIALOG --------------------

class preferences_dialog:

  def __init__( self, parent, preferences):
    self.parent = parent
    self.preferences = preferences
    self.dialog = Pmw.Dialog( parent,
                              buttons=(_('OK'), _('Cancel')),
                              defaultbutton=_('OK'),
                              title=_('Preferences'),
                              command=self.done,
                              master='parent')
    self.body = self.dialog.interior()
    #self.body.pack( fill='both', expand=1)
    self.replace_minus = tkinter.IntVar()
    self.replace_minus.set( self.preferences.get_preference( "replace_minus") or 0)
    self.use_real_minus = tkinter.IntVar()
    self.use_real_minus.set( self.preferences.get_preference( "use_real_minus") or 0)
    self.use_real_minus_old = self.use_real_minus.get()
    self.result = 0

    self.draw()
    self.dialog.activate()



  def draw( self):
    self.pages = Pmw.NoteBook( self.body)
    self.pages.pack( anchor='w', pady=0, padx=0, fill='both', expand=1)
    # COMMON
    common_page = self.pages.add( _('Common'))
    # use real minus ?
    replace_minus_button = tkinter.Checkbutton( common_page, text=_('Use real minus character (instead of hyphen)?'),
                                                variable=self.use_real_minus)
    replace_minus_button.pack( anchor='w', padx=10, pady=10)

    # replace hyphens with minuses in export?
    # ***HACK***
    #replace_minus_button = tkinter.Checkbutton( common_page, text=_('Replace hyphens with minus in SVG export?'),
    #                                            variable=self.replace_minus)
    #replace_minus_button.pack( anchor='w', padx=10, pady=10)

    self.pages.setnaturalsize()



  def done( self, button):
    self.dialog.deactivate()
    if button == _('OK'):
      #self.preferences.add_preference( "replace_minus", self.replace_minus.get())
      self.preferences.add_preference( "use_real_minus", self.use_real_minus.get())
      if self.use_real_minus.get() != self.use_real_minus_old:
        self.result = 1
    else:
      pass







## -------------------- fragment overwiev --------------------

class fragment_dialog( Pmw.Dialog):

  def __init__( self, paper, deletion=True):
    self.paper = paper
    if deletion:
      butts = (_('OK'), _('Delete'), _('Cancel'))
    else:
      butts = (_('OK'), _('Cancel'))

    Pmw.Dialog.__init__( self,
                         Store.app,
                         buttons=butts,
                         defaultbutton=_('OK'),
                         title=_('Fragment overview'),
                         command=self.done,
                         master='parent')

    self._items = set()
    self._frags = {}
    self.value = None
    self.init_list()


  def init_list( self):
    self.list = Pmw.ScrolledListBox( self.interior(),
                                     selectioncommand=self.select,
                                     labelpos = "n",
                                     label_text=_("Fragments"),
                                     listbox_selectmode="single",
                                     listbox_width=30,
                                     items=self.get_all_fragments())
    self.list.pack()


  def get_all_fragments( self):
    self._frags = {}
    for m in self.paper.molecules:
      for frag in m.fragments:
        text_form = "%s (%s)" % (frag.name, frag.id)
        self._frags[ text_form] = frag
    return self._frags.keys()


  def select( self):
    self.clean()
    if self.list.getvalue():
      frag = self._frags[ self.list.getvalue()[0]]
      self.value = frag
      self._highlight( frag)



  def _highlight( self, frag, size=3):
    for b in frag.edges:
      x1, y1 = b.atom1.get_xy()
      x2, y2 = b.atom2.get_xy()
      x = (x1 + x2) / 2
      y = (y1 + y2) / 2
      self._items.add( self.paper.create_oval( x-size, y-size, x+size, y+size, fill="orange", outline="red"))
    for a in frag.vertices:
      self._items.add( self.paper.create_oval( a.x-size, a.y-size, a.x+size, a.y+size, fill="orange", outline="red"))



  def clean( self):
    map( self.paper.delete, self._items)
    self._items = set()


  def done( self, button):
    if button == _('Delete'):
      self._delete_selected()
      return
    self.clean()
    self.deactivate()


  def _delete_selected( self):
    if self.value:
      mol = list( self.value.edges | self.value.vertices)[0].molecule
      mol.delete_fragment( self.value)
    self.list.setlist( self.get_all_fragments())



## -------------------- logging dialog --------------------

class logging_dialog( Pmw.Dialog):

  def __init__( self, paper, logger):
    self.logger = logger
    Pmw.Dialog.__init__( self,
                         Store.app,
                         buttons=(_('OK'), _('Cancel')),
                         defaultbutton=_('OK'),
                         title=_('Logging'),
                         command=self.done,
                         master='parent')
    self.init_list()


  def init_list( self):
    root = self.interior()
    self.choosers = {}
    tkinter.Label( root, text=_("Choose how each type of message is to be shown:"), font=("Helvetica", 12, "bold")).pack( pady=10)
    for message_type in self.logger.type_order:
      f = tkinter.Frame( root)
      label = tkinter.Label( f, text=self.logger.type_to_text[message_type], font=("Helvetica", 12, "bold"))
      label.pack( side='left', anchor="w")
      chooser = Pmw.RadioSelect( f,
                                 buttontype='radiobutton',
                                 orient='horizontal',
                                 pady=0)
      self.choosers[message_type] = chooser                                         
      for handle_type in self.logger.handle_order:
        chooser.add( self.logger.handle_to_text[handle_type])
      chooser.invoke( self.logger.handle_order.index( self.logger.handling[message_type]))
      chooser.pack( side='right', anchor='e', padx=5, pady=5)
      f.pack( fill="x")
    tkinter.Label( root, text=_("The setting will be immediately applied and saved on application exit.")).pack( pady=10)


  def done( self, button):
    if button == _("OK"):
      self.proceed = True
      for message_type,chooser in self.choosers.items():
        index = chooser.index( chooser.getvalue())
        self.logger.set_handling( message_type, self.logger.handle_order[index])
    self.deactivate()





## -------------------- language dialog --------------------

class language_dialog( Pmw.Dialog):

  def __init__( self, paper):
    Pmw.Dialog.__init__( self,
                         Store.app,
                         buttons=(_('OK'), _('Cancel')),
                         defaultbutton=_('OK'),
                         title=_('Language'),
                         command=self.done,
                         master='parent')
    self.proceed = False
    self.init_list()



  def init_list( self):
    langs = []
    import gettext
    self.languages = {}
    for lang, language in data.languages.items():
      system = gettext.find( 'BKChem', None, [lang])
      local = gettext.find( 'BKChem', os.path.normpath( os.path.join( os_support.get_bkchem_run_dir(), '../locale')), [lang])
      if system or local or lang == "en":
        lang_text = "%s (%s)" % (language, lang)
        langs.append( lang_text)
        self.languages[lang_text] = lang
    langs.sort()
    # default
    default = "%s (default)"%_("System default")
    self.languages[default] = "default"
    langs.append( default)

    self.list = Pmw.ScrolledListBox( self.interior(),
                                     #selectioncommand=self.select,
                                     labelpos = "n",
                                     label_text=_("Available Languages"),
                                     listbox_selectmode="single",
                                     listbox_width=30,
                                     items=langs)
    del gettext
    self.list.pack()


  def done( self, button):
    if button == _("OK"):
      self.proceed = True
    self.deactivate()
    




## -------------------- PROGRESS DIALOG --------------------

class progress_dialog( tkinter.Toplevel):

  bar_width = 300
  bar_height = 20
  bar_fontsize = 8


  def __init__(self, parent, title=None):
    
    self.parent = parent

    tkinter.Toplevel.__init__(self, parent)
    self.transient(parent)
    self.geometry("+%d+%d" % (parent.winfo_rootx()+200,
                              parent.winfo_rooty()+200))
    #self.resizable( 0, 0)
    self.update_idletasks()
    
    if title:
      self.title(title)

    body = tkinter.Frame(self)
    body.pack(padx=5, pady=5, side="left", expand=1, fill="both")

    self.top_text = tkinter.StringVar()
    tkinter.Label( body, textvariable=self.top_text, width=50, height=1, anchor="w").grid( row=1, sticky="W")

    self.canvas = tkinter.Canvas( body, width=self.bar_width, height=self.bar_height, background="white")
    self.canvas.grid( row=2)
    self.bar = self.canvas.create_rectangle( 0, 0, 0, self.bar_height, fill="#7395c8")
    self.ratio = self.canvas.create_text( (self.bar_width/2)-10,
                                          self.bar_height-8,
                                          text="0%",
                                          font="Helvetica %d normal" % self.bar_fontsize)

    self.bottom_text = tkinter.StringVar()
    tkinter.Label( body, textvariable=self.bottom_text, width=50, height=1, anchor="w").grid( row=3, sticky="W")

    self.grab_set()
    self.protocol("WM_DELETE_WINDOW", self.close)

    self.focus_set()
    self.update_idletasks()
    self.parent.update_idletasks()
    #self.wait_window(self)


  def update( self, ratio, top_text="", bottom_text=""):
    self.set_ratio( ratio)
    if top_text:
      self.top_text.set( top_text)
    if bottom_text:
      self.bottom_text.set( bottom_text)
    
    self.update_idletasks()
    

  def set_ratio( self, ratio):
    self.canvas.coords( self.bar, 0, 0, ratio*self.bar_width, self.bar_height)
    self.canvas.itemconfig( self.ratio, text="%d%%" % (100*ratio)) 


  def close( self):
    self.parent.focus_set()
    self.destroy()

