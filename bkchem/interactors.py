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

"""here reside functions that implement a glue between application or paper
(main.py or paper.py) and the dialogs (dialogs.py)"""

from .molecule import molecule
import Pmw
import tkinter.messagebox as tkMessageBox
from . import validator
from . import widgets
import xml
from . import os_support
import os
from . import dialogs

from . import bkchem_exceptions as excs
from .singleton_store import Store
from .atom import atom
import operator
from functools import reduce


def ask_name_for_selected( paper):
  """opens dialog for input of molecule name and sets it"""
  top_levels, unique = paper.selected_to_unique_top_levels()
  ms = [o for o in top_levels if isinstance( o, molecule)]

  if not ms:
    tkMessageBox.showerror( _("No molecule selected."),
                            _("At least one molecule must be selected. Please select it."))
    return

  dial = Pmw.PromptDialog( paper,
                           title=_('Name'),
                           label_text=_('Name:'),
                           entryfield_labelpos = 'n',
                           buttons=(_('OK'),_('Cancel')))
  # if only one mol is selected use it as default
  if len( ms) == 1 and ms[0].name:
    dial.insertentry( 0, ms[0].name)
  res = dial.activate()
  if res == _('OK'):
    name = dial.get()
  else:
    return

  for m in ms:
    m.name = name
  Store.log( _('Name %s was set to molecule(s)') % name)
  paper.start_new_undo_record()




def ask_id_for_selected( paper):
  """opens dialog for input of molecule ID and sets it"""
  top_levels, unique = paper.selected_to_unique_top_levels()
  ms = [o for o in top_levels if isinstance( o, molecule)]

  if not ms:
    tkMessageBox.showerror( _("No molecule selected."),
                            _("At least one molecule must be selected. Please select it."))
    return 

  if len( ms) > 1:
    tkMessageBox.showerror( _("Only one molecule should be selected."),
                            _("ID must be unique value, therefore it is obviously possible to set it to one molecule only. Please select only one molecule"))
    return

  m = ms[0]

  while 1:
    dial = Pmw.PromptDialog( paper,
                             title=_('Id'),
                             label_text=_('Id:'),
                             entryfield_labelpos = 'n',
                             buttons=(_('OK'),_('Cancel')))
    # put the recent value
    if m.id:
      dial.insertentry( 0, m.id)

    res = dial.activate()
    if res == _('OK'):
      id = dial.get()
    else:
      return

    collision = 0
    for mol in paper.molecules:
      if mol != m and mol.id == id:
        tkMessageBox.showerror( _("ID collision"),
                                _("This ID is already used, use a different one"))
        collision = 1
        break
    if not collision:
      break

  m.id = id
  Store.log( _('ID %s was set to molecule') % id)
  paper.start_new_undo_record()





def check_validity( mols):
  val = validator.validator()
  val.validate( mols)
  if val.report.text_atoms:
    import tkinter.messagebox as tkMessageBox
    tkMessageBox.showerror( _("Validity error"),
                            _("Sorry but your drawing includes 'text atoms'\n - atoms with no chemical sense.") + "\n\n" +
                            _("It is not possible to export them.") + "\n\n" +
                            _("For details check the chemistry with '%s/%s'.") % (_("Chemistry"), _("Check chemistry")))
    return 0
  if val.report.exceeded_valency:
    import tkinter.messagebox as tkMessageBox
    tkMessageBox.showwarning( _("Validity warning"),
                              _("Your drawing includes some atoms with exceeded valency.") + "\n\n" + 
                              _("For details check the chemistry with '%s/%s'.") % (_("Chemistry"), _("Check chemistry")))
  if val.report.group_atoms:
    import tkinter.messagebox as tkMessageBox
    yes = tkMessageBox.askokcancel( _("Expand groups?"),
                                    _("Your drawing includes some groups.") + "\n\n" + 
                                    _("These must be expanded in order to get chemicaly valid drawing. The expansion could be undone afterwards.") + "\n\n"+
                                    _("Proceed with expansion?"))
    if yes:
      Store.app.paper.expand_groups( selected=0)
      return 1
    else:
      return 0
  return 1





def ask_inchi_program_path():
  path = Store.pm.get_preference( "inchi_program_path") or ""
  dial = widgets.FileSelectionWithText( Store.app,
                                        title=_("The InChI program path"),
                                        prompt =_("Select the InChI program executable: "),
                                        value = path,
                                        filetypes=((_("Executable files"), ("*",)),)
                                        )
  a = dial.activate()
  if a == _("OK"):
    Store.pm.add_preference( "inchi_program_path", dial.entry.get())
    Store.app.menu.component( _("Chemistry")+"-menu").entryconfigure( _("Generate InChI"), state="normal")
    return 1
  return 0



def ask_display_form_for_selected( paper):
  top_levels, unique = paper.selected_to_unique_top_levels()
  ms = [o for o in top_levels if isinstance( o, molecule)]

  if not ms:
    tkMessageBox.showerror( _("No molecule selected."),
                            _("At least one molecule must be selected. Please select it."))
    return

  dial = Pmw.Dialog( paper,
                     title=_('Display Form'),
                     #defaultbutton = _('OK'),
                     buttons=(_('OK'),_('Cancel')))
  input = widgets.HTMLLikeInput( dial.interior())
  input.pack()
  input.editPool.focus_set()
                                 
  # if only one mol is selected use it as default
  if len( ms) == 1 and ms[0].display_form:
    input.text = ms[0].display_form
  res = dial.activate()
  if res == _('OK'):
    df = input.editPool.get()
    df = str(df).encode( 'utf-8')
    ## catch not well-formed text
    try:
      xml.sax.parseString( "<a>%s</a>" % df, xml.sax.ContentHandler())
    except xml.sax.SAXParseException:
      df = xml.sax.saxutils.escape( df)
      # the second round of try: except: should catch problems not
      # related to XML wellfomedness but rather to encoding
      try:
        xml.sax.parseString( "<a>%s</a>" % df, xml.sax.ContentHandler())
      except xml.sax.SAXParseException:        
        tkMessageBox.showerror( _("Parse Error"), _("Unable to parse the text-\nprobably problem with input encoding!"))
        Store.app.paper.bell()
        return
  else:
    return

  for m in ms:
    m.display_form = df
  Store.log( _('Display form %s was set to molecule(s)') % df)
  paper.start_new_undo_record()





def save_as_template( paper):
  missing = {}
  for mol in paper.molecules:
    if not mol.t_atom:
      missing[ 'atom'] = missing.get( 'atom', 0) + 1
    if not mol.t_bond_first:
      missing[ 'bond'] = missing.get( 'bond', 0) + 1
    if not mol.name:
      missing[ 'name'] = missing.get( 'name', 0) + 1

  errors = 'atom' in missing or 'name' in missing

  if missing:
    dialog = Pmw.TextDialog( paper, title=_("Template summary"))
    dialog.withdraw()

    if errors:
      dialog.insert( 'end', _("Errors"), 'headline')
      dialog.insert( 'end', "\n")
    if 'atom' in missing:
      dialog.insert('end', ngettext(
        "%d molecule have no template atom specified",
        "%d molecules have no template atom specified",
        int(missing['atom'])) % missing['atom'])
      dialog.insert( 'end', "\n")
    if 'name' in missing:
      dialog.insert('end', ngettext(
        "%d molecule have no name specified",
        "%d molecules have no name specified",
        int(missing['name'])) % missing['name'])
      dialog.insert( 'end', "\n")
    if 'bond' in missing:
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Warnings"), 'headline')
      dialog.insert( 'end', "\n")
      dialog.insert('end', ngettext(
        "%d molecule have no template bond specified",
        "%d molecules have no template bond specified",
        int(missing['bond'])) % missing['bond'])
      dialog.insert( 'end', "\n")

    if errors:
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Please correct the above errors first"), 'headline')
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("A tutorial on how to prepare a template can be found in the file doc/custom_templates_en.html"))
      dialog.insert( 'end', "\n")

    dialog.tag_config( 'headline', underline=1)
    dialog.activate()



  if not errors:
    # check the template directory
    path = os_support.get_local_templates_path()
    if not os.path.isdir( path):
      path = os_support.create_personal_config_directory()
      if path:
        path = os_support.create_personal_config_directory( "templates")
      if not path:
        tkMessageBox.showerror( _("Directory creation failed."),
                                _("It was not possible to create the personal directory %s.") % os_support.get_personal_config_directory())
        return

    # ask for the name
    name = ''
    while not name:
      dial = Pmw.PromptDialog( paper,
                               title=_('Template file name'),
                               label_text=_('File name for the template:'),
                               entryfield_labelpos = 'n',
                               buttons=(_('OK'),_('Cancel')))
      res = dial.activate()
      if res == _('OK'):
        name = dial.get()
      else:
        return

      name = os.path.join( path ,name) + '.svg'

      if os.path.exists( name):
        q = tkMessageBox.askokcancel( _("The file already exists."),
                                      _("Template with this name already exists (path %s).\nShould I rewrite it?") % name)
        if q:
          return name
        else:
          name = ''

      else:
        return name



def create_fragment_from_selected( paper):
  top_levels, unique = paper.selected_to_unique_top_levels()
  if len( top_levels) != 1:
    Store.log( _("The selected items must be part of exactly one molecule."), message_type="error")
    return

  mol = top_levels[0]
  es = [e for e in paper.selected if e in mol.edges]
  vs = [v for v in paper.selected if v in mol.vertices]

  # ask for name
  dial = Pmw.PromptDialog( paper,
                           title=_('Fragment name'),
                           label_text=_('Enter fragment name:'),
                           entryfield_labelpos = 'w',
                           buttons=(_('OK'),_('Cancel')),
                           defaultbutton=_('OK'))
  res = dial.activate()
  if res == _('OK'):
    if mol.create_fragment( dial.get(), es, vs):
      Store.log( _("The bonds and atoms were used for creation of a new molecular fragment."), message_type="info")
    else:
      Store.log( _("The bonds and atoms could not have been used for creation of a new molecular fragment, they are probably not defining a connected subgraph of the molecular graph."), message_type="warning")





def view_fragments( paper):
  a = dialogs.fragment_dialog( paper, deletion=True)
  a.activate()



def set_atom_number( atoms):
  dial = Pmw.PromptDialog( Store.app,
                           title=_('Atom number'),
                           label_text=_('Enter atom number:'),
                           entryfield_labelpos = 'w',
                           buttons=(_('OK'),_('Cancel')))
  res = dial.activate()
  if res == _('OK'):
    for a in atoms:
      a.number = dial.get()
    Store.log( _("Number %s was set to atom(s).") % dial.get(), message_type="info")

  


def log_atom_type( vtype):
  """according to vtype tells the user how an atom text was interpreted"""
  if  vtype == "atom":
    Store.log( _("BKChem interpreted the entered text as an atom"))
  elif vtype == "group":
    Store.log( _("BKChem thinks it can interpret the entered text as a group, try to expand it to find out how it was interpreted."))
  elif vtype == "textatom":
    Store.log( _("BKChem could not interpret the entered text as anything with chemical meaning"))



def select_language( paper):
  a = dialogs.language_dialog( paper)
  a.activate()
  if a.proceed:
    lang = a.list.getvalue()
    if lang:
      if a.languages[lang[0]] == "default":
        Store.pm.remove_preference( "lang")
      else:
        Store.pm.add_preference( "lang", a.languages[lang[0]])
      tkMessageBox.showinfo( _("Info"),
                             _("The selected language will be used the next time you start BKChem."))




def convert_selected_to_linear_fragment( paper):
  # check the selection
  bond_length = 10
  changes = False
  mols = [m for m in paper.selected_to_unique_top_levels()[0] if m.object_type == "molecule"]
  for mol in mols:
    vs = [v for v in mol.vertices if v in paper.selected]
    try:
      change = atoms_to_linear_fragment( mol, vs, bond_length=bond_length)
    except ValueError:
      Store.log( _("The selection does not define connected subgraph"), message_type="error")
      return
    except excs.bkchem_graph_error as e:
      if e.id == "circular_selection":
        Store.log( e.value, message_type="error")
      else:
        raise
    else:
      changes = changes or change
      if changes:
        f = mol.create_fragment( "linear_form", mol.vertex_subgraph_to_edge_subgraph( vs), vs, type="linear_form")
        f.properties['bond_length'] = bond_length

  if changes:
    paper.start_new_undo_record()







def atoms_to_linear_fragment( mol, vs, bond_length=10):
  changes = False
  if vs and mol.defines_connected_subgraph_v( vs):
    # the selection is connected
    for v in vs:
      if len( [n for n in v.neighbors if n in vs]) > 2:
        Store.log( _("The selection is not linear - there are some splittings."), message_type="error")
        return
    # ok, we are clear
    # here comes the code to do the work
    # we start from the end atom that is more on the left side
    changes = True
    ends = [v for v in vs if len( [n for n in v.neighbors if n in vs]) == 1]
    if not ends and len( vs) != 1:
      # whole ring is selected, how could this be possibly linearized?
      raise excs.bkchem_graph_error( "circular_selection",
                                     _("The selected part of a molecule is a whole ring, there is no way to linearize it"))
    if len( vs) == 1:
      start = list(vs)[0]
      end = start
    else:
      start = ends[0].x > ends[1].x and ends[1] or ends[0]
      end = start == ends[0] and ends[1] or ends[0]
    current = start
    x = current.x
    y = current.y
    processed = set()
    current_e = None
    while 1:
      processed.add( current)
      current.show_hydrogens = True
      current.redraw()
      if current != start:
        dx = x - current.bbox()[0] + bond_length
        dy = start.y - current.y
        # move all neighbors that are not selected with their fragments
        ps = mol.get_pieces_after_edge_removal( current_e)
        if len( ps) == 2:
          p = current in ps[0] and ps[0] or ps[1]
          for a in p:
            a.move( dx, dy)
        else:
          # we are in a ring - move only current
          current.move( dx, dy)
      x = current.bbox()[2]
      if current != end:
        new = [n for n in current.neighbors if n in vs and n not in processed][0]
        current_e = new.get_edge_leading_to( current)
        current = new
      else:
        break

    mol.redraw()
    return changes

  else:
    raise ValueError("the vertices do not define connected subgraph")



def compute_oxidation_number( paper):
  v = validator.validator()
  v.validate( paper.selected_atoms)
  logged = False
  if v.report.group_atoms:
    Store.log( _("Groups must be expanded to compute oxidation number for them."), message_type="hint")
    logged = True
  # we have to check if the neighbors of the atoms we are processing are not groups or so...
  ns = list( reduce( operator.or_, map(set, [a.neighbors for a in paper.selected_atoms])))
  v.validate( ns)
  if v.report.group_atoms or v.report.text_atoms:
    Store.log( _("Unexpanded groups or text-only atoms may cause incorrect computation of oxidation number."), message_type="warning")
    logged = True
    
  for a in paper.selected_atoms:
    if isinstance( a, atom):
      oxes = a.get_marks_by_type( "oxidation_number")
      if not oxes:
        a.set_mark( "oxidation_number", draw=a.drawn)
      elif a.drawn:
        oxes[0].redraw()

  paper.start_new_undo_record()
  if not logged:
    Store.log( _("You can move and delete the created oxidation numbers in the mark mode"), message_type="hint")


def set_logging( paper, logger):
  d = dialogs.logging_dialog( paper, logger)
  d.activate()
