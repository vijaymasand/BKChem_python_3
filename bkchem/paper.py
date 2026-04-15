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


"""chem_paper - the main drawing part for BKChem resides here"""


from tkinter import Canvas, ALL
import tkinter.font as tkFont
import tkinter.messagebox as tkMessageBox
from . import classes
from . import arrow
from .molecule import molecule
from functools import reduce
try:
  from .oasa.oasa.transform import transform 
  from .oasa.oasa.transform3d import transform3d
except ImportError:
  from .oasa.transform import transform
  from .oasa.transform3d import transform3d
from . import misc
from .temp_manager import template_manager
import string
from . import data
from . import config
import gettext
_ = gettext.gettext
ngettext = gettext.ngettext
from . import messages
from . import dom_extensions
import xml.dom.minidom as dom
import operator
from warnings import warn
from . import undo
import math
from . import xml_writer
from .oasa import periodic_table as PT
import Pmw
from . import graphics
import types
from . import os_support
import copy
from . import dialogs
from . import CDML_versions
import os
from . import parents
from .reaction import reaction
from . import debug
from . import oasa
from .external_data import external_data_manager
from .group import group
from .atom import atom
from .textatom import textatom
from . import oasa
from .oasa import geometry
from .id_manager import id_manager
from . import interactors
from . import checks
from .helper_graphics import selection_rect
      
from .singleton_store import Store, Screen


class chem_paper( Canvas, object):

  object_type = 'paper'
  all_names_to_bind = ('atom','bond','arrow','point','plus','text','vector','helper_rect')
  # the following classes should have refocus triggered when a different item of these
  # composite objects is focused - this is typical for selection_rect that needs to respond
  # differently in different corners
  classes_with_per_item_reselection = (selection_rect,)
  

  def __init__( self, master = None, file_name={}, **kw):
    Canvas.__init__( self, master, kw)
    
    self.clipboard = None

    self.standard = self.get_personal_standard()
    self.submode = None
    self.selected = []    # selected item
    self.__in = 1
    self.__in_id = 0
    self._id_2_object = {}
    self.stack = []

    # bindings to input events
    self.set_bindings()

    self.set_viewport()


    # undo manages
    self.um = undo.undo_manager( self)  # undo manager

    # external data management
    self.edm = external_data_manager()
    self.edm.load_available_definitions()
    #print "loaded definitions for classes:", self.edm.load_available_definitions()

    # file name
    self.file_name = file_name

    # paper sizes etc.
    self._paper_properties = {}
    self.set_default_paper_properties()

    self.changes_made = 0

    self._do_not_focus = [] # this is to enable an ugly hack in a drag-and-focus hack


  def set_bindings( self):
    if not Store.app.in_batch_mode:
      self.bind( "<B1-Motion>", self._drag1)
      self.bind( "<ButtonRelease-1>", self._release1)
      self.bind( "<Shift-B1-Motion>", self._drag1)
      self.bind( "<Button-1>", lambda e: self._pressed1( e, mod=[]))
      self.bind( "<Shift-Button-1>", lambda e: self._pressed1( e, mod=['shift']))
      self.bind( "<Control-Button-1>", lambda e: self._pressed1( e, mod=['ctrl']))
      self.bind( "<Control-B1-Motion>", self._drag1)
      self.bind( "<Delete>", self.key_pressed)
      self.bind( "<Key>", self.key_pressed)
      self.bind( "<KeyRelease>", self.key_released)
      self.bind( "<Enter>", self.take_focus)
      self.bind( "<Button-3>", self._n_pressed3)
      self.bind( "<Shift-Button-3>", lambda e: self._n_pressed3( e, mod=["shift"]))
      self.bind( "<Control-Button-3>", lambda e: self._n_pressed3( e, mod=["ctrl"]))
      self.bind( "<Button-2>", self._n_pressed2)
      self.bind( "<Shift-Button-2>", lambda e: self._n_pressed2( e, mod=["shift"]))
      self.bind( "<Control-Button-2>", lambda e: self._n_pressed2( e, mod=["ctrl"]))
      self.bind( "<Motion>", self._move)
      self.bind( "<Leave>", self._leave)
      # scrolling (linux only?)
      self.bind( "<Button-4>", lambda e: self.yview( "scroll", -1, "units"))
      self.bind( "<Button-5>", lambda e: self.yview( "scroll", 1, "units"))
      # scrolling (windows)
      #self.bind( "<MouseWheel>", lambda e: self.yview( "scroll", -misc.signum( e.delta), "units"))
      # hope it does not clash on some platforms :(
      
      # Mouse wheel zoom - works on Linux (Button-4/5) and Windows/Mac (MouseWheel)
      self.bind( "<Button-4>", self._on_zoom_in)
      self.bind( "<Button-5>", self._on_zoom_out)
      self.bind( "<MouseWheel>", self._on_mousewheel)


  ### PROPERTIES


  # molecules
  def _get_molecules( self):
    return [o for o in self.stack if isinstance( o, molecule)]

  molecules = property( _get_molecules)


  # arrows
  def _get_arrows( self):
    return [o for o in self.stack if isinstance( o, arrow.arrow)]

  arrows = property( _get_arrows)


  # pluses
  def _get_pluses( self):
    return [o for o in self.stack if isinstance( o, classes.plus)]

  pluses = property( _get_pluses)



  # texts
  def _get_texts( self):
    return [o for o in self.stack if isinstance( o, classes.text)]

  texts = property( _get_texts)


  # vectors
  def _get_vectors( self):
    return [o for o in self.stack if isinstance( o, graphics.vector_graphics_item)]

  vectors = property( _get_vectors)


  # top_levels
  def _get_top_levels( self):
    #print [o for o in self.stack if not isinstance( o, graphics.top_level)]
    return self.stack
    #return [o for o in self.stack if isinstance( o, graphics.top_level)]

  top_levels = property( _get_top_levels)


  # selection related properties
  def _get_selected_mols( self):
    return [o for o in self.selected_to_unique_top_levels()[0] if isinstance( o, molecule)]

  selected_mols = property( _get_selected_mols)

  def _get_selected_atoms( self):
    return [o for o in self.selected if isinstance( o, oasa.graph.vertex)]

  selected_atoms = property( _get_selected_atoms)

  def _get_selected_bonds( self):
    return [o for o in self.selected if isinstance( o, oasa.graph.edge)]

  selected_bonds = property( _get_selected_bonds)

  def _is_two_or_more_selected( self):
    if len( self.selected_to_unique_top_levels()[0]) > 1:
      return True
    else:
      return False

  two_or_more_selected = property( _is_two_or_more_selected)

  def _get_groups_selected( self):
    return [o for o in self.selected if isinstance( o, group)]

  groups_selected = property( _get_groups_selected)


  def _is_one_molecule_selected( self):
    if len( self.selected_mols) != 1:
      return False
    else:
      return True

  one_mol_selected = property( _is_one_molecule_selected)


  ### // PROPERTIES




  def add_bindings( self, active_names=()):
    self.lower( self.background)
    [o.lift() for o in self.stack]
    if not Store.app.in_batch_mode:
      if not active_names:
        names = self.all_names_to_bind
      else:
        names = active_names
##       for name in names:
##         self.tag_bind( name, '<Enter>', self.enter_item)
##         self.tag_bind( name, '<Leave>', self.leave_item)
    self._do_not_focus = [] # self._do_not_focus is temporary and is cleaned automatically here
    self.event_generate( "<<selection-changed>>")
    # we generate this event here because this method is often called after some change as a last thing


  def remove_bindings( self, ids=()):
    if not ids:
      for tag in self.all_names_to_bind + ("mark",):
        self.tag_unbind( tag, '<Enter>')
        self.tag_unbind( tag, '<Leave>')
    else:
      [self.tag_unbind( id, '<Enter>') for id in ids]
      [self.tag_unbind( id, '<Leave>') for id in ids]
    
  ## event bound methods

  ## overall


  def _pressed1( self, event, mod=None):
    "button 1"
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    Store.app.mode.mouse_down( event, modifiers=mod or [])





  def _release1( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    Store.app.mode.mouse_up( event)
    




  def _drag1( self, event):
    # unfortunately we need to simulate "enter" and "leave" in this way because
    # when B1 is down such events do not occur
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    Store.app.update_cursor_position( event.x, event.y)
    Store.app.mode.mouse_drag( event) 
    b = self.find_overlapping( event.x-2, event.y-2, event.x+2, event.y+2)
    b = filter( self.is_registered_id, b)
    a = map( self.id_to_object, b)
    a = [i for i in a if i not in self._do_not_focus]
    if a:
      a = a[-1]
    else:
      a = None
    if a:
      if not self.__in:
        self.__in = a
        Store.app.mode.enter_object( self.__in, event)
      elif a != self.__in:
        self.__in = a
        Store.app.mode.leave_object( event)
        Store.app.mode.enter_object( self.__in, event)
    else:
      if self.__in or Store.app.mode.focused: # sometimes self.__in and Store.app.mode.focused is different
        self.__in = None
        Store.app.mode.leave_object( event)





  def _n_pressed3( self, event, mod=None):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    Store.app.mode.mouse_down3( event, modifiers=mod or [])



  def _n_pressed2( self, event, mod=None):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    Store.app.mode.mouse_down2( event, modifiers=mod or [])





  def _move( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)

    Store.app.update_cursor_position( event.x, event.y)
    Store.app.mode.mouse_move( event)


    b = self.find_overlapping( event.x-3, event.y-3, event.x+3, event.y+3)
    b = filter( self.is_registered_id, b)
    id_objs = [(x, self.id_to_object( x)) for x in b]
    a = [i for i in id_objs if i[1] not in self._do_not_focus]

    if a:
      fid, fobj = a[-1]
    else:
      fid, fobj = None, None

    # this may cause some trouble later on
    # it was hacked because of the http_server2 functionality, but could break unexpected things
    self.__in = Store.app.mode.focused

    if fobj and (fobj != self.__in or (misc.isinstance_of_one( fobj, self.classes_with_per_item_reselection) and self.__in_id != fid)):
      self.__in = fobj
      self.__in_id = fid
      Store.app.mode.enter_object( self.__in, event)
    elif not fobj and self.__in:
      #if not a and Store.app.mode.focused:
      self.__in = None
      self.__in_id = None
      Store.app.mode.leave_object( event)





  def _enter( self, event):
    Store.app.mode.clean_key_queue()





  def _leave( self, event):
    Store.app.mode.clean_key_queue()

  # item bound methods





  def enter_item( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)

    #
##     b = self.find_overlapping( event.x-3, event.y-3, event.x+3, event.y+3)
##     b = filter( self.is_registered_id, b)
##     a = map( self.id_to_object, b)
##     print a
##     a = [i for i in a if i not in self._do_not_focus]
##     print a

##     if a:
##       a = a[-1]
##     else:
##       a = None
    # //

    try:
      a = self.id_to_object( self.find_withtag( 'current')[0])
    except IndexError:
      a = None
    if a and a != self.__in:
      self.__in = a
      Store.app.mode.enter_object( self.__in, event)




  def leave_item( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    if self.__in:
      self.__in = None
      Store.app.mode.leave_object( event)





  def key_pressed( self, event):
    Store.app.mode.key_pressed( event)





  def key_released( self, event):
    Store.app.mode.key_released( event)

  ## end of event bound methods





  def select( self, items):
    "adds an object to the list of other selected objects and calls their select() method"
    for o in items:
      if o.object_type in ('arrow','polygon','polyline'):
        # we cannot allow arrows or polygons to be selected because selection of arrow and its points
        # doubles some actions (moving etc.) and this couldn't be easily solved other way
        self.select( o.points)
      elif o.object_type == 'selection_rect' or o.object_type == 'selection_square':
        return
      elif o not in self.selected:
        self.selected.append( o)
        o.select()
    self.event_generate( "<<selection-changed>>")
    #print [o.object_type for o in self.selected]




  def unselect( self, items):
    "reverse of select()"
    for item in items:
      try:
        self.selected.remove( item)
        item.unselect()
      except ValueError:
        pass #warn( 'trying to unselect not selected object '+id( item))
    self.event_generate( "<<selection-changed>>")




  def unselect_all( self):
    [o.unselect() for o in self.selected]
    self.selected = []
    self.event_generate( "<<selection-changed>>")




  def delete_selected( self):
    # ARROW
    to_delete = [o for o in self.selected if o.object_type == 'arrow']
    [a.arrow.delete_point( a) for a in self.selected if a.object_type == 'point' and (a.arrow not in to_delete)]
    for a in self.arrows:
      if a.is_empty_or_single_point():
        if a not in to_delete:
          to_delete += [a]
      else:
        a.redraw()
    map( self.stack.remove, to_delete)
    [o.delete() for o in to_delete]
    # Force canvas update to refresh display after arrow deletion
    self.update()
    self.update_idletasks()
    # PLUS
    to_delete = filter( lambda o: o.object_type == 'plus', self.selected)
    map( lambda o: o.delete(), to_delete)
    map( self.stack.remove, to_delete)
    # TEXT
    to_delete = filter( lambda o: o.object_type == 'text', self.selected)
    for t in to_delete:
      t.delete()
      self.stack.remove( t)
    # VECTOR GRAPHICS
    for o in [obj for obj in self.selected if obj.object_type == 'rect' or obj.object_type == 'oval']:
      o.delete()
      self.stack.remove( o)
    # polygon is special (points were removed on begining together with arrow points)
    to_delete = [o for o in self.selected if o.object_type in ('polygon','polyline')]
    for a in self.vectors:
      if a.object_type in ('polygon','polyline'):
        if a.is_empty_or_single_point():
          if a not in to_delete:
            to_delete += [a]
        else:
          a.redraw()
    map( self.stack.remove, to_delete)
    [o.delete() for o in to_delete]
    # BOND AND ATOM
    bonds = [o for o in self.selected if o.object_type == 'bond']
    atoms = [o for o in self.selected if o.object_type == 'atom']
    deleted, new, mols_to_delete = [], [], []
    changed_mols = []
    for mol in self.molecules:
      items = [o for o in bonds+atoms if o.molecule == mol]
      if items:
        changed_mols.append( mol)
      now_deleted, new_mols = mol.delete_items( items)
      deleted += now_deleted
      new += new_mols
      if new_mols:
        mols_to_delete.append( mol)
    if new:
      map( self.stack.remove, mols_to_delete)
      self.stack.extend( new)
    empty_mols = filter( lambda o: o.is_empty(), self.molecules)
    [self.stack.remove( o) for o in empty_mols]
    # start new undo
    if self.selected:
      self.start_new_undo_record()
    self.selected = []
    #return deleted

    ## check reactions
    [a.reaction.check_the_references( self.stack) for a in self.arrows]
    self.event_generate( "<<selection-changed>>")      

      


  def bonds_to_update( self, exclude_selected_bonds=True):
    a = reduce( operator.or_, map( set, [v.get_neighbor_edges() for v in self.selected if v.object_type == "atom"]), set())
    # if bond is also selected then it moves with and should not be updated
    if exclude_selected_bonds:
      return [b for b in a if b not in self.selected]
    else:
      return a





  def atoms_to_update( self):
    a = []
    for o in self.selected:
      if o.object_type == 'bond':
        a.extend( o.atoms)
    if a:
      return misc.difference( misc.filter_unique( a), self.selected)
    else:
      return []





  def arrows_to_update( self):
    a = map( lambda o: o.arrow, filter( lambda p: p.object_type == 'point', self.selected))
    return misc.filter_unique( a)







  def read_package( self, CDML, draw=True):
    self.onread_id_sandbox_activate() # to sandbox the ids 

    original_version = CDML.getAttribute( 'version')
    success = CDML_versions.transform_dom_to_version( CDML, config.current_CDML_version)
    if not success:
      if not tkMessageBox.askokcancel( _('Proceed'),
				       _('''This CDML document does not seem to have supported version.
				       \n Do you want to proceed reading this document?'''),
                                       default = 'ok',
				       parent=self):
        return None
    # paper properties
    paper = [o for o in CDML.childNodes if (not o.nodeValue) and (o.localName == 'paper')]
    if paper:
      paper = paper[0]
      t = paper.getAttribute( 'type')
      o = paper.getAttribute( 'orientation')
      sx = paper.getAttribute( 'size_x')
      sy = paper.getAttribute( 'size_y')
      if paper.getAttribute( 'crop_svg'):
        cr = int( paper.getAttribute( 'crop_svg'))
      else:
        cr = 1
      cm = int( paper.getAttribute( 'crop_margin') or self.standard.paper_crop_margin)
      use_real_minus = int( paper.getAttribute( 'use_real_minus') or Store.pm.get_preference( "use_real_minus") or 0)
      replace_minus = int( paper.getAttribute( 'replace_minus') or Store.pm.get_preference( "replace_minus") or 0)
      self.set_paper_properties( type=t, orientation=o, x=sx, y=sy, crop_svg=cr, crop_margin=cm, use_real_minus=use_real_minus, replace_minus=replace_minus)
    else:
      self.set_default_paper_properties()
    # viewport
    viewport = dom_extensions.getFirstChildNamed( CDML, 'viewport')
    if viewport:
      viewport = viewport.getAttribute( 'viewport')
      self.set_viewport( view= map( float, viewport.split(' ')))
    else:
      self.set_viewport()
    # standard must be read before all items
    new_standard = self.read_standard_from_dom( CDML)
    old_standard = self.standard
    if new_standard:
      self.standard = new_standard
    for p in CDML.childNodes:
      if p.nodeName in data.loadable_types:
        o = self.add_object_from_package( p)
        if not o:
          continue
        if o.object_type == 'molecule':
          if not o.is_connected():
            mols = o.get_disconnected_subgraphs()
          else:
            mols = [o]
          for mol in mols:
            if float( original_version) < 0.12:
              # we need to know if the bond is positioned according to the rules or the other way
              # it is however very expensive for large molecules with many double bonds and therefore
              # it was in version '0.12' of CDML moved to the saved package and does not have to be
              # checked on start anymore
              [b.post_read_analysis() for b in mol.bonds]
          if draw:
            [mol.draw( automatic="none") for mol in mols]
        else:
          if draw:
            o.draw()
    # now check if the old standard differs
    if new_standard and old_standard != self.standard and not Store.app.in_batch_mode:
      if not tkMessageBox.askokcancel( _('Replace standard values'),
				       messages.standards_differ_text,
                                       default = 'ok',
				       parent=self):
        self.standard = old_standard

    # external data
    ees = CDML.getElementsByTagName( "external-data")
    if ees:
      [self.edm.read_package( ee) for ee in ees]

    # finish
    # we close the sandbox and generate new ids for everything
    self.onread_id_sandbox_finish()

    # this forces forgetting of old viewport and effectively transforms the coordinates for rest of work
    self.set_viewport()
    
    if draw:
      self.add_bindings()
    self.um.start_new_record()


  def onread_id_sandbox_activate( self):
    """For reading we provide a new, clean id_manager as a sandbox to prevent
    clashes between ids that might be already on the paper and ids that are in the file.
    This is especialy needed for copying and template addition (although this is done somewhere else)"""
    self.__old_id_manager = Store.id_manager
    Store.id_manager = id_manager()
    

  def onread_id_sandbox_finish( self, apply_to=None):
    Store.id_manager = self.__old_id_manager
    del self.__old_id_manager
    if apply_to == None:
      os = self.stack
    else:
      os = apply_to
    for o in os:
      o.generate_id()
      if isinstance( o, molecule):
        [ch.generate_id() for ch in o.children]


  def get_package( self):
    doc = dom.Document()
    root = dom_extensions.elementUnder( doc, 'cdml', attributes = (('version', config.current_CDML_version),
                                                                   ( 'xmlns', data.cdml_namespace)))
    info = dom_extensions.elementUnder( root, 'info')
    dom_extensions.textOnlyElementUnder( info, 'author_program', 'BKChem', attributes = (('version',config.current_BKChem_version),))
    paper = dom_extensions.elementUnder( root, 'paper',
                                         attributes = (('type', self._paper_properties['type']),
                                                       ('orientation', self._paper_properties['orientation']),
                                                       ('crop_svg', '%d' % self._paper_properties['crop_svg']),
                                                       ('crop_margin', '%d' % self._paper_properties['crop_margin']),
                                                       ('use_real_minus', '%d' % self._paper_properties['use_real_minus']),
                                                       ('replace_minus', '%d' % self._paper_properties['replace_minus'])
                                                       ))
    if self._paper_properties['type'] == 'custom':
      dom_extensions.setAttributes( paper, (('size_x', '%d' % self._paper_properties['size_x']),
                                            ('size_y', '%d' % self._paper_properties['size_y'])))
    dom_extensions.elementUnder( root, 'viewport', attributes = (('viewport','%f %f %f %f' % self._view),))
    root.appendChild( self.standard.get_package( doc))
    for o in self.stack:
      root.appendChild( o.get_package( doc))
    for a in self.arrows:
      if not a.reaction.is_empty():
        root.appendChild( a.reaction.get_package( doc))

    # external data
    edm_doc = self.edm.get_package( doc)
    if edm_doc:
      root.appendChild( edm_doc)

    return doc
    

  def mrproper( self):
    self.unselect_all()

    for a in self.stack:
      if isinstance( a, parents.container):
        for ch in a.children:
          if hasattr( ch, 'id'):
            Store.id_manager.unregister_id( ch.id, ch)

          if hasattr( ch, "paper"):
            try:
              ch.paper = None
            except:
              pass
          if hasattr( ch, "canvas"):
            try:
              ch.canvas = None
            except:
              pass
          if hasattr( ch, "ftext") and ch.ftext:
            ch.ftext.canvas = None
            for i in ch.ftext.items:
              i.paper = None

      if isinstance( a, molecule):
        for ch in a.children:
          ch.molecule = None
          if hasattr( ch, "group_graph"):
            ch.group_graph = None

          if isinstance( ch, atom) or isinstance( ch, textatom):
            for m in ch.marks:
              m.atom = None


    self.clean_paper()
    
    self.um.mrproper()

    del self.clipboard
    del self.standard
    del self.submode
    self.mode = None
    del self.selected
    del self._id_2_object
    del self.um
    del self.file_name




  def clean_paper( self):
    "removes all items from paper and deletes them from molecules and items"
    self.unselect_all()
    self.delete( 'all')
    self.background = None
    del self._id_2_object
    self._id_2_object = {}

    for obj in self.stack:
      obj.paper = None
      if hasattr( obj, 'id'):
        Store.id_manager.unregister_id( obj.id, obj)
        
    del self.stack
    self.stack = []
    self.um.clean()
    self.changes_made = 0
    




  def del_container( self, container):
    container.delete()
    self.stack.remove( container)





  def handle_overlap( self):
    "puts overlaping molecules together to one and then calles handle_overlap(a1, a2) for that molecule"
    #import time
    #ttt = time.time()
    overlap = []
    for a in self.find_withtag('atom'):
      x, y = self.id_to_object( a).get_xy()
      for b in self.find_overlapping( x-2, y-2, x+2, y+2):
        if (a != b) and ( 'atom' in self.gettags( b)):
          a1 = self.id_to_object( a)
          a2 = self.id_to_object( b)
          if ( abs( a1.x - a2.x) < 2) and ( abs( a1.y - a2.y) < 2): 
            if (not [a2,a1] in overlap) and a1.z == a2.z:
              overlap.append( [a1,a2])

    deleted = []
    if overlap:
      mols = misc.filter_unique( map( lambda a: map( lambda b: b.molecule, a), overlap))
      #print 3, time.time() - ttt
      a_eatenby_b1 = []
      a_eatenby_b2 = []
      for (mol, mol2) in mols:
        while (mol in a_eatenby_b1):
          mol = a_eatenby_b2[ a_eatenby_b1.index( mol)]
        while (mol2 in a_eatenby_b1):
          mol2 = a_eatenby_b2[ a_eatenby_b1.index( mol2)]
        if mol != mol2 and (mol2 not in a_eatenby_b1):
          mol.eat_molecule( mol2)
          a_eatenby_b1.append( mol2)
          a_eatenby_b2.append( mol)
          self.stack.remove( mol2)
        else:
          deleted.extend( mol.handle_overlap())
      #print 4, time.time() - ttt
      deleted.extend( reduce( operator.add, [mol.handle_overlap() for mol in misc.difference( a_eatenby_b2, a_eatenby_b1)], []))
      self.selected = misc.difference( self.selected, deleted)
      self.add_bindings()
      Store.log( _('concatenated overlaping atoms'))

    preserved = []
    for a, b in overlap:
      preserved.append( a in deleted and b or a)
    return deleted, preserved
    #print 5, time.time() - ttt
      




  def set_name_to_selected( self, name, interpret=1):
    """sets name to all selected atoms and texts,
    also records it in an undo !!!"""
    if isinstance(name, bytes):
      name = name.decode('utf-8')
    vtype = None
    for item in self.selected[:]:
      if isinstance( item, oasa.graph.vertex):
        if name:
          self.unselect( [item])
          v = item.molecule.create_vertex_according_to_text( item, name, interpret=interpret)
          item.copy_settings( v)
          item.molecule.replace_vertices( item, v)
          item.delete()
          v.draw()
          self.select( [v])
          vtype = v.__class__.__name__
      if item.object_type == 'text':
        if name:
          item.xml_ftext = name
          item.redraw()
    if self.selected:
      self.start_new_undo_record()
    return vtype




  def take_focus( self, event):
    self.focus_set()





  def register_id( self, id, object):
    self._id_2_object[ id] = object





  def unregister_id( self, id):
    try:
      del self._id_2_object[ id]
    except KeyError:
      warn( 'trying to unregister not registered id', UserWarning, 3)





  def id_to_object( self, id):
    try:
      return self._id_2_object[ id]
    except KeyError:
      return None



  def object_to_id( self, obj):
    for k, v in self._id_2_object.items():
      if v == obj:
        return k
    return None




  def is_registered_object( self, o):
    """has this object a registered id?"""
    return o in self._id_2_object.values()



  def is_registered_id( self, id):
    return id in self._id_2_object.keys()




  def new_molecule( self):
    mol = molecule( self)
    self.stack.append( mol)
    return mol





  def add_molecule( self, mol):
    self.stack.append( mol)





  def new_arrow( self, points=[], spline=0, type="normal"):
    arr = arrow.arrow( self, type=type, points=points, spline=spline)
    self.stack.append( arr)
    arr.draw()
    return arr





  def new_plus( self, x, y):
    pl = classes.plus( self, xy = (x,y))
    self.stack.append( pl)
    pl.draw()
    return pl





  def new_text( self, x, y, text=''):
    txt = classes.text( self, xy=(x,y), text=text)
    self.stack.append( txt)
    return txt





  def new_rect( self, coords):
    rec = graphics.rect( self, coords=coords)
    self.stack.append( rec)
    return rec





  def new_oval( self, coords):
    ovl = graphics.oval( self, coords=coords)
    self.stack.append( ovl)
    return ovl





  def new_square( self, coords):
    rec = graphics.square( self, coords=coords)
    self.stack.append( rec)
    return rec





  def new_circle( self, coords):
    ovl = graphics.circle( self, coords=coords)
    self.stack.append( ovl)
    return ovl





  def new_polygon( self, coords):
    p = graphics.polygon( self, coords=coords)
    self.stack.append( p)
    return p



  def new_polyline( self, coords):
    p = graphics.polyline( self, coords=coords)
    self.stack.append( p)
    return p





  def list_bbox( self, items):
    """extension of Canvas.bbox to provide support for lists of items"""
    self.dtag( 'bbox', 'bbox') # just to be sure
    items_count = 0
    for i in items:
      if i is not None:
        self.addtag_withtag( 'bbox', i)
        items_count += 1
    if items_count == 0:
      return (0, 0, 0, 0)
    ret = self.bbox( 'bbox')
    self.dtag( 'bbox', 'bbox')
    return ret or (0, 0, 0, 0)





  def selected_to_clipboard( self, delete_afterwards=0, strict=0):
    """strict means that only what is selected is copied, not the whole molecule"""
    if self.selected:
      cp, unique = self.selected_to_unique_top_levels()
      # now find center of bbox of all objects in cp
      xmin, ymin, xmax, ymax = self.common_bbox( cp)
      xy = ( xmin+(xmax-xmin)/2, ymin+(ymax-ymin)/2)
      clipboard_doc = dom.Document()
      clipboard = dom_extensions.elementUnder( clipboard_doc, 'clipboard')
      for o in cp:
        if strict and isinstance( o, oasa.graph.graph):
          clipboard.appendChild( o.get_package( clipboard_doc, items=misc.intersection( o.children, self.selected)))
        else:
          clipboard.appendChild( o.get_package( clipboard_doc))
      Store.app.put_to_clipboard( clipboard, xy)
      if delete_afterwards:
        [self.del_container(o) for o in cp]
        Store.log( _("killed %s object(s) to clipboard") % str( len( cp)))
        self.start_new_undo_record()
      else:
        Store.log( _("copied %s object(s) to clipboard") % str( len( cp)))
      self.event_generate( "<<clipboard-changed>>")
      return [xmin, ymin, xmax, ymax]






  def paste_clipboard( self, xy):
    """pastes items from clipboard to position xy"""
    clipboard = Store.app.get_clipboard()
    clipboard_pos = Store.app.get_clipboard_pos()
    if clipboard:
      new = []
      self.unselect_all()
      if xy:
        dx = xy[0] - clipboard_pos[0]
        dy = xy[1] - clipboard_pos[1]
      else:
        dx, dy = 20, 20
      # the same trick as in reading of files
      self.onread_id_sandbox_activate()

      os = []
      for p in clipboard.childNodes:
        o = self.add_object_from_package( p)
        os.append( o)
        o.draw()
        o.move( dx, dy)
        if o.object_type == 'molecule':
          self.select( o)
        elif o.object_type == 'arrow':
          self.select( o.points)
        else:
          self.select( [o])
      self.add_bindings()
      Store.log( _("pasted from clipboard"))

      # put the id_manager back
      self.onread_id_sandbox_finish( apply_to=os)
      self.handle_overlap()
      self.start_new_undo_record()
      




  def add_object_from_package( self, package):
    if package.nodeName == 'molecule':
      o = molecule( self, package=package)
    elif package.nodeName == 'arrow':
      o = arrow.arrow( self, package=package)
    elif package.nodeName == 'plus':
      o = classes.plus( self, package=package)
    elif package.nodeName == 'text':
      o = classes.text( self, package=package)
    elif package.nodeName == 'rect':
      o = graphics.rect( self, package=package)
    elif package.nodeName == 'oval':
      o = graphics.oval( self, package=package)
    elif package.nodeName == 'square':
      o = graphics.square( self, package=package)
    elif package.nodeName == 'circle':
      o = graphics.circle( self, package=package)
    elif package.nodeName == 'polygon':
      o = graphics.polygon( self, package=package)
    elif package.nodeName == 'polyline':
      o = graphics.polyline( self, package=package)
    elif package.nodeName == 'reaction':
      react = reaction()
      react.read_package( package)
      if react.arrows:
        react.arrows[0].reaction = react
      o = None
    else:
      o = None
    if o:
      self.stack.append( o)
    return o
    




  def align_selected( self, mode):
    """aligns selected items according to mode - t=top, b=bottom,
    l=left, r=right, h=horizontal center, v=vertical center"""
    # locate all selected top_levels, filter them to be unique
    to_align, unique = self.selected_to_unique_top_levels()
    # check if there is anything to align
    if len( to_align) < 2:
      return None
    bboxes = []
    if not unique:
      # if not unique align is done according to bboxes of top_levels
      for o in to_align:
        bboxes.extend( o.bbox())
    else:
      # otherwise align according to bboxes of items
      for o in self.selected:
        if o.object_type == 'atom':
          if o.show:
            bboxes.extend( o.ftext.bbox())
          else:
            x, y = o.get_xy()
            bboxes.extend( (x,y,x,y))
        elif o.object_type == 'point':
          x, y = o.get_xy()
          bboxes.extend( (x,y,x,y))
        elif o.object_type == 'bond':
          x1, y1, x2, y2 = o.bbox()
          x = (x1+x2)/2
          y = (y1+y2)/2
          bboxes.extend( (x,y,x,y))
        else:
          bboxes.extend( o.bbox())
    # now the align itself
    # modes dealing with x
    if mode in 'lrv':
      if mode == 'l':
        xs = [bboxes[i] for i in range( 0, len( bboxes), 4)] 
        x = min( xs)
      elif mode == 'r':
        xs = [bboxes[i] for i in range( 2, len( bboxes), 4)] 
        x = max( xs)
      else:
        xmaxs = [bboxes[i] for i in range( 0, len( bboxes), 4)] 
        xmins = [bboxes[i] for i in range( 2, len( bboxes), 4)]
        xs = map( operator.add, xmaxs, xmins)
        xs = map( operator.div, xs, len(xs)*[2])
        x = (max( xs) + min( xs)) / 2 # reduce( operator.add, xs) / len( xs) # this makes mean value rather then center 
      for i in range( len( xs)):
        to_align[i].move( x-xs[i], 0)
    # modes dealing with y
    elif mode in 'tbh':
      if mode == 'b':
        ys = [bboxes[i] for i in range( 3, len( bboxes), 4)] 
        y = max( ys)
      elif mode == 't':
        ys = [bboxes[i] for i in range( 1, len( bboxes), 4)] 
        y = min( ys)
      else:
        ymaxs = [bboxes[i] for i in range( 1, len( bboxes), 4)] 
        ymins = [bboxes[i] for i in range( 3, len( bboxes), 4)]
        ys = map( operator.add, ymaxs, ymins)
        ys = map( operator.div, ys, len(ys)*[2])
        y = (max( ys) + min( ys)) /2 # reduce( operator.add, ys) / len( ys) 
      for i in range( len( ys)):
        to_align[i].move( 0, y-ys[i])
    self.start_new_undo_record()


  def place_next_to_selected( self, mode, align, dist, obj):
    """Places an object (obj) in a distance (dist) next to the selection,
    by changing the x or the y value of the object according to the mode.
    Modes: l= left r=right a=above b=below
    Align: t=top b=bottom l=left r=right h=horizontal v=vertical
    align or mode can be set to "" to use only one function"""
    # locate all selected top_levels, filter them to be unique
    cp, unique = self.selected_to_unique_top_levels()
    # now find center of bbox of all objects in cp
    self.place_next_to_bbox( mode, align, dist, obj, self.common_bbox( cp))
    self.start_new_undo_record()



  def place_next_to_bbox( self, mode, align, dist, obj, bbox):
    """Places an object (obj) in a distance (dist) next to the bbox,
    by changing the x or the y value of the object according to the mode.
    Modes: l= left r=right a=above b=below
    Align: t=top b=bottom l=left r=right h=horizontal v=vertical
    align or mode can be set to "" to use only one function"""
    # now find center of bbox of all objects in cp
    xmin, ymin, xmax, ymax = bbox
    x1o,y1o,x2o,y2o = obj.bbox()
    if mode == "l":
        obj.move(xmin-x2o-dist, 0)
    elif mode == "r":
        obj.move(xmax-x1o+dist, 0)
    elif mode == "b":
        obj.move(0, ymax-y1o+dist)
    elif mode == "a":
        obj.move(0, ymin-y2o-dist)
    if align == "t":
        obj.move (0,ymin-y1o)
    elif align == "b":
        obj.move (0,ymax-y2o)
    elif align == "l":
        obj.move (xmin-x1o,0)
    elif align == "r":
        obj.move (xmax-x2o,0)
    elif align == "v":
        obj.move ((xmax+xmin)/2-(x1o+x2o)/2,0)
    elif align == "h":
        obj.move (0,(ymax+ymin)/2-(y1o+y2o)/2)



  def toggle_center_for_selected( self):
    for o in self.selected:
      if o.object_type == 'atom' and o.show:
        o.toggle_center()





  def selected_to_unique_top_levels( self):
    """maps all items in self.selected to their top_levels (atoms->molecule etc.),
    filters them to be unique and returns tuple of (unique_top_levels, unique)
    where unique is true when there was only one item from each container"""
    filtrate = []
    unique = 1
    for o in self.selected:
      if o.object_type == 'atom' or o.object_type == 'bond':
        if o.molecule not in filtrate:
          filtrate.append( o.molecule)
        else:
          unique = 0
      elif o.object_type == 'point':
        if o.arrow not in filtrate:
          filtrate.append( o.arrow)
        else:
          unique = 0
      else:
        if o not in filtrate:
          filtrate.append( o)
        else:
          unique = 0
    return (filtrate, unique)
          




  def undo( self):
    self.unselect_all()
    i = self.um.undo()
    self.changes_made = 1
    if i > 0:
      Store.log(ngettext("undo (%d further undo available)",
                         "undo (%d further undos available)",
                         i) % i)
    else:
      Store.log( _("no further undo"))
    self.event_generate( "<<undo>>")    




  def redo( self):
    self.unselect_all()
    i = self.um.redo()
    self.changes_made = 1
    if i > 0:
      Store.log(ngettext("redo (%d further redo available)",
                         "redo (%d further redos available)",
                         i) % i)
    else:
      Store.log( _("no further redo"))
    self.event_generate( "<<redo>>")
    




  def scale_selected( self, ratio_x, ratio_y, scale_font=1, fix_centers=0, scale_bond_width=False):
    top_levels, unique = self.selected_to_unique_top_levels()
    ratio = math.sqrt( ratio_x*ratio_y) # ratio for operations where x and y can't be distinguished (font size etc.)
    tr = transform()
    tr.set_scaling_xy( ratio_x, ratio_y)
    for o in top_levels:
      if fix_centers:
        bbox = o.bbox()
        x0 = (bbox[0] + bbox[2])/2
        y0 = (bbox[1] + bbox[3])/2
      self.scale_object( o, tr, ratio, scale_font=scale_font, scale_bond_width=scale_bond_width)
      if fix_centers:
        self.center_object( o, x0, y0)

    # the final things
    if top_levels:
      self.add_bindings()
      self.start_new_undo_record()



  def scale_object( self, o, tr, ratio, scale_font=1, scale_bond_width=False):
    """scale_font now also refers to scaling of marks"""
    if o.object_type == 'molecule':
      o.transform( tr)
      if scale_font:
        [i.scale_font( ratio) for i in o.atoms]
        [i.redraw() for i in o.atoms if i.show]
      if scale_font:
        for a in o.atoms:
          for m in a.marks:
            m.size *= ratio
            m.redraw()
      if scale_bond_width:
        for e in o.edges:
          e.bond_width *= ratio
          e.redraw()
      for frag in o.fragments:
        if frag.type == "linear_form":
          frag.properties['bond_length'] = round( frag.properties['bond_length'] * ratio)
          o.check_linear_form_fragment( frag)
    if o.object_type in ('arrow','polygon','polyline'):
      for i in o.points:
        x, y = tr.transform_xy( i.x, i.y)
        i.move_to( x, y)
      o.redraw()
    if o.object_type == 'text':
      x, y = tr.transform_xy( o.x, o.y)
      o.move_to( x, y)
      if scale_font:
        o.scale_font( ratio)
      o.redraw()
    if o.object_type == 'plus':
      x, y = tr.transform_xy( o.x, o.y)
      o.move_to( x, y)
      if scale_font:
        o.scale_font( ratio)
      o.redraw()
    elif o.object_type in ('rect', 'oval'):
      coords = tr.transform_4( o.coords)
      o.resize( coords)
      o.redraw()
      o.unselect()
      o.select()






  def selected_to_real_clipboard_as_SVG( self):
    """exports selected top_levels as SVG to system clipboard"""
    cont, unique = self.selected_to_unique_top_levels()
    exporter = xml_writer.SVG_writer( self)
    exporter.full_size = False
    exporter.construct_dom_tree( cont)
    self.clipboard_clear()
    xml = exporter.get_nicely_formated_document()
    first_line = xml.splitlines()[0]
    if first_line.startswith("<?") and first_line.endswith("?>"):
      xml = "\n".join( xml.splitlines()[1:])
    self.clipboard_append( xml)
    Store.log( _("selected top_levels were exported to clipboard in SVG"))


  def selected_to_real_clipboard_as_image( self):
    """exports selected top_levels as high resolution PNG to system clipboard"""
    cont, unique = self.selected_to_unique_top_levels()
    if not cont:
      return

    try:
      import cairo
      from .plugins.tk2cairo import tk2cairo
      from .oasa import transform
      import win32clipboard
      import io
    except ImportError as e:
      Store.log( _("Missing dependency for image export: %s") % str(e), message_type="error")
      return

    temp_tag = "no_export_temp"

    # Identify items to export and find bounding box
    bboxes = []
    all_items = self.find_all()

    valid_items = set()
    def collect_items(o):
      if not o: return
      if isinstance(o, (int, str)):
        valid_items.add(o)
        return
      if hasattr(o, 'item') and o.item: valid_items.add(o.item)
      if hasattr(o, 'items') and o.items:
        for i in o.items: collect_items(i)
      if hasattr(o, 'second') and o.second:
        for i in o.second: collect_items(i)
      if hasattr(o, 'third') and o.third:
        for i in o.third: collect_items(i)
      if hasattr(o, 'ftext') and o.ftext: collect_items(o.ftext)
      if hasattr(o, 'marks') and o.marks: 
        for m in getattr(o, 'marks', []): collect_items(m)
      if hasattr(o, 'atoms') and o.atoms:
        for a in getattr(o, 'atoms', []): collect_items(a)
      if hasattr(o, 'bonds') and o.bonds:
        for b in getattr(o, 'bonds', []): collect_items(b)
      if hasattr(o, 'points') and o.points:
        for p in getattr(o, 'points', []): collect_items(p)
      if hasattr(o, 'lines') and o.lines:
        for l in getattr(o, 'lines', []): collect_items(l)
      if hasattr(o, 'polygon') and o.polygon:
        collect_items(o.polygon)

    for top in cont:
      collect_items(top)
    
    for item in all_items:
      obj = self.id_to_object(item)
      is_valid = False
      if item in valid_items:
        is_valid = True
      elif obj:
        top = obj
        if hasattr(obj, 'molecule') and obj.molecule:
          top = obj.molecule
        elif hasattr(obj, 'arrow') and obj.arrow:
          top = obj.arrow
        elif hasattr(obj, 'reaction') and obj.reaction:
          top = obj.reaction
          
        if top in cont:
          is_valid = True

      if is_valid:
        bboxes.extend(self.bbox(item))
      else:
        # non-bkchem items (like selection rects) should be ignored
        if "no_export" not in self.gettags(item):
          self.addtag_withtag(temp_tag, item)
          self.addtag_withtag("no_export", item)

    if not bboxes:
      # Clear tags and return
      for item in self.find_withtag(temp_tag):
        self.dtag(item, "no_export")
        self.dtag(item, temp_tag)
      return

    x1, y1, x2, y2 = min(bboxes[0::4]), min(bboxes[1::4]), max(bboxes[2::4]), max(bboxes[3::4])
    
    margin = 20
    x1 -= margin; y1 -= margin; x2 += margin; y2 += margin
    dx = x2 - x1
    dy = y2 - y1

    import tkinter.simpledialog
    dpi = tkinter.simpledialog.askinteger(_("Image Resolution"), _("Enter DPI for the exported image:"), initialvalue=300, minvalue=50, maxvalue=3600, parent=self)
    if not dpi:
      for item in self.find_withtag(temp_tag):
        self.dtag(item, "no_export")
        self.dtag(item, temp_tag)
      return
      
    from .singleton_store import Screen
    scale = float(dpi) / Screen.dpi

    tr = transform.transform()
    tr.set_move(-x1, -y1)
    tr.set_scaling_xy(scale, scale)

    w, h = int(dx * scale), int(dy * scale)
    if w <= 0 or h <= 0:
      for item in self.find_withtag(temp_tag):
        self.dtag(item, "no_export")
        self.dtag(item, temp_tag)
      return

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    context = cairo.Context(surface)
    # Transparent background
    context.set_source_rgba(0, 0, 0, 0)
    context.set_operator(cairo.OPERATOR_SOURCE)
    context.paint()
    context.set_operator(cairo.OPERATOR_OVER)

    converter = tk2cairo(text_to_curves=False)
    converter.export_to_cairo(self, context, transformer=tr)

    for item in self.find_withtag(temp_tag):
      self.dtag(item, "no_export")
      self.dtag(item, temp_tag)

    output = io.BytesIO()
    surface.write_to_png(output)
    surface.finish()
    png_data = output.getvalue()

    try:
      win32clipboard.OpenClipboard()
      win32clipboard.EmptyClipboard()
      png_format = win32clipboard.RegisterClipboardFormat("PNG")
      win32clipboard.SetClipboardData(png_format, png_data)
      win32clipboard.CloseClipboard()
      Store.log(_("selected top_levels were exported to clipboard as high-res image"))
    except Exception as e:
      Store.log(_("Failed to write image to clipboard: %s") % str(e), message_type="error")





  def start_new_undo_record( self, name=''):
    if name != "arrow-key-move":
      self.before_undo_record()
    if not self.changes_made:
      self.changes_made = 1
    self.um.start_new_record( name=name)
    self.after_undo_record()


  def before_undo_record( self):
    """this method is place where periodical checks and other things that should be done before
    undo is recorded should be done"""
    checks.check_linear_fragments( self)

  def after_undo_record( self):
    """similar to before_undo_record but is run after the undo was recorded"""
    # check the bbox to see if we need to update scroll region
    if not hasattr( self, "_old_bbox"):
      self._old_bbox = self.bbox(ALL)
      self.update_scrollregion()
    else:
      _bbox = self.bbox(ALL)
      if _bbox != self._old_bbox:
        self.update_scrollregion()


  def display_weight_of_selected( self):
    s_mols = [m for m in self.selected_to_unique_top_levels()[0] if m.object_type == 'molecule']
    w = 0
    for m in s_mols:
      w += m.get_formula_dict().get_molecular_weight()
    Store.app.update_status( str( w))



  def display_info_on_selected( self):
    s_mols = [m for m in self.selected_to_unique_top_levels()[0] if m.object_type == 'molecule']
    if not s_mols:
      return

    dialog = Pmw.TextDialog( self, title=_("Info on selected molecules"), defaultbutton=0)
    dialog.withdraw()

    ws = 0
    comps = PT.formula_dict()
    for m in s_mols:
      comp = m.get_formula_dict()
      comps += comp
      dialog.insert( 'end', _("Name: %s") % m.name)
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Id: %s") % m.id)
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Formula: %s") % comp)
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Weight: %4.4f") % comp.get_molecular_weight())
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Monoisotopic mass: %12.8f") % comp.get_exact_molecular_mass())
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Composition: %s") % PT.dict_to_composition( comp))
      dialog.insert( 'end', "\n\n")
    if len( s_mols) > 1:
      dialog.insert( '1.0', "\n")
      dialog.insert( "1.0", _("Individual molecules:"), 'headline')
      dialog.insert( '1.end', "\n")      
      dialog.insert( 'end', "\n")
      dialog.insert( "end", _("Summary for all selected molecules:"), 'headline')
      dialog.insert( 'end', "\n\n")
      dialog.insert( "end", _("Formula: %s") % comps)
      dialog.insert( 'end', "\n")
      dialog.insert( "end", _("Weight: %4.4f") % comps.get_molecular_weight())
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Monoisotopic mass: %12.8f") % comps.get_exact_molecular_mass())
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Composition: %s") % PT.dict_to_composition( comps))
    dialog.tag_config( 'headline', underline=1)
    dialog.activate()






  def check_chemistry_of_selected( self):
    from . import validator
    val = validator.validator()
    s_mols = [m for m in self.selected_to_unique_top_levels()[0] if m.object_type == 'molecule']
    if not s_mols:
      return

    dialog = Pmw.TextDialog( self, title=_("Chemistry check of selected molecules"), defaultbutton=0)
    dialog.withdraw()

    val.validate( s_mols)
    dialog.insert( 'end', val.report.get_summary())

    dialog.activate()






  def select_all( self):
    self.unselect_all()
    self.select( [o for o in map( self.id_to_object, self.find_all()) if o and hasattr( o, 'select') and o.object_type != 'arrow']) 
    self.add_bindings()
    




  def set_viewport( self, view=(0,0,640,480)):
    x1, y1, x2, y2 = view
    self._view = tuple( view)
    
    self._real2screen = transform()
    self._real2screen.set_move( -x1, -y1)
    ratiox, ratioy = 640/(x2-x1), 480/(y2-y1)
    self._real2screen.set_scaling_xy( ratiox, ratioy)
    self._ratio = math.sqrt( ratioy*ratiox)

    self._screen2real = transform()
    ratiox, ratioy = (x2-x1)/640, (y2-y1)/480
    self._screen2real.set_scaling_xy( ratiox, ratioy)
    self._screen2real.set_move( x1, y1)
  




  def screen_to_real_coords( self, coords):
    """transforms set of x,y coordinates to real coordinates, input list must have even length"""
    if len( coords) % 2:
      raise ValueError("only even number of coordinates could be transformed")
    out = []
    for i in range( 0, len( coords), 2):
      out.extend( self._screen2real.transform_xy( coords[i], coords[i+1]))
    return out





  def real_to_screen_coords( self, coords):
    """transforms set of x,y coordinates to screen coordinates, input list must have even length"""
    if len( coords) % 2:
      raise ValueError("only even number of coordinates could be transformed")
    out = []
    for i in range( 0, len( coords), 2):
      out.extend( self._real2screen.transform_xy( coords[i], coords[i+1]))
    return out





  def screen_to_real_ratio( self):
    return 1.0/self._ratio





  def real_to_screen_ratio( self):
    return self._ratio





  def expand_groups( self, selected=1):
    """expands groups, if selected==1 only for selected, otherwise for all"""
    if selected:
      mols = [o for o in self.selected_to_unique_top_levels()[0] if o.object_type == 'molecule']
      atoms = [o for o in self.selected if isinstance( o, group)]
      self.unselect_all()
      for mol in mols:
        this_atoms = misc.intersection( atoms, mol.atoms)
        mol.expand_groups( atoms = this_atoms)
    else:
      self.unselect_all()
      [m.expand_groups() for m in self.molecules]
    self.add_bindings()
    self.start_new_undo_record()





  def lift_selected_to_top( self):
    os = self.selected_to_unique_top_levels()[0]
    for o in os:
      self.stack.remove( o)
      self.stack.append( o)
    Store.log( _("selected items were lifted"))
    self.add_bindings()
    self.start_new_undo_record()





  def lower_selected_to_bottom( self):
    os = self.selected_to_unique_top_levels()[0]
    for o in os:
      self.stack.remove( o)
      self.stack.insert( 0, o)
    Store.log( _("selected items were put back"))
    self.add_bindings()
    self.start_new_undo_record()





  def swap_selected_on_stack( self):
    os = self.selected_to_unique_top_levels()[0]
    indxs = [self.stack.index( o) for o in os]
    indxs.sort()
    for i in range( len( indxs) // 2):
      self.stack[ indxs[i]], self.stack[ indxs[-1-i]] =  self.stack[ indxs[-1-i]], self.stack[ indxs[i]]
    Store.log( _("selected items were swapped"))
    self.add_bindings()
    self.start_new_undo_record()





  def _open_debug_console( self):
    m = Store.app.mode
    for i in m.__dict__:
      print(i, ' : ', m.__dict__[i])






  def any_color_to_rgb_string( self, color):
    if not color:
      return "none"
    else:
      r, g, b = map( lambda x: (x < 256 and x) or (x >= 256 and x//256),  self.winfo_rgb( color))
      return "#%02x%02x%02x" % (r,g,b)
  


  def set_default_paper_properties( self):
    t = self.standard.paper_type
    o = self.standard.paper_orientation
    if o == 'portrait':
      sy, sx = data.paper_types[t]
    else:
      sx, sy = data.paper_types[t]

    self._paper_properties = {'type': t,
                              'orientation': o,
                              'size_x': sx,
                              'size_y': sy}
                              
    if not 'background' in self.__dict__ or not self.background:
      self.background = self.create_rectangle( 0, 0, '%dm'%sx, '%dm'%sy, fill='white', outline='black', tags="no_export")
    else:
      self.coords( self.background, 0, 0, '%dm'%sx, '%dm'%sy)

    # crop svg
    self._paper_properties['crop_svg'] = self.standard.paper_crop_svg
    # crop margin
    self._paper_properties['crop_margin'] = self.standard.paper_crop_margin
    self._paper_properties['use_real_minus'] = Store.pm.get_preference( "use_real_minus") or 0
    self._paper_properties['replace_minus'] = Store.pm.get_preference( "replace_minus") or 0
    self.update_scrollregion()

    

  def create_background( self):
    sx = self._paper_properties['size_x']
    sy = self._paper_properties['size_y']

    if not 'background' in self.__dict__ or not self.background:
      self.background = self.create_rectangle( 0, 0, '%dm'%sx, '%dm'%sy, fill='white', outline='black', tags="no_export")
    else:
      self.coords( self.background, 0, 0, '%dm'%sx, '%dm'%sy)
    


  def set_paper_properties( self, type=None, orientation=None, x=None, y=None, crop_svg=None, all=None, crop_margin=None, use_real_minus=None, replace_minus=None):
    if all:
      self._paper_properties = copy.copy( all)
      return
    if type:
      if type != 'custom':
        t = type or self.standard.paper_type
        o = orientation or self.standard.paper_orientation
        if o == 'portrait':
          sy, sx = data.paper_types[t]
        else:
          sx, sy = data.paper_types[t]
      else:
        t = 'custom'
        o = orientation or self._paper_properties['orientation']
        sx, sy = x, y
      self._paper_properties['type'] = t
      self._paper_properties['orientation'] = o
      self._paper_properties['size_x'] = sx
      self._paper_properties['size_y'] = sy
                              
    # crop svg
    if crop_svg != None:
      self._paper_properties['crop_svg'] = crop_svg

    if crop_margin != None:
      self._paper_properties['crop_margin'] = crop_margin

    if use_real_minus != None:
      old = 'use_real_minus' in self._paper_properties and self._paper_properties['use_real_minus'] or 0
      self._paper_properties['use_real_minus'] = use_real_minus
      if old != use_real_minus:
        [i.redraw() for i in self.stack]

    if replace_minus != None:
      self._paper_properties['replace_minus'] = replace_minus

    self.create_background()
    self.update_scrollregion()


  def update_scrollregion( self):
    x1,y1,x2,y2 = self.bbox(ALL)
    self.config( scrollregion=(x1-100,y1-100,x2+100,y2+100))



  def get_paper_property( self, name):
    if name in self._paper_properties:
      return self._paper_properties[ name]
    else:
      return None



    
## def coords( self, item, *args, **keyargs):
##     if 'unit' in keyargs:
##       u = keyargs['unit']
##       if u == 'cm':
##         if args:
##           return map( self.px_to_cm, Canvas.coords( self, item, args))
##         else:
##           return map( self.px_to_cm, Canvas.coords( self, item))
##     if args:
##       return Canvas.coords( self, item, *args)
##     else:
##       return Canvas.coords( self, item)





  def read_standard_from_dom( self, d):
    std = dom_extensions.getFirstChildNamed( d, 'standard')
    if std:
      st = classes.standard()
      st.read_package( std)
      return st
    return None





  def apply_current_standard( self, objects=[], old_standard=None, template_mode=0):
    """if no objects are given all are used, if old_standard is given only the values
    that have changed are applied; in template mode no changes of paper format are made"""
    if not template_mode:
      self.create_background()
    objs = objects or self.top_levels
    to_redraw = []
    st = self.standard
    for m in objs:
      if m.object_type == 'molecule':
        for b in m.bonds:
          b.read_standard_values( self.standard, old_standard=old_standard)
          to_redraw.append( b)
        for a in m.atoms:
          a.read_standard_values( self.standard, old_standard=old_standard)
          to_redraw.append( a)
      elif m.object_type != "point":
        m.read_standard_values( self.standard, old_standard=old_standard)
        to_redraw.append( m)
    return to_redraw
          




  def get_personal_standard( self):
    name = os_support.get_config_filename( 'standard.cdml', level="personal", mode="r")
    if name:
      try:
        cdml = dom.parse( name).childNodes[0]
      except:
        return classes.standard()
      return self.read_standard_from_dom( cdml)
    return classes.standard()





  def save_personal_standard( self, st):
    name = os_support.get_config_filename( 'standard.cdml', level="personal", mode="w")
    if name:
      doc = dom.Document()
      root = dom_extensions.elementUnder( doc, 'cdml', attributes = (('version', config.current_CDML_version),
                                                                     ( 'xmlns', data.cdml_namespace)))
      info = dom_extensions.elementUnder( root, 'info')
      dom_extensions.textOnlyElementUnder( info, 'author_program', 'BKChem', attributes = (('version',config.current_BKChem_version),))
      root.appendChild( st.get_package( doc))
      dom_extensions.safe_indent( root)
      try:
        f = file( name, 'w')
      except IOError:
        return 0
      try:
        f.write( doc.toxml().encode('utf-8'))
      except IOError:
        f.close()
        return 0
      f.close()
      return name
    return 0






  def swap_sides_of_selected( self, mode="vertical"):
    """mirrors the selected things, vertical uses y-axis as a mirror plane,
    horizontal x-axis"""
    # locate all selected top_levels, filter them to be unique
    to_align, unique = self.selected_to_unique_top_levels()
    to_select_then = copy.copy( self.selected)
    self.unselect_all()
    # check if there is anything to align
    if len( to_align) < 1:
      return None
    bboxes = []
    for o in to_align:
      bboxes.extend( o.bbox())
    # vertical (rotate around y axis)
    if mode == 'vertical':
      xs = [bboxes[i] for i in range( 0, len( bboxes), 2)]
      x0 = (max( xs) + min( xs)) / 2.0
      for o in to_align:
        if o.object_type == 'molecule':
          tr = transform()
          tr.set_move( -x0, 0)
          tr.set_scaling_xy( -1, 1)
          tr.set_move( x0, 0)
          o.transform( tr)
        else:
          pass
    # horizontal (rotate around x axis)
    if mode == 'horizontal':
      ys = [bboxes[i] for i in range( 1, len( bboxes), 2)]
      y0 = (max( ys) + min( ys)) / 2.0
      for o in to_align:
        if o.object_type == 'molecule':
          tr = transform()
          tr.set_move( 0, -y0)
          tr.set_scaling_xy( 1, -1)
          tr.set_move( 0, y0)
          o.transform( tr)
        else:
          pass

    self.select( to_select_then)
    self.add_bindings()
    self.start_new_undo_record()






  def flush_first_selected_mol_to_graph_file( self):
    mols, u = self.selected_to_unique_top_levels()
    for m in mols:
      if m in self.molecules:
        m.flush_graph_to_file()
        return
    




  def config_selected( self):
    if self.selected:
      dialog = dialogs.config_dialog( Store.app, self.selected[:])
      if dialog.changes_made:
        self.start_new_undo_record()
      self.add_bindings()





  def get_base_name( self):
    return os.path.splitext( self.file_name['name'])[0]






  def _get_full_path( self):
    return os.path.abspath( os.path.join( self.file_name['dir'], self.file_name['name']))

  full_path = property( _get_full_path)
    




  def _get_window_name( self):
    return self.create_window_name( self.file_name)

  window_name = property( _get_window_name)




  def create_window_name( name_dict):
    if name_dict['ord'] == 0:
      return name_dict['name']
    else:
      return name_dict['name'] + '<%d>' % name_dict['ord']
    
  create_window_name = staticmethod( create_window_name)



  def clean_selected( self):
    """cleans the geomerty of all selected molecules, the position of atoms that are selected will not be changed.
    The selection must define a continuos subgraph of the molecule(s) otherwise the coords generation would not be possible,
    at least two atoms (one bond) must be selected for the program to give some meaningfull result"""
    # normalization of selection
    for item in self.selected:
      if item.object_type == 'bond':
        for a in item.atoms:
          if a not in self.selected:
            self.select( [a])

    mols, u = self.selected_to_unique_top_levels()
    for mol in mols:
      if isinstance( mol, molecule):
        notselected = set( mol.atoms) - set( self.selected)
        selected = set( mol.atoms) & set( self.selected)
        # we must check if the selection defines one connected subgraph of the molecule
        # otherwise the coordinate generation will not work
        if len( selected) == 1:
          print("sorry, but the selection must contain at least two atoms (one bond)")
          return
        else:
          sub = mol.get_new_induced_subgraph( selected, mol.vertex_subgraph_to_edge_subgraph( selected))
          subs = [comp for comp in sub.get_connected_components()]
          if len( subs) != 1:
            print("sorry, but the selection must define a continuos block in the molecule")
            return

        # now we check what has been selected
        side = None
        if len( selected) == 2:
          # if only two atoms are selected we need the information about positioning to guess
          # how to mirror the molecule at the end
          atom1, atom2 = selected
          side = sum( [geometry.on_which_side_is_point( (atom1.x, atom1.y, atom2.x, atom2.y), (a.x,a.y)) for a in notselected])
          
        for a in notselected:
          a.x = None
          a.y = None
          
        oasa.coords_generator.calculate_coords( mol, force=0, bond_length=-1)

        if len( selected) == 2:
          side2 = sum( [geometry.on_which_side_is_point( (atom1.x, atom1.y, atom2.x, atom2.y), (a.x,a.y)) for a in notselected])
          if side * side2 < 0:
            x1, y1, x2, y2 = (atom1.x, atom1.y, atom2.x, atom2.y)
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

            mol.transform( tr)

      mol.redraw( reposition_double=1)
      self.start_new_undo_record()


  def get_cropping_bbox( self):
    if hasattr( self, '_cropping_bbox') and self._cropping_bbox:
      return self._cropping_bbox
      
    margin = self.get_paper_property('crop_margin')
    items = list( self.find_all())
    items.remove( self.background)

    if not items:
      return None

    x1, y1, x2, y2 = self.list_bbox( items)
    return x1-margin, y1-margin, x2+margin, y2+margin



  def set_cropping_bbox( self, coords):
    self._cropping_bbox = coords
    

  def fix_current_cropping_bbox( self):
    self.set_cropping_bbox( self.get_cropping_bbox())


  def center_object( self, obj, x, y):
    """moves an object so that its centered on coordinates x,y"""
    x1, y1, x2, y2 = obj.bbox()
    dx = x2 - x1
    dy = y2 - y1
    obj.move( x-x1-dx/2.0, y-y1-dy/2.0)


  def center_objects( self, objs, x, y):
    """moves a set of objects so that the center of the group is placed on coordinates x,y"""
    x1, y1, x2, y2 = self.common_bbox( objs)
    dx = x2 - x1
    dy = y2 - y1
    for obj in objs:
      obj.move( x-x1-dx/2.0, y-y1-dy/2.0)


  def common_bbox( self, objects):
    """returns the bbox of all 'objects', in contrast to list_bbox it works with BKChem
    objects, not Tkinter canvas objects"""
    if not objects:
      return None
    xmin, ymin, xmax, ymax = objects[0].bbox()
    for o in objects[:]:
      x0, y0, x1, y1 = o.bbox()
    if x0 < xmin:
      xmin = x0
    if y0 < ymin:
      ymin = y0
    if x1 > xmax:
      xmax = x1
    if ymax < y1:
      ymax = y1
    return xmin, ymin, xmax, ymax


  def zoom_at_point( self, x, y, scale_factor):
    """Zoom in/out around a specific point (e.g., mouse cursor).
    
    This method scales all objects on the paper while keeping the point (x,y) 
    stationary, so molecules don't jump around during zoom.
    
    Args:
      x, y: The point to zoom around (typically mouse cursor position)
      scale_factor: Scale multiplier (>1 for zoom in, <1 for zoom out)
    """
    from bkchem.oasa.oasa.transform import transform
    tr = transform()
    # First translate the point to origin, then scale, then translate back
    tr.set_move( -x, -y)
    tr.set_scaling_xy( scale_factor, scale_factor)
    tr.set_move( x, y)
    
    # Scale all objects on the paper
    for o in self.stack:
      self.scale_object( o, tr, scale_factor, scale_font=1, scale_bond_width=False)
    
    # Refresh the display
    self.add_bindings()
    self.start_new_undo_record()


  def _on_mousewheel( self, event):
    """Handle mouse wheel events for zooming in/out around cursor position."""
    # Get mouse position on canvas
    x = self.canvasx( event.x)
    y = self.canvasy( event.y)
    
    # Determine zoom direction and factor
    # event.delta is typically 120 for zoom in, -120 for zoom out on Windows
    # On Linux with Button-4/5, we use different logic
    if hasattr( event, 'delta') and event.delta:
      # Windows/Mac style
      if event.delta > 0:
        scale_factor = 1.1  # Zoom in
      else:
        scale_factor = 0.9  # Zoom out
    else:
      # Linux style (Button-4 = zoom in, Button-5 = zoom out)
      # This is handled by which binding triggered the event
      return  # Let the specific bindings handle this
    
    self.zoom_at_point( x, y, scale_factor)


  def _on_zoom_in( self, event):
    """Handle zoom in request (e.g., Button-4 on Linux)."""
    x = self.canvasx( event.x)
    y = self.canvasy( event.y)
    self.zoom_at_point( x, y, 1.1)  # 10% zoom in


  def _on_zoom_out( self, event):
    """Handle zoom out request (e.g., Button-5 on Linux)."""
    x = self.canvasx( event.x)
    y = self.canvasy( event.y)
    self.zoom_at_point( x, y, 0.9)  # 10% zoom out
  
