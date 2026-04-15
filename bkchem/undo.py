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

"""this module implements undo_manager and state_record classes,
should provide everything needed to perform undo management.
state_record is used only inside of undo_manager and is not
exported in __all__."""

## NOTE that undo uses a low-level access to objects in order to
## speed up the task.

from . import misc
import copy
import functools
pass  # types wildcard removed  #should be safe

import inspect

__all__= ['undo_manager']

##-------------------- UNDO MANAGER --------------------

class undo_manager:
  """class to process requests for undo tracking and undoing"""

  MAX_RECORDS = 100
  
  def __init__( self, paper):
    """well, init"""
    self.paper = paper
    self._records = []
    self.clean()
    self.start_new_record()
    
  def start_new_record( self, name=''):
    """starts new undo_record closing the recent
    name may be set for a record"""
    if len( self._records)-1 > self._pos:
      del self._records[ (self._pos+1):]
    if len( self._records) >= self.MAX_RECORDS:
      del self._records[0]
      self._pos -= 1
    self._records.append( state_record( self.paper, name=name))
    self._pos += 1

  def undo( self):
    """undoes the last step and returns the number of undo records available"""
    self._pos -= 1
    if self._pos >= 0:
      self._records[ self._pos].undo( self._records[ self._pos+1])
    else:
      self._pos = 0
    return self._pos

  def redo( self):
    """redoes the last undone step, returns number of redos available"""
    self._pos += 1
    if self._pos < len( self._records):
      self._records[ self._pos].undo( self._records[ self._pos-1])
    else:
      self._pos = len( self._records)-1
    return len( self._records) - self._pos -1

  def clean( self):
    """removes all undo informations, does not start new undo record"""
    self._pos = -1
    for record in self._records:
      record.clean()
    del self._records
    self._records = []


  def mrproper( self):
    self.clean()
    del self.paper
    del self._records


  def get_last_record_name( self):
    """returns the last closed record name"""
    if self._pos >= 1:
      return self._records[ self._pos-1].name
    else:
      return None

  def delete_last_record( self):
    """deletes the last record, useful for concatenation of several records to one;
    especially powerfull in combination with named records;
    use with care - it could cause problems"""
    if self._pos > 0:
      del self._records[ self._pos-1]
      self._pos -= 1

  def get_number_of_records( self):
    return len( self._records)
  

  def can_undo( self):
    return bool( self._pos)

  def can_redo( self):
    return bool( self.get_number_of_records() - self._pos - 1)


  def compare_records( self, o, state_rec1, state_rec2):
    """returns True if the object o changed between ref1 and ref2"""
    x1 = o in state_rec1.objects
    x2 = o in state_rec2.objects
    if (x1 and not x2) or (x2 and not x1):
      # one record does not have o
      return False
    if not x1 and not x2:
      # no record has o - they are the same then
      return True
    rec1 = state_rec1.records[ state_rec1.objects.index( o)]
    rec2 = state_rec2.records[ state_rec2.objects.index( o)]
    for a in o.meta__undo_fake + o.meta__undo_simple + o.meta__undo_properties:
      if rec1[a] != rec2[a]:
        return False
    for a in o.meta__undo_copy:
      if rec1[a] != rec2[a]:
        return False
    # process the chidren
    for a in o.meta__undo_children_to_record:
      obj = getattr( o, a)
      if isinstance( obj, list) or isinstance( obj, set):
        for i in obj:
          if not self.compare_records( i, state_rec1, state_rec2):
            return False
      elif isinstance( obj, dict):
        for i in obj.values():
          if not self.compare_records( i, state_rec1, state_rec2):
            return False
      else:
        if not self.compare_records( obj, state_rec1, state_rec2):
          return False
    return True


  def get_changed_molecules( self):
    rec = self._records[ self._pos]
    ret = []
    for m in self.paper.molecules:
      if rec.object_changed( m):
        ret.append( m)
    return ret

  def get_last_record( self):
    if self._pos >= 1:
      return self._records[ self._pos]
    else:
      return None


##-------------------- STATE RECORD --------------------
    
class state_record:
  """class able to store state of the whole system and then set
  the system back to that stored state"""

  def __init__( self, paper, name=''):
    """hmmm, what is supposed to be in comment for __init__?"""
    self.paper = paper
    self.objects = []
    self.records = []
    self.name = name
    self.stack = []
    self.record_state()


  def clean( self):
    del self.stack
    del self.paper
    del self.objects
    del self.records
    del self.name


  def record_state( self):
    """stores all necessary information about the system, so that its than able to
    fully recover that state."""
    self.stack = copy.copy( self.paper.stack)

    for o in self.paper.top_levels:
      self.record_object( o)


  def record_object( self, o):
    rec = {}
    for a in o.meta__undo_fake:
      rec[a] = getattr( o, a)
    for a in o.meta__undo_simple:
      rec[a] = getattr( o, a)
    for a in o.meta__undo_properties:
      rec[a] = getattr( o, a)
    for a in o.meta__undo_copy:
      rec[a] = copy.copy( o.__dict__[a])
    self.objects.append( o)
    self.records.append( rec)
    # process the chidren
    for a in o.meta__undo_children_to_record:
      obj = getattr( o, a)
      if isinstance( obj, list) or isinstance( obj, set):
        [self.record_object( i) for i in obj]
      elif isinstance( obj, dict):
        [self.record_object( i) for i in obj.values() if i]
      else:
        self.record_object( obj)


  def undo( self, previous):
    """does undo, actually only calls self.set_state"""
    self.set_state( previous)


  def set_state( self, previous):
    """sets the system to the recorded state (update is done only where necessary,
    not changed values are not touched)."""
    # we need to know about deleted bonds before we try to redraw them (when updating atom)
    deleted = misc.difference( self.objects, previous.objects)
    added = misc.difference( previous.objects, self.objects)
    to_redraw = set()
    ## CHANGED OBJECTS
    i = 0
    for o in self.objects:
      changed = 0
      for a in o.meta__undo_fake:
        # fakes serve only to force redraw in some cases however do not perform any undo
        if self.records[i][a] != getattr( o, a):
          changed = 1
      for a in o.meta__undo_simple:
        if self.records[i][a] != o.__dict__[a]:
          o.__dict__[a] = self.records[i][a]
          if a != 'molecule':  # this jumps a little from the clean, meta-driven design, however saves much time
            changed = 1
      for a in o.meta__undo_copy:
        if self.records[i][a] != o.__dict__[a]:
          o.__dict__[a] = copy.copy( self.records[i][a])
          changed = 1
          # this part is not meta driven, I have to rewrite it one day
          if a == 'bonds':
            o.edges = o.bonds
          elif a == 'atoms':
            o.vertices = o.atoms
          # / end of the shitty patch
      for a in o.meta__undo_properties:
        if hasattr( o, a):
          if self.records[i][a] != getattr( o, a):
            setattr( o, a, self.records[i][a])
            changed = 1

      if changed:
        to_redraw.add( o)
        # some hacks needed to ensure complete redraw
        if o.object_type == 'atom':
          neigh_edges = set( [b for b in o.neighbor_edges if b not in deleted and b not in added])
          to_redraw |= neigh_edges
          # neighboring edges of the atoms edges - needed because of new bond drawing code
          # that takes neighboring edges into account
          neigh_edges2 = set()
          for e in neigh_edges:
            neigh_edges2 |= set( [e2 for e2 in e.get_neighbor_edges() if e2 not in added])
          to_redraw |= neigh_edges2
        elif o.object_type == 'bond':
          to_redraw |= set( [a for a in o.get_atoms() if a.show and not a in deleted and not a in added])
        elif o.object_type == 'point':
          to_redraw.add( o)
          to_redraw.add( o.parent)
        elif o.object_type == 'arrow':
          to_redraw.add( o)

      i += 1

    ## DELETED OBJECTS
    # deleted are known from the top of this def
    for o in deleted:
      if o.object_type not in ( 'molecule','mark') and hasattr( o, 'draw'):
        # no_automatic where possible
        if 'automatic' in inspect.getargspec( o.draw)[0]:
          o.draw( automatic = "none")
        else:
          o.draw()
      # hacks to ensure complete redraw
      if o.object_type == 'atom':
        to_redraw |= set( [b for b in o.neighbor_edges if b not in deleted])
      elif o.object_type == 'bond':
        to_redraw |= set( [a for a in o.get_atoms() if a.show and not a in deleted])
      elif o.object_type == 'point':
        to_redraw.add( o)
        to_redraw.add( o.parent)
      elif o.object_type == 'arrow':
        to_redraw.add( o)

    ## ADDED OBJECTS
    # added are known from the top of this def
    for o in added:
      if o.object_type != 'molecule' and hasattr( o, "delete"):
        o.delete()
    # Force canvas update
    if self.paper:
      self.paper.update()
      self.paper.update_idletasks()

    # now redrawing
    # sort the to_redraw
    to_redraw = list( to_redraw)
    to_redraw.sort(key=functools.cmp_to_key(_redraw_sorting))
    for o in to_redraw:
      if o not in deleted and o.object_type != 'molecule' and hasattr(o,'redraw'):
        if hasattr( o, "after_undo"):
          o.after_undo()
        if o.object_type == 'atom':
          o.redraw( suppress_reposition=1)
        else:
          o.redraw()

    self.paper.stack = copy.copy( self.stack)
    self.paper.add_bindings()


  def get_record( self, o):
    if o in self.objects:
      i = self.objects.index(o)
      return self.records[i]
    else:
      return None

  def object_changed( self, o):
    """returns True if the object o differs from the state recorded here"""
    rec = self.get_record( o)
    if rec == None:
      return True
    for a in o.meta__undo_fake + o.meta__undo_simple + o.meta__undo_properties:
      if getattr( o, a) != rec[a]:
        return True
    for a in o.meta__undo_copy:
      if getattr( o, a) != rec[a]:
        return True
    # process the chidren
    for a in o.meta__undo_children_to_record:
      obj = getattr( o, a)
      if isinstance( obj, list) or isinstance( obj, set):
        for i in obj:
          if self.object_changed( i):
            return True
      elif isinstance( obj, dict):
        for i in obj.values():
          if self.object_changed( i):
            return True
      else:
        if self.object_changed( obj):
          return True
    return False
    


REDRAW_PREFERENCES = ("atom", "bond")

def _redraw_sorting( o1, o2):
  for obj_type in REDRAW_PREFERENCES:
    if o1.object_type == obj_type:
      return -1
    if o2.object_type == obj_type:
      return 1

  return -1
  
  
