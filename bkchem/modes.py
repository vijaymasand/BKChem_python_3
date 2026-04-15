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


"""the modes in which the paper operates (such as edit, draw etc.) reside here"""

# Internationalization
try:
    _
except NameError:
    _ = lambda x: x

from . import misc
from warnings import warn
import operator
from .oasa import geometry
import math
from functools import reduce
try:
  from .oasa.oasa.transform import transform 
  from .oasa.oasa.transform3d import transform3d
except ImportError:
  from .oasa.transform import transform
  from .oasa.transform3d import transform3d
import time
from . import data
from . import config
import string
from . import dialogs
import xml.sax, xml.sax.saxutils
import tkinter.messagebox as tkMessageBox
from . import helper_graphics as hg
from . import dom_extensions
from . import messages
from .bond import bond
from .atom import atom
from .group import group
from .textatom import textatom
from .context_menu import context_menu
from .reaction import reaction
from . import parents, special_parents
from . import oasa
import Pmw
import tkinter as Tkinter
from .oasa import periodic_table as PT
from . import external_data

from . import interactors
from . import marks
import types
from .arrow import arrow
from .ftext import ftext

from .singleton_store import Store, Screen



## -------------------- PARENT MODES--------------------

class mode( object):
  """abstract parent for all modes. No to be used for inheritation because the more specialized
  edit mode has all the methods for editing - just override what you need to change"""
  def __init__( self):
    self.name = 'mode'
    self.submodes = []
    self.submode = []
    self.pulldown_menu_submodes = []
    self._key_sequences = {}
    self._recent_key_seq = ''
    self._specials_pressed = { 'C':0, 'A':0, 'M':0, 'S':0} # C-A-M-S
    
  def mouse_down( self, event, modifiers=[]):
    pass

  def mouse_down3( self, event, modifiers=[]):
    pass

  def mouse_down2( self, event, modifiers=[]):    
    pass

  def mouse_up( self, event):
    pass

  def mouse_click( self, event):
    pass

  def mouse_drag( self, event):
    pass

  def enter_object( self, object, event):
    pass

  def leave_object( self, event):
    pass

  def mouse_move( self, event):
    pass

  def key_pressed( self, event):
    key = event_to_key( event) # Note: event.state can be used to query CAMS
    # first filter off specials (CAMS)
    if len( key) == 1 and key in 'CAMS':
      self._specials_pressed[ key] = 1
    else:
      # then if key is not CAMS update the recent key sequence
      # CAMS modificators first
      first = 1 # to separate each step with ' '
      for a in 'CAMS':
        if self._specials_pressed[ a]:
          if self._recent_key_seq:
            if first:
              self._recent_key_seq += ' ' + a
            else:
              self._recent_key_seq += '-' + a
          else:
            self._recent_key_seq = a
          first = 0
      # then the key itself 
      if self._recent_key_seq:
        if first:
          first = 0
          self._recent_key_seq += ' ' + key
        else:
          self._recent_key_seq += '-' + key
      else:
        self._recent_key_seq = key
      # look if the keysequence is registered
      if self._recent_key_seq in self._key_sequences:
        Store.log( self._recent_key_seq)
        self._key_sequences[ self._recent_key_seq]()
        self._recent_key_seq = ''
      else:
        # or its a prefix of some registered sequence
        for key in self._key_sequences.keys():
          if key.find(self._recent_key_seq) != -1:
            Store.log( self._recent_key_seq)
            return None
        # if we get here it means that the key is neither used nor a prefix
        self._recent_key_seq = ''

      
  def key_released( self, event):
    key = event_to_key( event)
    if len( key) == 1 and key in 'CAMS':
      self._specials_pressed[ key] = 0

  def clean_key_queue( self):
    """cleans status of all special keys;
    needed because especially after C-x C-f the C-release is grabed by dialog
    and never makes it to paper, therefor paper calls this after a file was read"""
    for key in self._specials_pressed.keys():
      self._specials_pressed[ key] = 0

  def get_name( self):
    return self.name

  def get_submode( self, i):
    if i < len( self.submodes):
      return self.submodes[i][ self.submode[i]]
    raise ValueError("invalid submode index")

  def set_submode( self, name):
    for sms in self.submodes:
      if name in sms:
        i = self.submodes.index( sms)
        self.submode[i] = sms.index( name)
        txt_name = self.__class__.__name__+'_'+name
        try:
          Store.log( messages.__dict__[txt_name], delay=20, message_type="hint")
        except KeyError:
          pass
        self.on_submode_switch( i, name)
        break

  def register_key_sequence( self, sequence, function, use_warning = 0):
    """registers a function with its coresponding key sequence
    when use_warning is true (default) than issues warning about overriden
    or shadowed bindings. In most cases its good idea to let it check the bindings."""
    # registering a range
    if sequence.find( "##") >= 0:
      prefix, end = sequence.split('##')
      for c in end:
        self.register_key_sequence( prefix+c, misc.lazy_apply( function, (prefix+c,)), use_warning=use_warning)
    # check of already registered values
    if use_warning and sequence in self._key_sequences:
      warn( "binding of sequence %s to function %s overrides its binding to function %s" %
            (sequence, function.__name__, self._key_sequences[ sequence].__name__),
            UserWarning, 2)
    elif use_warning:
      for key in self._key_sequences.keys():
        if key.find(sequence) != -1:
          warn( "binding of sequence %s to function %s shadows %s (binded to %s)" %
                (sequence, function.__name__, key, self._key_sequences[ key].__name__),
                UserWarning, 2)
    # the registration
    self._key_sequences[ sequence] = function

  def register_key_sequence_ending_with_number_range( self, sequence_base, function, numbers=None, attrs=None):
    if not numbers:
      numbers = []
    for i in numbers:
      if sequence_base and sequence_base.endswith( "-"):
        b = sequence_base
      elif sequence_base and not sequence_base.endswith( ' '):
        b = sequence_base+' '
      else:
        b = sequence_base
      self.register_key_sequence( b+str(i), misc.lazy_apply( function, (i,), attrs=attrs))


  def unregister_all_sequences( self):
    self._key_sequences = {}


  def cleanup( self, paper=None):
    """called when switching to another mode"""
    if self.focused:
      self.focused.unfocus()
      self.focused = None
  

  def startup( self):
    """called when switching to this mode"""
    txt_name = self.__class__.__name__+"_startup"
    message = messages.__dict__.get( txt_name, "")
    if message:
      Store.log( message, delay=20, message_type="hint")
    

  def on_submode_switch( self, submode_index, name=''):
    """called when submode is switched"""
    pass


  def on_paper_switch( self, old_paper, new_paper):
    """called when paper is switched"""
    pass

  def copy_settings( self, old_mode):
    """called when modes are changed, enables new mode to copy settings from old_mode"""
    self._specials_pressed = dict( old_mode._specials_pressed)


## -------------------- BASIC MODE --------------------

class simple_mode( mode):
  """little more sophisticated parent mode""" 


  def __init__( self):
    mode.__init__( self)
    self.focused = None



  def enter_object( self, object, event):
    if self.focused:
      self.focused.unfocus()
    self.focused = object
    self.focused.focus()



  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None




  def on_paper_switch( self, old_paper, new_paper):
    """called when paper is switched"""
    self.focused = None




class basic_mode( simple_mode):

  def __init__( self):
    simple_mode.__init__( self)
    self.name = "simple"
    # align
    self.register_key_sequence( 'C-a C-t', lambda : Store.app.paper.align_selected( 't'))
    self.register_key_sequence( 'C-a C-b', lambda : Store.app.paper.align_selected( 'b'))
    self.register_key_sequence( 'C-a C-l', lambda : Store.app.paper.align_selected( 'l'))
    self.register_key_sequence( 'C-a C-r', lambda : Store.app.paper.align_selected( 'r'))
    self.register_key_sequence( 'C-a C-h', lambda : Store.app.paper.align_selected( 'h'))
    self.register_key_sequence( 'C-a C-v', lambda : Store.app.paper.align_selected( 'v'))
    # other
    self.register_key_sequence( 'C-d C-c', lambda : Store.app.paper.toggle_center_for_selected())
    self.register_key_sequence( 'C-d C-w', lambda : Store.app.paper.display_weight_of_selected())
    self.register_key_sequence( 'C-d C-i', lambda : Store.app.paper.display_info_on_selected())
    # object related key bindings
    self.register_key_sequence( 'C-o C-i', lambda : Store.app.paper.display_info_on_selected())
    self.register_key_sequence( 'C-o C-c', lambda : Store.app.paper.check_chemistry_of_selected())
    self.register_key_sequence( 'C-o C-d', lambda : interactors.ask_display_form_for_selected( Store.app.paper))
    # emacs like key bindings
    self.register_key_sequence( 'C-x C-s', Store.app.save_CDML)
    self.register_key_sequence( 'C-x C-w', Store.app.save_as_CDML)
    self.register_key_sequence( 'C-x C-f', Store.app.load_CDML)
    self.register_key_sequence( 'C-x C-c', Store.app._quit)
    self.register_key_sequence( 'C-x C-t', Store.app.close_current_paper)
    self.register_key_sequence( 'C-x C-n', Store.app.add_new_paper)
    self.register_key_sequence( 'C-/', lambda : Store.app.paper.undo())
    self.register_key_sequence( 'C-S-?', lambda : Store.app.paper.redo()) #note that 'S-/' => 'S-?'  !!!
    # windows style key bindings
    self.register_key_sequence( 'C-p', lambda : Store.app.print_file())
    self.register_key_sequence( 'C-s', Store.app.save_CDML)
    self.register_key_sequence( 'C-z', self.undo)
    self.register_key_sequence( 'C-S-z', self.redo)
    # 'C-a' from windoze is in use - 'C-S-a' instead
    self.register_key_sequence( 'C-S-a', lambda : Store.app.paper.select_all())
    # arrow moving
    self.register_key_sequence( 'Up', lambda : self._move_selected( 0, -1))
    self.register_key_sequence( 'Down', lambda : self._move_selected( 0, 1))
    self.register_key_sequence( 'Left', lambda : self._move_selected( -1, 0))
    self.register_key_sequence( 'Right', lambda : self._move_selected( 1, 0))
    # manipulation of the paper.stack
    self.register_key_sequence( 'C-o C-f', lambda : Store.app.paper.lift_selected_to_top())
    self.register_key_sequence( 'C-o C-b', lambda : Store.app.paper.lower_selected_to_bottom())
    self.register_key_sequence( 'C-o C-s', lambda : Store.app.paper.swap_selected_on_stack())
    # mode switching
    self.register_key_sequence_ending_with_number_range( 'C-', self.switch_mode, numbers=range(1,10))
    self.register_key_sequence_ending_with_number_range( 'C-A-', self.switch_mode, numbers=range(1,10), attrs={"add":9})

  def undo( self):
    Store.app.paper.undo()
    if self.focused and not Store.app.paper.is_registered_object( self.focused):
      # focused object was deleted
      self.focused = None

  def redo( self):
    Store.app.paper.redo()
    if self.focused and not Store.app.paper.is_registered_object( self.focused):
      # focused object was deleted
      self.focused = None
  
  def switch_mode( self, n, add=0):
    index = n+add-1
    if index < len( Store.app.modes_sort):
      self.cleanup()
      Store.app.radiobuttons.invoke( index) #change_mode( Store.app.modes_sort[n-1])


## /// -------------------- PARENT MODES --------------------



### -------------------- EDIT MODE --------------------

class edit_mode( basic_mode):
  """basic editing mode, also good as parent for more specialized modes"""
  def __init__( self):
    basic_mode.__init__( self)
    self.name = _('edit')
    self._dragging = 0
    self._dragged_molecule = None
    self._block_leave_event = 0
    self._moving_selected_arrow = None
    self._last_click_time = 0
    self.focused = None
    # responses to key events
    self.register_key_sequence( ' ', self._set_name_to_selected)
    self.register_key_sequence( '##'+string.ascii_lowercase, self._set_name_to_selected)
    self.register_key_sequence( 'S-##'+string.ascii_lowercase, self._set_name_to_selected)    
    self.register_key_sequence( 'Return', self._set_old_name_to_selected) 
    self.register_key_sequence( 'Delete', self._delete_selected, use_warning=0)
    self.register_key_sequence( 'BackSpace', self._delete_selected, use_warning=0)
    # object related key bindings
    self.register_key_sequence( 'C-o C-e', self._expand_groups)
    # emacs like key bindings
    self.register_key_sequence( 'A-w', lambda : Store.app.paper.selected_to_clipboard())
    self.register_key_sequence( 'M-w', lambda : Store.app.paper.selected_to_clipboard())
    self.register_key_sequence( 'C-w', lambda : Store.app.paper.selected_to_clipboard( delete_afterwards=1))
    self.register_key_sequence( 'C-y', self._paste_clipboard)
    # windows style key bindings
    self.register_key_sequence( 'C-c', lambda : Store.app.paper.selected_to_clipboard())
    self.register_key_sequence( 'C-v', self._paste_clipboard)
    # 'C-x' from windoze is in use - 'C-k' instead
    self.register_key_sequence( 'C-k', lambda : Store.app.paper.selected_to_clipboard( delete_afterwards=1))
    # 'C-a' from windoze is in use - 'C-S-a' instead
    # chains (C-d as draw)
    self.register_key_sequence_ending_with_number_range( 'C-d', self.add_chain, numbers=range(2,10))

    # config
    self.rectangle_selection = True  # this can be overriden by children

    self._move_sofar = 0
    


  def mouse_down( self, event, modifiers=None):
    mods = modifiers or []
    self._shift = 'shift' in mods
    self._ctrl = 'ctrl' in mods
    self._alt = 'alt' in mods
    # we focus what is under cursor if its not focused already
    if not self.focused:
      ids = Store.app.paper.find_overlapping( event.x, event.y, event.x, event.y)
      if ids and Store.app.paper.is_registered_id( ids[-1]):
        self.focused = Store.app.paper.id_to_object( ids[-1])
        self.focused.focus()
    if self.focused and isinstance( self.focused, hg.selection_square):
      # we will need that later to fix the right corner of the selection_square
      self._startx, self._starty = self.focused.get_fix()
    else:
      self._startx, self._starty = event.x, event.y
    self._block_leave_event = 1





  def mouse_down3( self, event, modifiers=None):
    mods = modifiers or []
    if self.focused:
      if self.focused not in Store.app.paper.selected:
        Store.app.paper.unselect_all()
        Store.app.paper.select( [self.focused])
      dialog = context_menu( Store.app.paper.selected[:])
      dialog.post( event.x_root, event.y_root)




  def mouse_down2( self, event, modifiers=None):
    mods = modifiers or []
    if self.focused and not isinstance( self.focused, marks.mark):
      if self.focused not in Store.app.paper.selected:
        if not "shift" in mods:
          Store.app.paper.unselect_all()
        Store.app.paper.select( [self.focused])
      dialog = dialogs.config_dialog( Store.app, Store.app.paper.selected[:])
      if dialog.changes_made:
        Store.app.paper.start_new_undo_record()
      Store.app.paper.add_bindings()
      




  def mouse_up( self, event):
    self._block_leave_event = 0
    self._move_sofar = 0
    # this strange thing makes the moving of selected arrows and polygons possible - the problem is
    # that these objects are not in Store.app.paper.selected (only their points) and thus ...
    if self._moving_selected_arrow:
      Store.app.paper.select( [self._moving_selected_arrow])
      self._moving_selected_arrow = None
    if not self._dragging:
      self.mouse_click( event)
    else:
      if self._dragging == 3:
        self._end_of_empty_drag( self._startx, self._starty, event.x, event.y)
        Store.app.paper.delete( self._selection_rect)
      elif self._dragging == 1:
        # repositioning of atoms and double bonds
        atoms = reduce( operator.add, [o.neighbors for o in Store.app.paper.selected if isinstance( o, oasa.graph.vertex) and not o in Store.app.paper.selected], [])
        atoms = misc.filter_unique( [o for o in Store.app.paper.selected if isinstance( o, oasa.graph.vertex)] + atoms)
        [o.decide_pos() for o in atoms]
        [o.redraw() for o in atoms]
        [self.reposition_bonds_around_atom( o) for o in atoms]
        [self.reposition_bonds_around_bond( o) for o in self._bonds_to_update]
        Store.app.paper.handle_overlap()
        Store.app.paper.start_new_undo_record()
      elif self._dragging == 2:
        Store.app.paper.handle_overlap()
        Store.app.paper.start_new_undo_record()
      elif self._dragging == 4:
        if self.focused:
          # the unfocus will otherwise not happen and cursor won't be restored
          self.focused.unfocus()
          self.focused = None
        Store.app.paper.start_new_undo_record()
      self._dragging = 0
      Store.app.paper.add_bindings()


    
  def mouse_click( self, event):
    if not self._shift:
      Store.app.paper.unselect_all()

    if self.focused:
#      if self.focused.object_type == 'arrow':
#        Store.app.paper.select( self.focused.points)
#      else:
      if self.focused in Store.app.paper.selected:
        Store.app.paper.unselect( [self.focused])
      elif (self.focused.object_type == 'selection_rect') and (self.focused.object in Store.app.paper.selected):
        Store.app.paper.unselect( [self.focused.object])
      else:
        if self.focused.object_type == 'selection_rect':
          Store.app.paper.select( [self.focused.object])
        else:
          Store.app.paper.select( [self.focused])
      # double click?
      t = time.time()
      if t - self._last_click_time < 0.3:
        self._last_click_time = 0
        self.double_click( event)
      else:
        self._last_click_time = t

      # when clicked with Ctrl pressed delete the focused atom
      if self._ctrl:
        self._delete_selected()

    Store.app.paper.add_bindings()



  def double_click( self, event):
    if self.focused:
      if misc.isinstance_of_one( self.focused, (oasa.graph.vertex, bond)):
        Store.app.paper.select( tuple( self.focused.molecule)) # molecule is iterator


  def mouse_drag( self, event):
    if self._ctrl:
      dx = 0
    else:
      dx = event.x-self._startx
    if self._shift: # shift to move only in x
      dy = 0
    else:
      dy = event.y-self._starty
    if not self._dragging:
      # drag threshhold
      self._move_sofar += math.sqrt( dx**2 + dy**2)
      if self._move_sofar <= 1.0:
        return

      if self.focused and (self.focused.object_type == 'arrow' or self.focused.object_type == 'polygon' or self.focused.object_type == "polyline"):
        for p in self.focused.points:
          if p in Store.app.paper.selected:
            self._moving_selected_arrow = self.focused
            Store.app.paper.unselect( self.focused.points)
            break
      if self.focused and self.focused.object_type == 'selection_rect':
        # resizing of vector graphics
        self._dragging = 4
        self._dragged_molecule = self.focused
      elif self.focused and (self.focused in Store.app.paper.selected) or self._moving_selected_arrow:
        ### move all selected
        self._dragging = 1
        Store.app.paper.select( Store.app.paper.atoms_to_update())
        self._bonds_to_update = Store.app.paper.bonds_to_update()
        self._arrows_to_update = Store.app.paper.arrows_to_update()
        self.focused.unfocus()
        self.focused = None
      elif self.focused:
        ### move container of focused item
        self._dragging = 2
        if isinstance( self.focused, parents.child):
          self._dragged_molecule = self.focused.parent
        else:
          self._dragged_molecule = self.focused
        self.focused.unfocus()
        self.focused = None
      elif self.rectangle_selection:
        ### select everything in selection rectangle
        if not self._shift:
          Store.app.paper.unselect_all()
        self._dragging = 3
        self._selection_rect = Store.app.paper.create_rectangle( self._startx, self._starty, event.x, event.y)
      else:
        ### don't do anything
        self._dragging = 10  # just a placeholder to know that click should not be called
    if self._dragging == 1:
      [o.move( dx, dy) for o in Store.app.paper.selected]
      if self._moving_selected_arrow:
        self._moving_selected_arrow.move( dx, dy)
      [o.redraw() for o in self._bonds_to_update]
      [o.redraw() for o in self._arrows_to_update]
      self._startx, self._starty = event.x, event.y
    elif self._dragging == 2:
      self._dragged_molecule.move( dx, dy)
      self._startx, self._starty = event.x, event.y
    elif self._dragging == 3:
      Store.app.paper.coords( self._selection_rect, self._startx, self._starty, event.x, event.y)
    elif self._dragging == 4:
      # whole means that the selection-rect is moving whole, not only one part
      whole = self._dragged_molecule.drag( event.x, event.y, fix=(self._startx, self._starty))
      if whole:
        self._startx, self._starty = event.x, event.y
      else:
        Store.log( '%i, %i' % ( dx, dy))
      
  def enter_object( self, object, event):
    if not self._dragging:
      if self.focused:
        self.focused.unfocus()
      self.focused = object
      if self.focused.object_type == 'selection_rect':
        self.focused.focus( item= Store.app.paper.find_withtag( 'current')[0])
      else:
        self.focused.focus()

  def leave_object( self, event):
    if self._block_leave_event:
      return
    if not self._dragging:
      if self.focused:
        self.focused.unfocus()
        self.focused = None

  def reposition_bonds_around_atom( self, a):
    bs = a.neighbor_edges
    [b.redraw( recalc_side = 1) for b in bs] # if b.order == 2]
    if isinstance( a, textatom) or isinstance( a, atom):
      a.reposition_marks()

  def reposition_bonds_around_bond( self, b):
    bs = misc.filter_unique( b.atom1.neighbor_edges + b.atom2.neighbor_edges)
    [b.redraw( recalc_side = 1) for b in bs if b.order == 2]
    # all atoms to update
    atms = misc.filter_unique( reduce( operator.add, [[b.atom1,b.atom2] for b in bs], []))
    [a.reposition_marks() for a in atms if isinstance( a, atom)]


  def _end_of_empty_drag( self, x1, y1, x2, y2):
    Store.app.paper.select( filter( lambda o: o,\
                                    map( Store.app.paper.id_to_object,\
                                         Store.app.paper.find_enclosed( x1, y1, x2, y2))))



  ## METHODS FOR KEY EVENTS RESPONSES

  def _delete_selected( self):
    if self.focused and self.focused.object_type == 'selection_rect' and self.focused.object in Store.app.paper.selected:
      self.focused.unfocus()
      self.focused = None
    Store.app.paper.delete_selected()
    if self.focused and not Store.app.paper.is_registered_object( self.focused):
      # focused object was deleted
      self.focused = None
    Store.app.paper.add_bindings()

  def _paste_clipboard( self):
    Store.app.paper.unselect_all()
    xy = (Store.app.paper.canvasx( Store.app.paper.winfo_pointerx() -Store.app.paper.winfo_rootx()),
          Store.app.paper.canvasy( Store.app.paper.winfo_pointery() -Store.app.paper.winfo_rooty()))
    if xy[0] > 0 and xy[1] > 0:
      Store.app.paper.paste_clipboard( xy)

  def _set_name_to_selected( self, char=''):
    if Store.app.paper.selected:
      if not [i for i in Store.app.paper.selected if isinstance( i, parents.text_like)]:
        return # well, we do not want to set text to bonds and pluses anyway
      # check if we should start with the last used text or edit the one of selected things
      text = ''
      select = 1
      # the initial value for editing
      if char != '':
        if char.startswith("S-"):
          text = char[2:].upper()
        else:
          text = char
        select = 0
      elif len( Store.app.paper.selected) == 1:
        item = Store.app.paper.selected[0]
        if isinstance( item, parents.text_like):
          text = item.xml_ftext
      if text:
        name = Store.app.editPool.activate( text=text, select=select)
      else:
        name = Store.app.editPool.activate()
      if not name or dom_extensions.isOnlyTags( name):
        return
      name = str(name).encode('utf-8')
      self.set_given_name_to_selected( name, interpret=Store.app.editPool.interpret)



  def _set_old_name_to_selected( self):
    self.set_given_name_to_selected( Store.app.editPool.text)



  def set_given_name_to_selected( self, name, interpret=1):
    vtype = Store.app.paper.set_name_to_selected( name, interpret=interpret)
    # inform the user what was set
    interactors.log_atom_type( vtype)
    # cleanup
    [self.reposition_bonds_around_bond( o) for o in Store.app.paper.bonds_to_update()]
    [self.reposition_bonds_around_atom( o) for o in Store.app.paper.selected if o.object_type == "atom"]
    Store.app.paper.add_bindings()
    



  def _move_selected( self, dx, dy):
    Store.app.paper.select( Store.app.paper.atoms_to_update())
    _bonds_to_update = Store.app.paper.bonds_to_update()
    _arrows_to_update = Store.app.paper.arrows_to_update()

    [o.move( dx, dy) for o in Store.app.paper.selected]
    [o.redraw() for o in _bonds_to_update]
    [o.redraw() for o in _arrows_to_update]
    if Store.app.paper.um.get_last_record_name() == "arrow-key-move":
      Store.app.paper.um.delete_last_record()
    Store.app.paper.add_bindings()
    Store.app.paper.start_new_undo_record( name="arrow-key-move")

  def _expand_groups( self):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    Store.app.paper.expand_groups()

  def add_chain( self, n):
    if not self.focused:
      return
    a = self.focused
    mol = a.molecule
    for i in range( n):
      a, b = mol.add_atom_to( a)
      Store.app.paper.select( [a])
    Store.app.paper.start_new_undo_record()
    Store.app.paper.add_bindings()



    

### -------------------- DRAW MODE --------------------

class draw_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('draw')
    self._moved_atom = None
    self._start_atom = None
    self.submodes = [['30','18','6','1'],
                     ['single','double','triple'],
                     ['normal','wedge','hatch','adder','bbold','dash','dotted'],
                     ['fixed','freestyle'],
                     ['nosimpledouble','simpledouble']]
    self.submodes_names = [[_('30'),_('18'),_('6'),_('1')],
                           [_('single'),_('double'),_('triple')],
                           [_('normal'),_('wedge'),_('hatch'),_('adder'),_('bold'),_('dash'),_('dotted')],
                           [_('fixed length'),_('freestyle')],
                           [_('normal double bonds for wedge/hatch'),_('simple double bonds for wedge/hatch')]]
    self.submode = [0, 0, 0, 0, 1]
    
  def mouse_down( self, event, modifiers = []):
    edit_mode.mouse_down( self, event, modifiers = modifiers)
    Store.app.paper.unselect_all()
    if not self.focused:
      mol = Store.app.paper.new_molecule()
      a = mol.create_new_atom( event.x, event.y)
      a.focus()
      self.focused = a
    #Store.app.paper.add_bindings()


    
  def mouse_up( self, event):
    if not self._dragging:
      self.mouse_click( event)
    else:
      if self._moved_atom:
        Store.app.paper.select( [self._moved_atom])
      deleted, preserved = Store.app.paper.handle_overlap() # should be done before repositioning for ring closure to take effect
      # repositioning of double bonds

      for vrx in preserved + [self._start_atom]:
        if vrx:
          # at first atom text
          if hasattr( vrx, 'update_after_valency_change'):
            vrx.update_after_valency_change()
          # warn when valency is exceeded
          if vrx.free_valency < 0:
            Store.log( _("maximum valency exceeded!"), message_type="warning")
          # adding more than one bond to group
          if isinstance( vrx, group):
            # we need to change the class of the vertex
            a = vrx
            m = a.molecule
            v = m.create_vertex_according_to_text( None, a.xml_ftext, interpret=0)
            a.copy_settings( v)
            a.molecule.replace_vertices( a, v)
            a.delete()
            v.draw()
            Store.log( _("Groups could have valency of 1 only! It was transformed to text!"), message_type="warning")

          self.reposition_bonds_around_atom( vrx)

      self._dragging = 0
      self._start_atom = None
      self._moved_atom = None
      Store.app.paper.add_bindings()
      Store.app.paper.start_new_undo_record()



  def mouse_click( self, event):
    if not self.focused:
      #print "it should not get here!!!"
      mol = Store.app.paper.new_molecule()
      a = mol.create_new_atom( event.x, event.y)
      Store.app.paper.add_bindings()
      b = bond( standard = Store.app.paper.standard,
                type=self.__mode_to_bond_type(),
                order=self.__mode_to_bond_order(),
                simple_double=self.submode[4])
      Store.app.paper.select( [mol.add_atom_to( a, bond_to_use=b)[0]])
      self.focused = a
    else:
      if isinstance( self.focused, oasa.graph.vertex):
        b = bond( standard = Store.app.paper.standard,
                  type=self.__mode_to_bond_type(),
                  order=self.__mode_to_bond_order(),
                  simple_double=self.submode[4])
        a, b = self.focused.molecule.add_atom_to( self.focused, bond_to_use=b)
        # update atom text
        if hasattr( self.focused, 'update_after_valency_change'):
          self.focused.update_after_valency_change()
          self.reposition_bonds_around_atom(self.focused)
        # warn when valency is exceeded
        if self.focused.free_valency < 0:
          Store.log( _("maximum valency exceeded!"), message_type="warning")
        # adding more than one bond to group
        if isinstance( self.focused, group):
          # we need to change the class of the vertex
          a = self.focused
          m = a.molecule
          v = m.create_vertex_according_to_text( None, a.xml_ftext, interpret=0)
          a.copy_settings( v)
          a.molecule.replace_vertices( a, v)
          a.delete()
          v.draw()
          v.focus()
          self.focused = v
          Store.log( _("Groups could have valency of 1 only! It was transformed to text!"), message_type="warning")
        # repositioning of double bonds
        self.reposition_bonds_around_bond( b)
        Store.app.paper.select( [a])
      elif isinstance( self.focused, bond):
        if self._shift:
          self.focused.toggle_type( only_shift = 1, to_type=self.__mode_to_bond_type(),
                                    to_order=self.__mode_to_bond_order(),
                                    simple_double = self.submode[4])
          self.focused.focus() # refocus
        else:
          self.focused.toggle_type( to_type=self.__mode_to_bond_type(),
                                    to_order=self.__mode_to_bond_order(),
                                    simple_double = self.submode[4])
          # update the atoms
          [a.redraw() for a in self.focused.atoms]
          # warn when valency is exceeded
          if self.focused.atom1.free_valency < 0 or self.focused.atom2.free_valency < 0:
            Store.log( _("maximum valency exceeded!"), message_type="warning")
          else:
            self.focused.focus() # refocus

    Store.app.paper.handle_overlap()
    Store.app.paper.start_new_undo_record()
    Store.app.paper.add_bindings()




  def mouse_drag( self, event):
    if not self._dragging:
      self._dragging = 1
      if self.focused and isinstance( self.focused, oasa.graph.vertex):
        self._start_atom = self.focused
        b = bond( standard = Store.app.paper.standard,
                  type=self.__mode_to_bond_type(),
                  order=self.__mode_to_bond_order(),
                  simple_double=self.submode[4])
        if self.submode[3] == 1:
          self._moved_atom, self._bonds_to_update = self.focused.molecule.add_atom_to( self.focused,
                                                                                       bond_to_use=b,
                                                                                       pos=(event.x, event.y))
        else:
          self._moved_atom, self._bonds_to_update = self.focused.molecule.add_atom_to( self.focused,
                                                                                       bond_to_use=b)

        # deactivate the new atom and bond for focus
        Store.app.paper._do_not_focus = [self._moved_atom, b]

        # update atom text
        if hasattr( self.focused, 'update_after_valency_change'):
          self.focused.update_after_valency_change()

        #Store.app.paper.add_bindings( active_names=('atom',))


    if self._start_atom:
      z = 0
      if self.focused and self.focused != self._start_atom and isinstance( self.focused, oasa.graph.vertex):
        x, y = self.focused.get_xy()
        z = self.focused.z
      elif self.submode[3] == 1:
        x, y = event.x, event.y
      else:
        dx = event.x - self._startx
        dy = event.y - self._starty
        x0, y0 = self._start_atom.get_xy()
        x,y = geometry.point_on_circle( x0, y0, Screen.any_to_px( Store.app.paper.standard.bond_length),
                                        direction = (dx, dy),
                                        resolution = int( self.submodes[0][ self.submode[ 0]]))
      self._moved_atom.move_to( x, y)
      # to be able to connect atoms with non-zero z coordinate
      if z != 0:
        self._moved_atom.z = z
      self._bonds_to_update.redraw()

  def enter_object( self, object, event):
    if self.focused:
      self.focused.unfocus()
    self.focused = object
    self.focused.focus()

      
  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    else:
      pass #warn( "leaving NONE", UserWarning, 2)

  def __mode_to_bond_type( self):
    """maps bond type submode to bond_type"""
    type = self.get_submode( 2)
    if type == 'dotted':
      return "o"
    else:
      return type[0]


  def __mode_to_bond_order( self):
    order = self.submode[1]+1
    return order




## -------------------- ARROW MODE --------------------

class arrow_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('arrow')
    self._start_point = None
    self._moved_point = None
    self._arrow_to_update = None
    self.submodes = [['30','18','6','1'],['fixed','freestyle'],['anormal','spline'],arrow.available_types]
    self.submodes_names = [[_('30'),_('18'),_('6'),_('1')], [_('fixed length'),_('freestyle')],
                           [_('normal'),_('spline')],arrow.available_type_names]
    self.submode = [0, 0, 0, 0]
    self.__nothing_special = 0 # to easy determine whether new undo record should be started

  def mouse_down( self, event, modifiers = []):
    edit_mode.mouse_down( self, event, modifiers = modifiers)
    Store.app.paper.unselect_all()
    if not self.focused:
      spline = (self.get_submode( 2) == 'spline')
      type = self.get_submode( 3)
      arr = Store.app.paper.new_arrow( spline=spline, type=type)
      self._start_point = arr.create_new_point( event.x, event.y)
      self._start_point.focus()
      self.focused = self._start_point
      self._arrow_to_update = arr
      #arr.draw()
    elif self.focused.object_type == 'point' and self.focused.arrow.object_type == 'arrow':
      self._start_point = self.focused
      self._arrow_to_update = self._start_point.arrow
    elif self.focused.object_type == 'arrow':
      self._arrow_to_update = self.focused
      self._start_point = None
    else:
      self.__nothing_special = 1
    self._block_leave_event = 0
    Store.app.paper.add_bindings()

  def mouse_drag( self, event):
    if self._start_point:
      if not self._dragging:
        self._dragging = 1
        # update the spline-notspline in case it differs from the set submode
        spline = (self.get_submode( 2) == 'spline')
        if self._arrow_to_update.spline != spline:
          self._arrow_to_update.spline = spline
        if self._start_point == self._arrow_to_update.points[-1]:
          pos = -1
        else:
          pos = self._arrow_to_update.points.index( self._start_point)
        self._moved_point = self._start_point.arrow.create_new_point( event.x, event.y, position=pos)
      if self.submode[1] == 1:
        x, y = event.x, event.y
      else:
        dx = event.x - self._startx
        dy = event.y - self._starty
        x0, y0 = self._start_point.get_xy()
        x,y = geometry.point_on_circle( x0, y0,
                                        Screen.any_to_px( Store.app.paper.standard.arrow_length),
                                        direction = (dx, dy),
                                        resolution = int( self.submodes[0][ self.submode[ 0]]))
      self._moved_point.move_to( x, y)
      self._arrow_to_update.redraw()

  def mouse_up( self, event):
    if not self._dragging:
      # update the spline-notspline in case it differs from the set submode
      spline = (self.get_submode( 2) == 'spline')
      if self._arrow_to_update and self._arrow_to_update.spline != spline:
        self._arrow_to_update.spline = spline
        self._arrow_to_update.redraw()
      # change the arrow direction only if the spline was not changed
      elif self._arrow_to_update and not self._start_point:
        self._arrow_to_update.change_direction()
      # add point
      elif self._arrow_to_update:
        x0, y0 = self._start_point.get_xy()
        if self._start_point == self._arrow_to_update.points[-1]:
          pos = -1
        else:
          pos = self._arrow_to_update.points.index( self._start_point)
        pnt = self._arrow_to_update.create_new_point( x0+Screen.any_to_px( Store.app.paper.standard.arrow_length),
                                                      y0, position=pos)
        Store.app.paper.select( [pnt])
        self._arrow_to_update.redraw()
      #self.mouse_click( event)
    else:
      if self._moved_point:
        Store.app.paper.select( [self._moved_point])
      self._dragging = 0
    self._start_point = None
    self._moved_point = None
    self._arrow_to_update = None
    if self.__nothing_special:
      self.__nothing_special = 0
    else:
      Store.app.paper.start_new_undo_record()
    Store.app.paper.add_bindings()

  def mouse_click( self, event):
    pass

  def enter_object( self, object, event):
    if self.focused:
      self.focused.unfocus()
    self.focused = object
    if self.focused.object_type == 'selection_rect':
      self.focused.focus( item= Store.app.paper.find_withtag( 'current')[0])
    else:
      self.focused.focus()


  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    else:
      warn( "leaving NONE", UserWarning, 2)



class plus_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('plus')
    self._start_point = None
    self._moved_point = None

  def mouse_down( self, event, modifiers = []):
    edit_mode.mouse_down( self, event, modifiers = modifiers)
    Store.app.paper.unselect_all()

  def mouse_drag( self, event):
    if not self._dragging:
      self._dragging = 1

  def mouse_up( self, event):
    if not self._dragging:
      self.mouse_click( event)
    self._dragging = 0

  def mouse_click( self, event):
    if not self.focused:
      pl = Store.app.paper.new_plus( event.x, event.y)
      Store.app.paper.select( [pl])
    else:
      pass
    Store.app.paper.start_new_undo_record()
    Store.app.paper.add_bindings()

  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    else:
      warn( "leaving NONE", UserWarning, 2)



## -------------------- TEMPLATE MODE --------------------

class template_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('template')
    template_names = Store.tm.get_template_names()
    # Handle case where no templates are loaded
    if not template_names:
      template_names = ['none']
    self.submodes = [template_names]
    self.submodes_names = [template_names]
    self.submode = [0]
    self.register_key_sequence( 'C-t', self._mark_focused_as_template_atom_or_bond)
    self._user_selected_template = ''
    self.template_manager = Store.tm
    
  def mouse_click( self, event):
    if self.submodes == [[]]:
      Store.log( _("No template is available"))
      return 
    Store.app.paper.unselect_all()
    if not self.focused:
      t = self._get_transformed_template( self.submode[0], (event.x, event.y), type='empty', paper=Store.app.paper)
    else:
      if isinstance( self.focused, oasa.graph.vertex):
        if self.focused.z != 0:
          Store.log( _("Sorry, it is not possible to append a template to an atom with non-zero Z coordinate, yet."),
                        message_type="hint")
          return
        if self.focused.free_valency >= self._get_templates_valency():
          x1, y1 = self.focused.neighbors[0].get_xy()
          x2, y2 = self.focused.get_xy()
          t = self._get_transformed_template( self.submode[0], (x1,y1,x2,y2), type='atom1', paper=Store.app.paper)
        else:
          x1, y1 = self.focused.get_xy()
          x2, y2 = self.focused.molecule.find_place( self.focused, Screen.any_to_px( Store.app.paper.standard.bond_length))
          t = self._get_transformed_template( self.submode[0], (x1,y1,x2,y2), type='atom2', paper=Store.app.paper)
      elif isinstance( self.focused, bond):
        x1, y1 = self.focused.atom1.get_xy()
        x2, y2 = self.focused.atom2.get_xy()
        #find right side of bond to append template to
        atms = self.focused.atom1.neighbors + self.focused.atom2.neighbors
        atms = misc.difference( atms, [self.focused.atom1, self.focused.atom2])
        coords = [a.get_xy() for a in atms]
        if reduce( operator.add, [geometry.on_which_side_is_point( (x1,y1,x2,y2), xy) for xy in coords], 0) > 0:
          x1, y1, x2, y2 = x2, y2, x1, y1
        t = self._get_transformed_template( self.submode[0], (x1,y1,x2,y2), type='bond', paper=Store.app.paper)
        if not t:
          return # the template was not meant to be added to a bond
      else:
        return
    Store.app.paper.stack.append( t)
    t.draw( automatic="both")
    #Store.app.paper.signal_to_app( ("Added molecule from template: ")+\
    #                              Store.tm.get_template_names()[ self.submode[0]].encode('utf-8'))
    Store.app.paper.select( [o for o in t])
    Store.app.paper.handle_overlap()
    # checking of valency
    if self.focused:
      if isinstance( self.focused, bond) and (self.focused.atom1.free_valency < 0 or self.focused.atom2.free_valency < 0):
        Store.log( _("maximum valency exceeded!"), message_type="warning")
      elif isinstance( self.focused, oasa.graph.vertex) and self.focused.free_valency < 0:
        Store.log( _("maximum valency exceeded!"), message_type="warning")

    Store.app.paper.start_new_undo_record()
    Store.app.paper.add_bindings()





  def _mark_focused_as_template_atom_or_bond( self):
    if self.focused and isinstance( self.focused, oasa.graph.vertex):
      self.focused.molecule.mark_template_atom( self.focused)
      Store.log( _("focused atom marked as 'template atom'")) 
    elif self.focused and isinstance( self.focused, bond):
      self.focused.molecule.mark_template_bond( self.focused)
      Store.log( _("focused bond marked as 'template bond'")) 





  def _get_transformed_template( self, name, coords, type='empty', paper=None):
    return self.template_manager.get_transformed_template( self.submode[0], coords, type=type, paper=paper)



  def _get_templates_valency( self):
    return self.template_manager.get_templates_valency( self.submode[0])



##--------------------TEXT MODE--------------------

class text_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('text')
    self._start_point = None
    self._moved_point = None

  def mouse_down( self, event, modifiers = []):
    edit_mode.mouse_down( self, event, modifiers = modifiers)
    Store.app.paper.unselect_all()

  def mouse_drag( self, event):
    if not self._dragging:
      self._dragging = 1

  def mouse_up( self, event):
    if not self._dragging:
      self.mouse_click( event)
    self._dragging = 0

  def mouse_click( self, event):
    if not self.focused:
      name = Store.app.editPool.activate()
      if not name:
        return
      name = str(name).encode( 'utf-8')
      # there is either something selected or a new thing is added
      # the unselecting code before does ensure that nothing is selected
      # when we click outside to create something new
      Store.app.paper.set_name_to_selected( name)
      if name and not dom_extensions.isOnlyTags( name):
        txt = Store.app.paper.new_text( event.x, event.y, text=name)
        txt.draw()
        Store.app.paper.select( [txt])
        Store.app.paper.add_bindings()
        Store.app.paper.start_new_undo_record()        
    else:
      if self.focused.object_type == 'text':
        Store.app.paper.select( [self.focused])
        name = Store.app.editPool.activate( text = self.focused.xml_ftext)
        if name and not dom_extensions.isOnlyTags( name):
          Store.app.paper.set_name_to_selected( name)
          Store.app.paper.add_bindings()
      elif isinstance( self.focused, oasa.graph.vertex):
        Store.log( _("The text mode can no longer be used to edit atoms, use atom mode."),
                      message_type="warning")


  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    else:
      warn( "leaving NONE", UserWarning, 2)






class rotate_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('rotate')
    self._rotated_mol = None
    self._rotated_atoms = []
    self.submodes = [['2D','3D'],['normal3d','fixsomething']]
    self.submodes_names = [[_('2D'),_('3D')],[_('normal 3D rotation'),_('fix selected bond in 3D')]]
    self.submode = [0,0]
    self._fixed = None


  def mouse_down( self, event, modifiers = []):
    edit_mode.mouse_down( self, event, modifiers = modifiers)
    # blocking is not necessary in rotate mode
    self._block_leave_event = 0
    self._fixed = None
    self._rotated_atoms = []
    if self.get_submode(0) == "3D" and self.get_submode(1) == "fixsomething":
      if len( Store.app.paper.selected) == 1:
        sel = Store.app.paper.selected[0]
        if isinstance( sel, bond):
          self._fixed = sel
        else:
          Store.log( _("The selected item must be a bond."), message_type="warning")
      else:
        Store.log( _("Exactly one item should be selected to fixed rotation to work, normal rotation will be used."), message_type="hint")
    Store.app.paper.unselect_all()
    if self.focused and (isinstance( self.focused, oasa.graph.vertex) or isinstance(self.focused, bond)):
      self._rotated_mol = self.focused.molecule
      if self._fixed:
        # 3D rotation around a bond
        self._rotated_atoms = self._get_objs_to_rotate()
      x1, y1, x2, y2 = Store.app.paper.list_bbox( [o.item for o in self._rotated_mol.atoms])
      self._centerx = x1+(x2-x1)/2.0
      self._centery = y1+(y2-y1)/2.0
    elif self.focused and self.get_submode(0) == '2D' and (isinstance( self.focused, arrow) or (hasattr( self.focused, 'arrow') and isinstance( self.focused.arrow, arrow))):
      if isinstance( self.focused, arrow):
        self._rotated_mol = self.focused
      else:
        self._rotated_mol = self.focused.arrow
      x1, y1, x2, y2 = self._rotated_mol.bbox()
      self._centerx = x1+(x2-x1)/2.0
      self._centery = y1+(y2-y1)/2.0
    elif self.focused:
      if self.get_submode(0) == '3D':
        tkMessageBox.showerror( _("You can only rotate molecules in 3D!"), _("Sorry but you can only rotate molecules in 3D."))
      else:
        tkMessageBox.showerror( _("You can only rotate molecules and arrows in 2D!"), _("Sorry but you can only rotate molecules and arrows in 2D."))

    
  def mouse_up( self, event):
    if not self._dragging:
      self.mouse_click( event)
    else:
      self._dragging = 0
      self._moved_atom = None
      if self._rotated_mol:
        if self.get_submode( 0) == '3D':
          [b.redraw( recalc_side=1) for b in self._rotated_mol.bonds]
          [a.reposition_marks() for a in self._rotated_mol.atoms]
        self._rotated_mol = None
        Store.app.paper.start_new_undo_record()
      if self._fixed:
        Store.app.paper.select( [self._fixed])
    Store.app.paper.add_bindings()

  def mouse_drag( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    if not self._dragging:
      self._dragging = 1
    if self._rotated_mol:
      dx0 = event.x - self._centerx
      dy0 = event.y - self._centery
      dx1 = event.x - self._startx
      dy1 = event.y - self._starty
      sig = -geometry.on_which_side_is_point( (self._centerx, self._centery, self._startx, self._starty), (event.x, event.y))
      self._startx, self._starty = event.x, event.y
      if self.submode[0] == 0:
        # 2D rotation
        angle = round( sig * (abs( dx1) +abs( dy1)) / 50.0, 2)
        tr = transform()
        tr.set_move( -self._centerx, -self._centery)
        tr.set_rotation( angle)
        tr.set_move( self._centerx, self._centery)
        self._rotated_mol.transform( tr)
      else:
        # 3D rotation
        if self.get_submode(1) == "fixsomething" and self._fixed and isinstance( self._fixed, bond):
          # we have a fixed part
          if self._fixed.molecule != self._rotated_mol:
            Store.log( _("You can only rotate the molecule for which you fixed a bond."), message_type="error")
            return 
          sig = abs(dx1) > abs(dy1) and misc.signum(dx1) or misc.signum(dy1)
          angle = round( sig * math.sqrt(dx1**2 +dy1**2) / 50.0, 3)
          t = geometry.create_transformation_to_rotate_around_particular_axis( self._fixed.atom2.get_xyz(), self._fixed.atom1.get_xyz(), angle)
          for a in self._rotated_atoms:
            x, y, z = a.x, a.y, a.z
            x, y, z = t.transform_xyz( x, y, z)
            a.move_to( x, y)
            a.z = z
          for a in self._rotated_mol.bonds:
            a.simple_redraw()
        else:
          # normal rotation
          angle1 = round( dx1 / 50.0, 2)
          angle2 = round( dy1 / 50.0, 2)
          tr = transform3d()
          tr.set_move( -self._centerx, -self._centery, 0)
          tr.set_rotation( -angle2, angle1, 0)
          tr.set_move( self._centerx, self._centery, 0)
          for a in self._rotated_mol.atoms:
            x, y, z = a.x, a.y, a.z
            x, y, z = tr.transform_xyz( x, y, z)
            a.move_to( x, y)
            a.z = z
          for a in self._rotated_mol.bonds:
            a.simple_redraw()

  def mouse_click( self, event):
    edit_mode.mouse_click( self, event)

  def _get_objs_to_rotate( self):
    if not self._shift:
      return self._fixed.molecule.atoms
    b = self._fixed
    mol = b.molecule
    mol.temporarily_disconnect_edge( b)
    cc = list( mol.get_connected_components())
    mol.reconnect_temporarily_disconnected_edge( b)
    if len( cc) == 1:
      return cc[0]
    else:
      if isinstance( self.focused, oasa.graph.vertex):
        to_use = self.focused in cc[0] and cc[0] or cc[1]
      elif isinstance( self.focused, bond):
        if self.focused in mol.vertex_subgraph_to_edge_subgraph( cc[0]):
          to_use = cc[0]
        else:
          to_use = cc[1]
      else:
        assert isinstance( self.focused, oasa.graph.vertex) or isinstance( self.focused, bond)
      return to_use


class bond_align_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('transformation mode')
    self._rotated_mol = None
    self.first_atom_selected = None
    self.submodes = [['tohoriz','tovert','invertthrough','mirrorthrough','freerotation']]
    self.submodes_names = [[_('horizontal align'),_('vertical align'),_('invert through a point'),_('mirror through a line'),_("free rotation around bond")]]
    self.submode = [0]
    self._needs_two_atoms = [1,1,0,1,-1]  #-1 is for those that accept only bonds

  def mouse_down( self, event, modifiers = []):
    if not self.focused:
      return
    if not misc.isinstance_of_one( self.focused, (oasa.graph.vertex, bond)):
      return
    if self._needs_two_atoms[ self.submode[0]] == -1 and isinstance( self.focused, oasa.graph.vertex):
      return
    # edit_mode.mouse_down( self, event, modifiers = modifiers)
    self._block_leave_event = 0
    if not self.first_atom_selected:
      Store.app.paper.unselect_all()
    if isinstance(self.focused, bond):
      if self.first_atom_selected:
        # waiting for second atom selection, clicking bond does nothing
        Store.log( _("select the second atom, please."), message_type="hint")
        return
      self._rotated_mol = self.focused.molecule
      x1, y1 = self.focused.atom1.get_xy()
      x2, y2 = self.focused.atom2.get_xy()
      coords = (x1,y1,x2,y2)
      objects = [self.focused]
    elif isinstance( self.focused, oasa.graph.vertex):
      if not self.first_atom_selected: # first atom picked
        if self._needs_two_atoms[ self.submode[0]] > 0:
          self.first_atom_selected = self.focused
          self.first_atom_selected.select()
          Store.app.paper.add_bindings()
          self._rotated_mol = self.focused.molecule
          return
        else:
          self._rotated_mol = self.focused.molecule
          coords = self.focused.get_xy()
          objects = [self.focused]
      else: # second atom picked
        if self.focused.molecule != self.first_atom_selected.molecule:
          Store.log( _("atoms must be in the same molecule!"), message_type="hint")
          return
        if self.focused == self.first_atom_selected:
          Store.log( _("atoms must be different!"), message_type="hint")
          return
        x1, y1 = self.first_atom_selected.get_xy()
        x2, y2 = self.focused.get_xy()
        coords = (x1,y1,x2,y2)
        objects = [self.focused, self.first_atom_selected]
        self.first_atom_selected.unselect()
        self.first_atom_selected = None
    tr = self.__class__.__dict__['_transform_'+self.get_submode(0)]( self, coords)
    if hasattr( self, '_apply_to_'+self.get_submode(0)):
      apply_to = self.__class__.__dict__['_apply_to_'+self.get_submode(0)]( self)
      if apply_to == None:
        return 
      [o.transform( tr) for o in apply_to]
    else:
      self._rotated_mol.transform( tr)
    self._rotated_mol = None
    Store.app.paper.start_new_undo_record()
    Store.app.paper.add_bindings()

#    if self.focused:
#      self.focused.unfocus()
#      self.focused = None


  def _transform_tohoriz( self, coords):
    x1, y1, x2, y2 = coords
    centerx = ( x1 + x2) / 2
    centery = ( y1 + y2) / 2
    angle0 = geometry.clockwise_angle_from_east( x2 - x1, y2 - y1)
    if angle0 >= math.pi :
      angle0 = angle0 - math.pi
    if (angle0 > -0.005) and (angle0 < .005) :
    # if angle0 == 0  :
      # bond is already horizontal => horizontal "flip"
      angle = math.pi
    elif angle0 <= math.pi/2:
      angle = -angle0
    else: # pi/2 < angle < pi
      angle = math.pi - angle0
    tr = transform()
    tr.set_move( -centerx, -centery)
    tr.set_rotation( angle)
    tr.set_move(centerx, centery)
    return tr
      

  def _transform_tovert( self, coords):
    x1, y1, x2, y2 = coords
    centerx = ( x1 + x2) / 2
    centery = ( y1 + y2) / 2
    angle0 = geometry.clockwise_angle_from_east( x2 - x1, y2 - y1)
    if angle0 >= math.pi :
      angle0 = angle0 - math.pi
    if (angle0 > math.pi/2 - .005) and (angle0 < math.pi/2 + 0.005):
    # if angle0 == math.pi/2:
      # bond is already vertical => vertical "flip"
      angle = math.pi
    else:
      angle = math.pi/2 - angle0
    tr = transform()
    tr.set_move( -centerx, -centery)
    tr.set_rotation( angle)
    tr.set_move(centerx, centery)
    return tr

  def _transform_invertthrough( self, coords):
    if len( coords) == 4:
      x1, y1, x2, y2 = coords      
      x = ( x1 +x2) /2.0
      y = ( y1 +y2) /2.0
    else:
      x, y = coords
    tr = transform()
    tr.set_move( -x, -y)
    tr.set_scaling_xy( -1, -1)
    tr.set_move( x, y)
    return tr

  def _transform_mirrorthrough( self, coords):
    x1, y1, x2, y2 = coords
    centerx = ( x1 + x2) / 2
    centery = ( y1 + y2) / 2
    angle0 = geometry.clockwise_angle_from_east( x2 - x1, y2 - y1)
    if angle0 >= math.pi :
      angle0 = angle0 - math.pi
    tr = transform()
    tr.set_move( -centerx, -centery)
    tr.set_rotation( -angle0)
    tr.set_scaling_xy( 1, -1)
    tr.set_rotation( angle0)
    tr.set_move(centerx, centery)
    return tr

  def _transform_freerotation( self, coords):
    return self._transform_mirrorthrough( coords)


  def _apply_to_freerotation( self):
    assert isinstance( self.focused, bond)
    b = self.focused
    mol = b.molecule
    mol.delete_bond( b)
    cc = list( mol.get_connected_components())
    mol.add_edge( b.atom1, b.atom2, b)
    b.draw()
    b.focus()
    if len( cc) == 1:
      Store.log( _("Bond is part of a ring, there is no possiblity for rotation!"),
                    message_type="hint")
      return None
    else:
      to_use = list( len( cc[0]) < len( cc[1]) and cc[0] or cc[1])
      return to_use + [b for b in mol.bonds if b.atom1 in to_use and b.atom2 in to_use]


  def cleanup( self):
    edit_mode.cleanup( self)
    if self.first_atom_selected:
      self.first_atom_selected.unselect()
      self.first_atom_selected = None


  def mouse_click( self, event):
    pass

  def mouse_up( self, event):
    pass

  def mouse_drag( self, event):
    pass





class vector_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('vector graphics')
    self.submodes = [['rectangle','square','oval', 'circle', 'polygon', 'polyline']]
    self.submodes_names = [[_('rectangle'),_('square'),_('oval'),_('circle'),_('polygon'),_('polyline')]]
    self.submode = [0]
    self._polygon_points = []
    self._polygon_line = None
    self._current_obj = None

  def mouse_down( self, event, modifiers=[]):
    edit_mode.mouse_down( self, event)
    if self.get_submode(0) in ("polyline","polygon"):
      Store.app.paper.unselect_all()
      self._block_leave_event = 0
      self._polygon_points += [event.x, event.y]


  def mouse_drag( self, event):
    if self.get_submode(0) in ("polyline","polygon"):
      self.mouse_move( event)
      return
    if not self.focused and not self._dragging:
      self._dragging = 5
      Store.app.paper.unselect_all()
      if self.get_submode( 0) == "rectangle":
        self._current_obj = Store.app.paper.new_rect( (self._startx, self._starty, event.x, event.y))
      elif self.get_submode( 0) == "square":
        self._current_obj = Store.app.paper.new_square( (self._startx, self._starty, event.x, event.y))
      elif self.get_submode( 0) == "oval":
        self._current_obj = Store.app.paper.new_oval( (self._startx, self._starty, event.x, event.y))
      elif self.get_submode( 0) == "circle":
        self._current_obj = Store.app.paper.new_circle( (self._startx, self._starty, event.x, event.y))
      self._current_obj.draw()
    elif not self.focused and self._dragging and self._current_obj:
      self._current_obj.resize( (self._startx, self._starty, event.x, event.y), fix=( self._startx, self._starty))
      Store.log( '%i, %i' % ( abs( self._startx-event.x), abs( self._starty-event.y)))
    elif self.focused or self._dragging in (1,2):
      edit_mode.mouse_drag( self, event)

  def mouse_up( self, event):
    if self.get_submode( 0) in ("polyline","polygon"):
      if not self._polygon_line:
        self._polygon_line = Store.app.paper.create_line( tuple( self._polygon_points + [event.x, event.y]), fill='black')
      else:
        Store.app.paper.coords( self._polygon_line, tuple( self._polygon_points + [event.x, event.y]))
      return
    self._block_leave_event = 0
    if self._dragging == 5:
      self._dragging = 0
      if self._current_obj:
        if self._current_obj.object_type != 'selection_rect':
          Store.app.paper.select( [self._current_obj])
        self._current_obj = None
      Store.app.paper.start_new_undo_record()
      Store.app.paper.add_bindings()
    elif self._dragging:
      edit_mode.mouse_up( self, event)
    else:
      self.mouse_click( event)

  def mouse_down3( self, event, modifiers = []):
    if self._polygon_line:
      Store.app.paper.delete( self._polygon_line)
      poly = None
      if self.get_submode( 0) == "polygon":
        if len( self._polygon_points) > 2:
          poly = Store.app.paper.new_polygon( tuple( self._polygon_points + [event.x, event.y]))
      elif self.get_submode( 0) == "polyline":
        poly = Store.app.paper.new_polyline( tuple( self._polygon_points + [event.x, event.y]))
      if poly:
        poly.draw()
        Store.app.paper.select( [poly])
      self._polygon_points = []
      self._polygon_line = None
      Store.app.paper.start_new_undo_record()
      Store.app.paper.add_bindings()
    else:
      edit_mode.mouse_down3( self, event, modifiers=modifiers)

  def mouse_move( self, event):
    if self.get_submode( 0) in ("polyline","polygon") and self._polygon_points:
      if not self._polygon_line:
        self._polygon_line = Store.app.paper.create_line( tuple( self._polygon_points + [event.x, event.y]), fill='black')
      else:
        Store.app.paper.coords( self._polygon_line, tuple( self._polygon_points + [event.x, event.y]))





## -------------------- MARK MODE --------------------    

class mark_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('mark')
    self.submodes = [['radical','biradical','electronpair','dottedelectronpair','plusincircle','minusincircle','pzorbital'],
                     ['add','remove']]
    self.submodes_names = [[_('radical'), _('biradical'), _('electron pair'), _('dotted electron pair'),
                            _('plus'), _('minus'), _('pz orbital')],
                           [_('add'), _('remove')]]
    self.submode = [0, 0]

    self.register_key_sequence( 'Up', lambda : self._move_mark_for_selected( 0, -1), use_warning=0)
    self.register_key_sequence( 'Down', lambda : self._move_mark_for_selected( 0, 1), use_warning=0)
    self.register_key_sequence( 'Left', lambda : self._move_mark_for_selected( -1, 0), use_warning=0)
    self.register_key_sequence( 'Right', lambda : self._move_mark_for_selected( 1, 0), use_warning=0)

    self.rectangle_selection = False


  def mouse_click( self, event):
    mark_name = self.get_submode( 0)
    recode = {'dottedelectronpair':'dotted_electronpair',
              'plusincircle'      :'plus',
              'minusincircle'     :'minus',
              'pzorbital'         :'pz_orbital'}
    if mark_name in recode:
      mark_name = recode[ mark_name]
    if self.get_submode( 1) == 'add':
      # we are adding a mark
      if self.focused and (isinstance( self.focused, special_parents.drawable_chem_vertex)):
        try:
          m = self.focused.set_mark( mark=mark_name)
        except ValueError:
          Store.log( _("This mark type is not allowed for this object"))
          return
        if m:
          m.register()
        if (self.focused.show_hydrogens and self.focused.show) and not isinstance( self.focused, textatom):
          self.focused.redraw()
        Store.app.paper.start_new_undo_record()

    elif self.get_submode( 1) == 'remove':
      # we are removing a mark
      if self.focused:
        if isinstance( self.focused, atom) or isinstance( self.focused, textatom):
          # we do it by name
          m = self.focused.remove_mark( mark_name)
          if not m:
            Store.log( _("There are no marks of type %s on the focused atom") % mark_name, message_type="warning")
          else:
            if (self.focused.show_hydrogens and self.focused.show) and not isinstance( self.focused, textatom):
              self.focused.redraw()
            Store.app.paper.start_new_undo_record()
        elif isinstance( self.focused, marks.mark):
          # we do it by reference
          m = self.focused.atom.remove_mark( self.focused)
          if (self.focused.atom.show_hydrogens and self.focused.atom.show) and not isinstance( self.focused, textatom):
            self.focused.atom.redraw()
          self.focused = None
          Store.app.paper.start_new_undo_record()

    Store.app.paper.add_bindings()



  def mouse_down3( self, event, modifiers = []):
    if self.focused and isinstance( self.focused, marks.mark):
      dialog = context_menu( [self.focused])
      dialog.post( event.x_root, event.y_root)
      if dialog.changes_made:
        Store.app.paper.start_new_undo_record()


  def mouse_drag( self, event):
    # this is here because the pz_orbital is rotated instead of moved when dragging,
    # therefor we need to use the move_to to position the mark
    # "pivot point" under the cursor when drags begins
    if not self._dragging and self.focused and self.focused.object_type == "mark" and self.focused.__class__.__name__ == "pz_orbital":
      self.focused.move_to( event.x, event.y)
    edit_mode.mouse_drag( self, event)



  def _move_mark_for_selected( self, dx, dy):
    to_move = [a for a in Store.app.paper.selected if isinstance( a, oasa.graph.vertex)]
    
    for a in to_move:
      for m in a.marks:
        m.move( dx, dy)

    if Store.app.paper.um.get_last_record_name() == "arrow-key-move":
      Store.app.paper.um.delete_last_record()
    Store.app.paper.start_new_undo_record( name="arrow-key-move")


  def startup( self):
    self._register_all_marks( Store.app.paper)
    Store.app.paper.remove_bindings()
    Store.app.paper.add_bindings( active_names=("mark","atom"))



  def cleanup( self, paper=None):
    edit_mode.cleanup( self, paper=paper)
    pap = paper or Store.app.paper
    self._unregister_all_marks( pap)
    pap.remove_bindings()
    pap.add_bindings()


  def _register_all_marks( self, paper):
    [i.register() for i in self._all_marks( paper)]

  def _unregister_all_marks( self, paper):
    [i.unregister() for i in self._all_marks( paper)]    

  def _all_marks( self, paper):
    for m in paper.molecules:
      for a in m.atoms:
        if hasattr( a, 'marks'):
          for mark in a.marks:
            yield mark


  def on_paper_switch( self, old, new):
    self.cleanup( old)
    self.startup()




## -------------------- ATOM MODE --------------------

class atom_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('atom')
    self._start_point = None
    self._moved_point = None

  def mouse_down( self, event, modifiers = []):
    edit_mode.mouse_down( self, event, modifiers = modifiers)
    Store.app.paper.unselect_all()

  def mouse_drag( self, event):
    if not self._dragging:
      self._dragging = 1

  def mouse_up( self, event):
    if not self._dragging:
      self.mouse_click( event)
    self._dragging = 0

  def mouse_click( self, event):
    if not self.focused:
      name = Store.app.editPool.activate()
      if not name:
        return
      name = str(name).encode( 'utf-8')
      if name and not dom_extensions.isOnlyTags( name):
        mol = Store.app.paper.new_molecule()
        a = mol.create_vertex_according_to_text( None, name, interpret=Store.app.editPool.interpret)
        a.x = event.x
        a.y = event.y
        mol.insert_atom( a)
        a.draw()
        interactors.log_atom_type( a.__class__.__name__)
        Store.app.paper.select( [a])
        Store.app.paper.add_bindings()
        Store.app.paper.start_new_undo_record()        
    else:
      if isinstance( self.focused, oasa.graph.vertex):
        a = self.focused
        name = Store.app.editPool.activate( text = a.symbol)
        if name and not dom_extensions.isOnlyTags( name):
          # we need to change the class of the vertex
          v = a.molecule.create_vertex_according_to_text( a, name, interpret=Store.app.editPool.interpret)
          a.copy_settings( v)
          a.molecule.replace_vertices( a, v)
          a.delete()
          v.draw()
          Store.app.paper.select( [v])
          interactors.log_atom_type( v.__class__.__name__)

          # cleanup
          [self.reposition_bonds_around_bond( o) for o in Store.app.paper.bonds_to_update()]
          [self.reposition_bonds_around_atom( o) for o in Store.app.paper.selected if o.object_type == "atom"]

          Store.app.paper.start_new_undo_record()        
          Store.app.paper.add_bindings()



  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    else:
      warn( "leaving NONE", UserWarning, 2)





## -------------------- REACTION MODE --------------------

class reaction_mode( basic_mode):

  def __init__( self):
    basic_mode.__init__( self)
    self.name = _('reaction')
    self.submodes = [['reactant','rplus','rarrow','condition','product']]
    self.submodes_names = [[_('reactant'),_('plus'),_('arrow'),_('condition'),_('product')]]
    self.submode = [0]
    self.focused = None
    self._items = []
    self.arrow = None


  def mouse_down( self, event, modifiers=[]):
    if self.focused:
      if not self.arrow:
        tkMessageBox.showerror( _("No arrow present"),
                                _("""The reaction information in BKChem are associated with arrows, therefore you have to have at least one arrow before you can construct any reaction."""))
        return

      sm = self.get_submode(0)
      if sm == 'reactant':
        m = self.focused.molecule
        if m not in self.arrow.reaction.reactants:
          self.arrow.reaction.reactants.append( m)
          # remove it from products
          if m in self.arrow.reaction.products:
            self.arrow.reaction.products.remove( m)
        else:
          self.arrow.reaction.reactants.remove( m)
      elif sm == 'product':
        m = self.focused.molecule
        if m not in self.arrow.reaction.products:
          self.arrow.reaction.products.append( m)
          # remove it from reactants
          if m in self.arrow.reaction.reactants:
            self.arrow.reaction.reactants.remove( m)
        else:
          self.arrow.reaction.products.remove( m)
      elif sm == 'rarrow':
        if self.focused.object_type == 'point' and self.focused.arrow.object_type == 'arrow':
          self.arrow = self.focused.arrow
        elif self.focused.object_type == 'arrow':
          self.arrow = self.focused
      elif sm == 'condition':
        if self.focused not in self.arrow.reaction.conditions:
          self.arrow.reaction.conditions.append( self.focused)
        else:
          self.arrow.reaction.conditions.remove( self.focused)
      elif sm == 'rplus':
        if self.focused not in self.arrow.reaction.pluses:
          self.arrow.reaction.pluses.append( self.focused)
        else:
          self.arrow.reaction.pluses.remove( self.focused)
          
      self._mark_reaction()
      


  def _mark_reaction( self):
    for i in self._items:
      Store.app.paper.delete( i)
    self._items = []
    width = 3
    
    self._items.append( Store.app.paper.create_rectangle( self.arrow.bbox(), fill='', outline='blue', width=width))
    
    for m in self.arrow.reaction.reactants:
      self._items.append( Store.app.paper.create_rectangle( m.bbox(), outline='green', width=width))
    for m in self.arrow.reaction.products:
      self._items.append( Store.app.paper.create_rectangle( m.bbox(), outline='red', width=width))
    for m in self.arrow.reaction.conditions:
      self._items.append( Store.app.paper.create_rectangle( m.bbox(), outline='cyan', width=width))
    for m in self.arrow.reaction.pluses:
      self._items.append( Store.app.paper.create_rectangle( m.bbox(), outline='orange', width=width))

    #self._add_bindings_according_to_submode()


  def _add_bindings_according_to_submode( self):
    name = self.get_submode(0)
    if name == 'reactant' or name == 'product':
      Store.app.paper.add_bindings( active_names=('atom','bond'))
    elif name == 'rarrow':
      Store.app.paper.add_bindings( active_names=('arrow','point'))
    elif name == 'rplus':
      Store.app.paper.add_bindings( active_names=('plus',))
    elif name == 'condition':
      Store.app.paper.add_bindings( active_names=('text',))
    


  def on_submode_switch( self, submode_index, name=''):
    Store.app.paper.remove_bindings()
    self._add_bindings_according_to_submode()


  def startup( self):
    Store.app.paper.unselect_all()
    arrows = Store.app.paper.arrows
    if arrows:
      self.arrow = arrows[0]
    else:
      self.arrow = None
    if self.arrow:
      self._mark_reaction()


  def cleanup( self, paper=None):
    basic_mode.cleanup( self, paper=paper)
    pap = paper or Store.app.paper
    for i in self._items:
      pap.delete( i)
    self._items = []
    pap.add_bindings()


  def on_paper_switch( self, old_paper, new_paper):
    self.cleanup( old_paper)
    self.startup()
    self.on_submode_switch( 0)





## -------------------- USER TEMPLATE MODE --------------------

class user_template_mode( template_mode):

  def __init__( self):
    template_mode.__init__( self)
    self.name = _('users templates')
    self.submodes = [Store.utm.get_template_names()]
    self.submodes_names = [Store.utm.get_template_names()]
    self.submode = [0]
    self.pulldown_menu_submodes = [0]
    #self.register_key_sequence( 'C-t C-1', self._mark_focused_as_template_atom_or_bond)
    self.template_manager = Store.utm
    



## -------------------- EXTERNAL DATA MODE --------------------

class external_data_mode( basic_mode):

  def __init__( self):
    basic_mode.__init__( self)
    self.name = _('External data management')
    self.submodes = [['molecule','atom','bond'], Store.app.paper.edm.get_definition_classes()]
    self.submodes_names = [[_('molecule'),_('atom'),_('bond')],Store.app.paper.edm.get_definition_classes()]
    self.submode = [0,0]
    self.pulldown_menu_submodes = [1]
    self.focused = None
    self._items = set()
    self._entries = {}
    self._win = None
    self._active_object = None
    self._object_selector = None  # item that highlights the active object
    self._focus_selector = None  # item that highlights the object refered in entry


  def mouse_down( self, event, modifiers=[]):
    if self.focused:
      e = self._get_active_entry()
      if e:
        e.value = self.focused.id
        self._entry_left()
        self._entry_entered( e)
      else:
        if self.get_submode( 0) == "molecule":
          self._activate_object( self.focused.parent)
        else:
          self._activate_object( self.focused)
        self._populate_table_for_active_object()


  def _get_active_entry( self):
    e = Store.app.focus_get()
    if e in self._entries.values() and e.type_class == "reference":
      return e


  def _activate_object( self, obj):
    self._active_object = obj
    if self._object_selector:
      Store.app.paper.delete( self._object_selector)
    self._object_selector = Store.app.paper.create_rectangle( obj.bbox(), outline='red', width=2)
    self._add_bindings_according_to_submode()


  def _populate_table_for_active_object( self):
    defs = Store.app.paper.edm.get_definitions_for_class_and_type( self.get_submode( 1), self.get_submode( 0))
    if defs:
      for k,v in defs.items():
        val = Store.app.paper.edm.get_data( self.get_submode( 1), self._active_object, k)
        if hasattr( val, 'id'):
          self._entries[ k].value = val.id
        else:
          self._entries[ k].value = val
    self._draw_the_arrows()


  def _entry_entered( self, e):
    obj = Store.id_manager.get_object_with_id_or_none( e.value)
    if obj:
      self._focus_selector = Store.app.paper.create_rectangle( obj.bbox(), outline="orange", width=2)
    self._add_bindings_according_to_active_name( e.type)


  def _entry_left( self):
    if self._focus_selector:
      Store.app.paper.delete( self._focus_selector)
    self._add_bindings_according_to_submode()


  def _set_data( self):
    defs = Store.app.paper.edm.get_definitions_for_class_and_type( self.get_submode( 1), self.get_submode( 0))
    if defs:
      for k,v in defs.items():
        val = self._entries[ k].value
        if val != '':
          if v['type'] in Store.app.paper.edm.reference_types:
            # can be passed to edm.set_data now
            try:
              val = Store.id_manager.get_object_with_id( val)
            except Exception as e:
              pass
          Store.app.paper.edm.set_data( self.get_submode( 1), self._active_object, k, val)

    self._draw_the_arrows()
    Store.log( _("The data were set to the active item"), message_type="info")


  def _show_table_for_submode( self):
    defs = Store.app.paper.edm.get_definitions_for_class_and_type( self.get_submode( 1), self.get_submode( 0))
    if defs:
      self._frame = tkinter.Frame( Store.app.paper)
      self._win = Store.app.paper.create_window( 500, 100, window=self._frame)
      for k,v in defs.items():
        label = tkinter.Label( self._frame, text=v['text'])
        if v['type'] in Store.app.paper.edm.reference_types:
          entry = external_data.ExternalDataEntry( self._frame, v['type'], "reference")
          entry.bind( "<FocusIn>", lambda e: self._entry_entered( e.widget))
          entry.bind( "<FocusOut>", lambda e: self._entry_left())
        elif type( v['type']) == list:
          entry = external_data.ExternalDataListSelection( self._frame, v['type'])
        else:
          entry = external_data.ExternalDataEntry( self._frame, v['type'], "internal")
        self._items.add( label)
        self._entries[ k] = entry
        label.pack()
        entry.pack()
      tkinter.Button( self._frame, text=_("Set"), command=self._set_data).pack()
    

  def _draw_the_arrows( self):
    for e in self._entries.values():
      if e.type_class == "reference":
        e.cleanup( Store.app.paper)
        obj = Store.id_manager.get_object_with_id_or_none( e.value)
        if obj:
          e.arrow = self._draw_arrow_from_to( e, obj)
    self._add_bindings_according_to_submode()
    

  def _draw_arrow_from_to( self, e, obj):
    e.update()
    x0, y0 = Store.app.paper.bbox( self._win)[0:2]
    x1 = x0
    y1 = y0 + e.winfo_y() + e.winfo_height()/2
    bbox = obj.bbox()
    x2 = (bbox[0]+bbox[2])/2
    y2 = (bbox[1]+bbox[3])/2
    arrow = Store.app.paper.create_line( x1, y1, x2, y2, arrow="last", fill="blue", width=1)
    return arrow


  def _add_bindings_according_to_submode( self):
    name = self.get_submode(0)
    self._add_bindings_according_to_active_name( name)
    

  def _add_bindings_according_to_active_name( self, name):
    Store.app.paper.remove_bindings()
    if name == 'molecule':
      Store.app.paper.add_bindings( active_names=('atom','bond'))
    elif name == 'atom':
      Store.app.paper.add_bindings( active_names=('atom',))
    elif name == 'bond':
      Store.app.paper.add_bindings( active_names=('bond',))


    


  def on_submode_switch( self, submode_index, name=''):
    Store.app.paper.remove_bindings()
    self._add_bindings_according_to_submode()
    self._delete_table()
    self._show_table_for_submode()
    for x in Store.app.paper.stack:
      if x.object_type == self.get_submode( 0):
        self._activate_object( x)
        break
    self._populate_table_for_active_object()


  def startup( self):
    Store.app.paper.unselect_all()



  def cleanup( self, paper=None):
    basic_mode.cleanup( self, paper=paper)
    pap = paper or Store.app.paper
    self._delete_table( pap)
    pap.add_bindings()



  def _delete_table( self, paper=None):
    pap = paper or Store.app.paper
    if self._win:
      self._items = set()
      [e.cleanup( pap) for e in self._entries.values()]
      self._entries = {}
      self._frame = None
      pap.delete( self._win)
      self._win = None
    for x in ('_object_selector','_focus_selector'):
      pap.delete( self.__dict__[ x])
      self.__dict__[ x] = None



  def on_paper_switch( self, old_paper, new_paper):
    self.cleanup( old_paper)
    self.startup()
    self.on_submode_switch()








### -------------------- RAPID DRAW MODE --------------------

class rapid_draw_mode( edit_mode):

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('Rapid drawing')
    self._moved_line = None
    self._start_atom = None

    self.submodes = [['30','18','6','1'],
                     ['fixed','freestyle'],
                     ['noclean','autoclean']]
    self.submodes_names = [[_('30'),_('18'),_('6'),_('1')],
                           [_('fixed length'),_('freestyle')],
                           [_('do nothing after drawing is done'),_('auto clean after drawing is finished')]]
    self.submode = [0, 0, 0]

    self.molecule = None
    self.register_key_sequence( '##'+string.ascii_lowercase, self._set_name_to_last, use_warning=0)
    self._key_to_atom_map = {'l':'Cl', 'r':'Br', 'a':'Na','i':'Li'}
    self._bond_to_fix = None
    
  def mouse_down( self, event, modifiers = []):
    #edit_mode.mouse_down( self, event, modifiers = modifiers)
    Store.app.paper.unselect_all()
    self.handle_click( event, modifiers=modifiers, button=1)


  def handle_click( self, event, modifiers=[], button=1):
    if not self.focused:
      if not self.molecule:
        self.molecule = Store.app.paper.new_molecule()
        self._start_atom = self.molecule.create_new_atom( event.x, event.y)
      else:
        x, y = self._get_xy_according_to_submodes( event)
        self._start_atom, b = self.molecule.add_atom_to( self._start_atom, bond_to_use=self.get_edge( self.molecule, modifiers), pos=(x, y))
    elif isinstance( self.focused, oasa.graph.vertex):
      if self.molecule and self.focused != self._start_atom:
        if self.focused.molecule == self.molecule:
          if not self._start_atom in self.focused.neighbors:
            e = self.molecule.add_edge( self._start_atom, self.focused, e=self.get_edge( self.molecule, modifiers))
            e.draw()
            self._start_atom = self.focused
          else:
            self._start_atom = self.focused
        else:
          mol = self.focused.molecule
          self.molecule.eat_molecule( self.focused.molecule)
          Store.app.paper.stack.remove( mol)
          e = self.molecule.add_edge( self.focused, self._start_atom, e=self.get_edge( self.molecule, modifiers))
          e.draw()
          self._start_atom = self.focused
      elif not self.molecule:
        self.molecule = self.focused.molecule
        self._start_atom = self.focused
        self._bond_to_fix = list( self.molecule.bonds)[0]
    else:
      return 

    if self._moved_line:
      Store.app.paper.delete( self._moved_line)

    # create the _moved_line according to set submodes
    x, y = self._get_xy_according_to_submodes( event)
    self._moved_line = Store.app.paper.create_line( self._start_atom.x, self._start_atom.y, x, y)

    Store.app.paper.add_bindings()
    


  def get_edge( self, mol, modifiers):
    e = mol.create_edge()
    if 'shift' in modifiers:
      e.order = 2
    else:
      e.order = 1
    return e



  def mouse_move( self, event):
    if self._moved_line:
      x, y = self._get_xy_according_to_submodes( event)
      Store.app.paper.coords( self._moved_line, (self._start_atom.x, self._start_atom.y, x, y))



  def mouse_down3( self, event, modifiers = []):
    if self._moved_line:
      Store.app.paper.delete( self._moved_line)

    Store.app.paper.start_new_undo_record()

    if self.get_submode( 2) == 'autoclean':
      if self._bond_to_fix:
        Store.app.paper.select( [self._bond_to_fix])
        self._bond_to_fix = None
      else:
        Store.app.paper.select( [self._start_atom.get_neighbor_edges()[0]])
      Store.app.clean()

    self._start_atom = None
    self.molecule = None
    self._moved_line = None


    
  def mouse_up( self, event):
    pass


  def mouse_click( self, event):
    pass


  def mouse_drag( self, event):
    pass


  def enter_object( self, object, event):
    if self.focused:
      self.focused.unfocus()
    self.focused = object
    self.focused.focus()

      
  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    else:
      pass #warn( "leaving NONE", UserWarning, 2)


  def _set_name_to_last( self, char=''):
    if char and self._start_atom:
      if char.upper() in PT.periodic_table:
        self._start_atom.set_name( char.upper())
        self._start_atom.redraw()
      elif char in self._key_to_atom_map:
        self._start_atom.set_name( self._key_to_atom_map[ char])
        self._start_atom.redraw()



  def _get_xy_according_to_submodes( self, event):
    if self._start_atom:
      if self.get_submode(1) == "freestyle":
        return event.x, event.y
      else:
        dx = event.x - self._start_atom.x
        dy = event.y - self._start_atom.y
        x,y = geometry.point_on_circle( self._start_atom.x,
                                        self._start_atom.y,
                                        Screen.any_to_px( Store.app.paper.standard.bond_length),
                                        direction = (dx, dy),
                                        resolution = int( self.get_submode( 0)))
        return x, y
    else:
      return event.x, event.y



# -------------------- BRACKETS MODE --------------------

class bracket_mode( edit_mode):


  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('Brackets')
    self.submodes = [['rectangularbracket','roundbracket']]
    self.submodes_names = [[_('Rectangular'),_("Round")]]
    self.submode = [0]


  def _end_of_empty_drag( self, x1, y1, x2, y2):
    if self.get_submode(0) == "rectangularbracket":
      dx = 0.05*math.sqrt( (y2-y1)**2 + (x2-x1)**2)
      Store.app.paper.new_polyline( [x1+dx, y1,
                                     x1,    y1,
                                     x1,    y2,
                                     x1+dx, y2]).draw()

      Store.app.paper.new_polyline( [x2-dx, y1,
                                     x2,    y1,
                                     x2,    y2,
                                     x2-dx, y2]).draw()

    elif self.get_submode(0) == "roundbracket":
      dx = 0.05*math.sqrt( (y2-y1)**2 + (x2-x1)**2)
      dy = abs( 0.05*(y2-y1))
      l1 = Store.app.paper.new_polyline( [x1+dx, y1,
                                          x1,    y1+dy,
                                          x1,    y2-dy,
                                          x1+dx, y2])
      l1.spline = True
      l1.draw()
      l2 = Store.app.paper.new_polyline( [x2-dx, y1,
                                          x2,    y1+dy,
                                          x2,    y2-dy,
                                          x2-dx, y2])
      l2.spline = True
      l2.draw()
    Store.app.paper.start_new_undo_record()





# -------------------- MISCELANOUS MODE --------------------

class misc_mode( edit_mode):
  """container mode for small, seldom needed modes"""

  wavy_width = 3

  def __init__( self):
    edit_mode.__init__( self)
    self.name = _('Miscelanous small modes')
    self.submodes = [['numbering','wavyline']]
    self.submodes_names = [[_('Numbering'),_("Wavy line")]]
    self.submode = [0]

    self._number = 1
    self._line = None


  def mouse_click( self, event):
    if self.get_submode( 0) == "numbering": 
      if self.focused and hasattr( self.focused, 'number'):
        self.focused.number = str( self._number)
        self._number += 1
        for m in self.focused.get_marks_by_type( "atom_number"):
          m.auto = False
        Store.app.paper.start_new_undo_record()

  def mouse_down( self, event, modifiers=None):
    edit_mode.mouse_down( self, event)

  def mouse_drag( self, event):
    if self.get_submode( 0) == "numbering":
      edit_mode.mouse_drag( self, event)
    else:
      coords = self._startx, self._starty, event.x, event.y
      if self._line:
        Store.app.paper.coords( self._line, *coords)
      else:
        self._line = Store.app.paper.create_line( *coords)
        

  def mouse_up( self, event):
    if self.get_submode( 0) == "numbering":
      edit_mode.mouse_up( self, event)
    elif self.get_submode( 0) == "wavyline":
      coords = self._startx, self._starty, event.x, event.y
      if self._line:
        Store.app.paper.delete( self._line)
        self._line = None
        # create the wavy line
        self._draw_wavy( coords)
      Store.app.paper.start_new_undo_record()


  def _draw_wavy( self, coords):
    x1, y1, x2, y2 = coords
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.wavy_width/2.0)
    d = math.sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    step_size = self.wavy_width
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 
    ddx = x - x1 
    ddy = y - y1 

    coords2 = []
    coords2.extend((x1, y1))
    for i in range( 0, int( round( d/ step_size))+1):
      coords = [x1+dx*i*step_size+ddx, y1+dy*i*step_size+ddy, x1+dx*i*step_size-ddx, y1+dy*i*step_size-ddy] 
      if i % 2:
        coords2.extend((coords[0], coords[1]))
      else:
        coords2.extend((coords[2], coords[3]))
    coords2.extend((x2, y2)) 
    Store.app.paper.new_polyline( coords2).draw()
      

  def cleanup( self):
    edit_mode.cleanup( self)
    Store.app.paper.remove_bindings()
    Store.app.paper.add_bindings()



  def startup( self):
    Store.app.paper.remove_bindings()
    Store.app.paper.add_bindings( active_names=('atom',))
    Store.app.paper.unselect_all()
    self._number = 1
    

  def leave_object( self, event):
    if self.focused:
      self.focused.unfocus()
      self.focused = None
    else:
      warn( "leaving NONE", UserWarning, 2)







def event_to_key( event):
  key = event.keysym
  # 2 hacks to prevent ' ' -> 'space', '.' -> 'period' and other conversions
  # first is dealing with "strange keys" (see data.strange_key_symbols for more info)
  if key in data.strange_key_symbols:
    key = data.strange_key_symbols[ key]
  # second is for keys that are more consistent in their behavior (char is not changing with Ctrl)
  elif len(key) > 1 and key.lower() == key:
    key = event.char
  # now special keys as Ctrl, Alt etc.
  elif key in data.special_key_symbols:
    key = data.special_key_symbols[ key]
  else:
    # normal keys should be lowercase, specials uppercase
    if len( key) == 1:
      key = key.lower()
  if key:
    return key
  else:
    warn( 'how did we get here?!?', UserWarning, 2)
    return ''


