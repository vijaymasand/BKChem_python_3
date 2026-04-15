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


"""the main application class resides here"""

from tkinter import *

# Internationalization
try:
    _
except NameError:
    _ = lambda x: x

from .paper import chem_paper
import Pmw
from .xml_writer import SVG_writer
from tkinter.filedialog import asksaveasfilename, askopenfilename
import os
import sys
import tkinter.messagebox as tkMessageBox
import xml.dom.minidom as dom
from . import data
from . import messages
from . import dom_extensions
from . import non_xml_writer
from . import import_checker
from . import dialogs
from . import export
import warnings
from . import plugins
from . import misc
from .edit_pool import editPool
from . import pixmaps
import types
from .temp_manager import template_manager
from . import modes
from . import interactors
from . import os_support
from .id_manager import id_manager
from . import pref_manager
import string

from . import oasa_bridge
from .plugins import plugin
from . import config
from . import logger
from .plugin_support import plugin_manager
from . import print_utils


from .singleton_store import Store, Screen
from . import oasa
from . import molecule



class BKChem( Tk):


  def __init__( self):
    Tk.__init__( self)
    # setting the singleton values
    Store.app = self
    Screen.dpi = self.winfo_fpixels( "1i")

    self.tk.call("tk", "useinputmethods", "1")
    #self.tk.call( "encoding", "system", "iso8859-2")
    #print self.tk.call( "encoding", "system")
    #self.option_add( "*Background", "#eaeaea")
    self.option_add( "*Entry*Background", "white")
    self.option_add( "*Entry*Foreground", "#000000")
    self.tk_setPalette( "background", config.background_color,
                        "insertBackground","#ffffff")

    oasa.config.Config.molecule_class = molecule.molecule
    

  def initialize( self):
    self.in_batch_mode = 0
    self.init_basics()
    
    # template and group managers - MUST be before add_new_paper!
    self.init_singletons()
    
    # main drawing part
    self.papers = []
    self.notebook = Pmw.NoteBook( self.main_frame,
                                  raisecommand=self.change_paper,
                                  borderwidth=config.border_width)
    self.add_new_paper()

    # menu initialization
    self.init_menu()
    self.init_plugins_menu()

    # modes initialization
    self.init_modes()
    self.mode = 'draw' # this is normaly not a string but it makes things easier on startup
    self.init_mode_buttons()

    # edit pool
    self.editPool = editPool( self.main_frame, width=60)
    self.editPool.grid( row=3, sticky="wens")

    # main drawing part packing
    self.notebook.grid( row=4, sticky="wens")
    self.notebook.setnaturalsize()


    # preferences
    self.init_preferences()

    # init status bar
    self.init_status_bar()

    # 
    self.radiobuttons.invoke( self.mode)

    # protocol bindings
    self.protocol("WM_DELETE_WINDOW", self._quit)


    self.update_menu_after_selection_change( None)

    #self.start_server()


  def initialize_batch( self):
    self.in_batch_mode = 1
    self.init_basics()
    
    # main drawing part
    self.papers = []
    self.notebook = Pmw.NoteBook( self.main_frame,
                                  raisecommand=self.change_paper)
    self.add_new_paper()

    # template and group managers
    self.init_singletons()

    # not very verbose logging strategy
    Store.logger.handling = logger.batch_mode

    # main drawing part packing
    self.notebook.grid( row=4, sticky="wens")
    #self.notebook.setnaturalsize()


    #self.papers.append( self.paper)

    # protocol bindings
    self.protocol("WM_DELETE_WINDOW", self._quit)

    # modes initialization
    self.mode = 'draw' # this is normaly not a string but it makes things easier on startup
    



  def init_menu( self):
    # defining menu
    menuf = Frame( self.main_frame, relief=RAISED, bd=config.border_width)
    menuf.grid( row=0, sticky="we")

    self.menu = Pmw.MenuBar( menuf, balloon=self.menu_balloon)
    self.menu.pack( side="left", expand=1, fill="both")


    self.menu_template = [
      # file menu
      ( _('File'),  'menu',     _('Open, save, export, and import files'),   'left'),
      #  menu         type        name            accelerator  status help                          command             state variable
      ( _('File'),  'command',  _('New'),       '(C-x C-n)', _("Create a new file in a new tab"), self.add_new_paper, None),
      ( _('File'),  'command',  _('Save'),      '(C-x C-s)', _("Save the file"),                  self.save_CDML,     None),
      ( _("File"),  'command',  _('Save As..'), '(C-x C-w)', _("Save the file under different name"), self.save_as_CDML, None),
      ( _("File"),  'command',  _('Save As Template'), None, _("Save the file as template, certain criteria must be met for this to work"), self.save_as_template, None),
      ( _("File"),  'command',  _('Load'),      '(C-x C-f)', _("Load (open) a file in a new tab"), self.load_CDML,    None),
      ( _("File"),  'command',  _('Load to the same tab'), None, _("Load a file replacing the current one"), lambda : self.load_CDML( replace=1), None),
      ( _("File"),  'cascade',  _("Recent files"), _("The most recently used files")),
      ( _("File"),  'separator'),
      # export cascade
      ( _("File"),  'cascade',  _('Export'),     _("Export the current file")),
      ( _("Export"), 'command',  _('SVG'),  None, _("Export to plain SVG - Scalable Vector Graphics - without embedding BKChem data inside"), self.save_SVG, None),
      ( _("File"),  'cascade',  _('Import'),     _("Import a non-native file format")),
      ( _("File"),  'separator'),
      ( _("File"),  'command',  _('Page Setup'), None, _("Set the papers size and other properties of the document"), self.change_properties, None),
      ( _("File"),  'separator'),
      ( _("File"),  'command',  _('Print'),      '(C-p)', _("Print Preview and Print"), self.print_file, None),
      ( _("File"),  'command',  _('Close tab'), '(C-x C-t)', _("Close the current tab, exit when there is only one tab"), self.close_current_paper, None),
      ( _("File"),  'separator'),
      ( _("File"),  'command',  _('Exit'),      '(C-x C-c)', _("Exit BKChem"), self._quit, None),

      # edit menu
      ( _('Edit'),  'menu',     _("Undo, Copy, Paste etc."),   'left'),
      ( _("Edit"),  'command',  _('Undo'),      '(C-z)',     _("Revert the last change made"), lambda : self.paper.undo(), lambda : self.paper.um.can_undo()),
      ( _("Edit"),  'command',  _('Redo'),      '(C-S-z)',   _("Revert the last undo action"), lambda : self.paper.redo(), lambda : self.paper.um.can_redo()),
      ( _("Edit"),  'separator'),
      ( _("Edit"),  'command',  _('Cut'), '(C-w)', _("Copy the selected objects to clipboard and delete them"), lambda : self.paper.selected_to_clipboard( delete_afterwards=1),  'selected'),
      ( _("Edit"),  'command', _('Copy'), '(A-w)', _("Copy the selected objects to clipboard"), lambda : self.paper.selected_to_clipboard(),  'selected'),
      ( _("Edit"),  'command', _('Paste'), '(C-y)', _("Paste the content of clipboard to current paper"), lambda : self.paper.paste_clipboard( None), lambda : self._clipboard),
      ( _("Edit"),  'separator'),
      ( _("Edit"),  'command', _('Selected to clipboard as SVG'), None, _("Create SVG for the selected objects and place it to clipboard in text form"), lambda : self.paper.selected_to_real_clipboard_as_SVG(),  'selected'),
      ( _("Edit"),  'command', _('Selected to clipboard as image'), None, _("Create high resolution image for the selected objects and place it to clipboard"), lambda : self.paper.selected_to_real_clipboard_as_image(),  'selected'),
      ( _("Edit"),  'separator'),
      ( _("Edit"),  'command', _('Select all'), '(C-S-a)', _("Select everything on the paper"), lambda : self.paper.select_all(),  None),
      
      # align menu
      ( _('Align'), 'menu',    _("Aligning of selected objects"), 'left'),
      ( _("Align"), 'command', _('Top'), '(C-a C-t)', _("Align the tops of selected objects"), lambda : self.paper.align_selected( 't'), 'two_or_more_selected'),
      ( _("Align"), 'command', _('Bottom'), '(C-a C-b)', _("Align the bottoms of selected objects"), lambda : self.paper.align_selected( 'b'), 'two_or_more_selected'),
      ( _("Align"), 'command', _('Left'), '(C-a C-l)', _("Align the left sides of selected objects"), lambda : self.paper.align_selected( 'l'), 'two_or_more_selected'),
      ( _("Align"), 'command', _('Right'), '(C-a C-r)', _("Align the rights sides of selected objects"), lambda : self.paper.align_selected( 'r'), 'two_or_more_selected'),
      ( _("Align"), 'separator'),
      ( _("Align"), 'command', _('Center horizontally'), '(C-a C-h)', _("Align the horizontal centers of selected objects"), lambda : self.paper.align_selected( 'h'), 'two_or_more_selected'),
      ( _("Align"), 'command', _('Center vertically'), '(C-a C-v)', _("Align the vertical centers of selected objects"), lambda : self.paper.align_selected( 'v'), 'two_or_more_selected'),

      # object menu
      ( _("Object"), 'menu',    _("Set properties of selected objects"), 'left'),
      ( _("Object"), 'command', _('Scale'), None, _("Scale selected objects"), self.scale, 'selected'),
      ( _("Object"), 'separator'),
      ( _("Object"), 'command', _('Bring to front'), '(C-o C-f)', _("Lift selected objects to the top of the stack"), lambda : self.paper.lift_selected_to_top(), 'selected'),
      ( _("Object"), 'command', _('Send back'), '(C-o C-b)', _("Lower the selected objects to the bottom of the stack"), lambda : self.paper.lower_selected_to_bottom(), 'selected'),
      ( _("Object"), 'command', _('Swap on stack'), '(C-o C-s)', _("Reverse the ordering of the selected objects on the stack"), lambda : self.paper.swap_selected_on_stack(), 'two_or_more_selected'),
      ( _("Object"), 'separator'),
      ( _("Object"), 'command', _('Vertical mirror'), None,
        _("Creates a reflection of the selected objects, the reflection axis is the common vertical axis of all the selected objects"),
        lambda : self.paper.swap_sides_of_selected(), 'selected_mols'),
      ( _("Object"), 'command', _('Horizontal mirror'), None,
        _("Creates a reflection of the selected objects, the reflection axis is the common horizontal axis of all the selected objects"),
        lambda : self.paper.swap_sides_of_selected('horizontal'), 'selected_mols'),
      ( _("Object"), 'separator'),
      ( _("Object"), 'command', _('Configure'), 'Mouse-3', _("Set the properties of the object, such as color, font size etc."), lambda : self.paper.config_selected(), 'selected'),
      #( _("Object"), 'separator')

      # chemistry menu
      ( _('Chemistry'), 'menu', _("Information about molecules, group expansion and other chemistry related stuff"), 'left'),
      ( _("Chemistry"), 'command', _('Info'), '(C-o C-i)', _("Display summary formula and other info on all selected molecules"), lambda : self.paper.display_info_on_selected(), 'selected_mols'),
      ( _("Chemistry"), 'command', _('Check chemistry'), '(C-o C-c)', _("Check if the selected objects have chemical meaning"), lambda : self.paper.check_chemistry_of_selected(), 'selected_mols'),
      ( _("Chemistry"), 'command', _('Expand groups'), '(C-o C-e)', _("Expand all selected groups to their structures"), lambda : self.paper.expand_groups(), 'groups_selected'),
      ( _("Chemistry"), 'separator'),
      ( _("Chemistry"), 'command', _('Compute oxidation number'), None, _("Compute and display the oxidation number of selected atoms"), lambda : interactors.compute_oxidation_number( self.paper), 'selected_atoms'),      
      ( _("Chemistry"), 'separator'),
      ( _("Chemistry"), 'command', _('Read SMILES'), None, _("Read a SMILES string and convert it to structure"), self.read_smiles, None),
      ( _("Chemistry"), 'command', _('Read InChI'), None, _("Read an InChI string and convert it to structure"), self.read_inchi, None),
      ( _("Chemistry"), 'separator'),
      ( _("Chemistry"), 'command', _('Generate SMILES'), None, _("Generate SMILES for the selected structure"), self.gen_smiles, 'selected_mols'),
      ( _("Chemistry"), 'command', _('Generate InChI'), None, _("Generate an InChI for the selected structure by calling the InChI program"), self.gen_inchi,
        lambda : Store.pm.has_preference("inchi_program_path") and self.paper.selected_mols),
      ( _("Chemistry"), 'separator'),
      #( _("Chemistry"), 'command', _('Set display form'), "(C-o C-d)",
      #  _("The display form is stored in the saved file and tells how the molecule should be displayed in text"),
      #  lambda : interactors.ask_display_form_for_selected( self.paper), 'selected_mols'),
      ( _("Chemistry"), 'command', _('Set molecule name'), None, _("Set the name of the selected molecule"), lambda : interactors.ask_name_for_selected( self.paper), 'selected_mols'),
      ( _("Chemistry"), 'command', _('Set molecule ID'), None, _("Set the ID of the selected molecule"), lambda : interactors.ask_id_for_selected( self.paper), 'one_mol_selected'),
      ( _("Chemistry"), 'separator'),
      ( _("Chemistry"), 'command', _('Create fragment'), None, _("Create a fragment from the selected part of the molecule"), lambda : interactors.create_fragment_from_selected( self.paper), 'one_mol_selected'),
      ( _("Chemistry"), 'command', _('View fragments'), None, _("Show already defined fragments"), lambda : interactors.view_fragments( self.paper), None),
      ( _("Chemistry"), 'separator'),
      ( _("Chemistry"), 'command', _('Convert selection to linear form'), None, _("Convert selected part of chain to linear fragment. The selected chain must not be split."), lambda : interactors.convert_selected_to_linear_fragment( self.paper), 'selected_mols'),
      #
      
      # options
      ( _('Options'), 'menu',    _("Settings that affect how BKChem works"), 'left'),
      ( _("Options"), 'command', _('Standard'), None, _("Set the default drawing style here"), self.standard_values, None),
      ( _("Options"), 'command', _('Language'), None, _("Set the language used after next restart"), lambda : interactors.select_language( self.paper), None),
      ( _("Options"), 'command', _('Logging'), None, _("Set how messages in BKChem are displayed to you"), lambda : interactors.set_logging( self.paper, Store.logger), None),
      ( _("Options"), 'command', _('InChI program path'), None, _("To use InChI in BKChem you must first give it a path to the InChI program here"),
        interactors.ask_inchi_program_path, None),
      ( _("Options"), 'separator'),      
      ( _("Options"), 'command', _('Preferences'), None, _("Preferences"), self.ask_preferences, None),

      # help menu
      ( _('Help'), 'menu', _("Help and information about the program"), "right"),
      ( _("Help"), 'command', _('About'), None, _("General information about BKChem"), self.about, None),

      # plugins menu
      ( _("Plugins"), 'menu', _("Small additional scripts"), "right")
      ]

      

## ##     hacksButton.pack( side= 'right')
## ##     hacksMenu = Menu( hacksButton, tearoff=0)
## ##     hacksButton['menu'] = hacksMenu
## ##     hacksMenu.add( 'command', label=_('Molecules to separate tabs'), command=self.molecules_to_separate_tabs)
## ##     hacksMenu.add( 'command', label=_('Rings to separate tabs'), command=self.rings_to_separate_tabs)
## ##     hacksMenu.add( 'command', label=_('Normalize aromatic double bonds'), command=self.normalize_aromatic_double_bonds)
## ##     hacksMenu.add( 'command', label=_('Clean'), command=self.clean)


    # CREATION OF THE MENU
    
    menus = set() # we use this later for plugin entries addition

    for temp in self.menu_template:
      if temp[1] == "menu":
        self.menu.addmenu( temp[0], temp[2], side=temp[3])
        menus.add( temp[0])
      elif temp[1] == "command":
        menu, _ignore, label, accelerator, help, command, state_var = temp
        self.menu.addmenuitem( menu, 'command', label=label, accelerator=accelerator, statusHelp=help, command=command)
      elif temp[1] == "separator":
        self.menu.addmenuitem( temp[0], 'separator')
      elif temp[1] == "cascade":
        self.menu.addcascademenu( temp[0], temp[2], temp[3], tearoff=0)

        
    # ADDITION OF PLUGINS TO THE MENU
        
    added_to = set()
    for name in self.plug_man.get_names( type="script"):
      tooltip = self.plug_man.get_description( name)
      menu = self.plug_man.get_menu( name) 
      if menu and _(menu) in menus:
        menu = _(menu)
        if not menu in added_to:
          self.menu.addmenuitem( menu, "separator")
      else:
        menu = _("Plugins")

      self.menu.addmenuitem( menu, 'command', label=name,
                               statusHelp=tooltip,
                               command=misc.lazy_apply( self.run_plugin, (name,)))
      added_to.add( menu)






  def init_basics( self):
    Pmw.initialise( self)
    from . import pixmaps
    if os.name == 'posix':
      try:
        self.option_add( "*font", ("-adobe-helvetica-medium-r-normal-*-12-*-*-*-p-*-iso10646-1"))
        ##self.option_add( "*font", ("-adobe-helvetica-medium-r-normal-*-*-100-*-*-*-*-*-*"))
      except:
        print("cannot init default font")
    else:
      self.option_add( "*font", ("Helvetica",10,"normal"))
    # colors
    #self.option_add( "*background", "#d0d0d0")
    #self.option_add( "*borderwidth", config.border_width)
    self.title( "BKChem")
    self.stat= StringVar()
    self.cursor_position = StringVar()
    self.stat.set( "Idle")
    self.save_dir = '.'
    self.save_file = None
    self.svg_dir = '.'
    self.svg_file = ''
    self._recent_files = []

    self._clipboard = None
    self._clipboard_pos = None

    self._untitled_counter = 0
    self.__tab_name_2_paper = {}
    self.__last_tab = 0


    self._after = None

    self.balloon = Pmw.Balloon( self)
    self.menu_balloon = Pmw.Balloon( self, statuscommand=self.update_status)
    self.main_frame = Frame( self)
    self.main_frame.pack( fill='both', expand=1)
    self.main_frame.rowconfigure( 4, weight=1)
    self.main_frame.columnconfigure( 0, weight=1)

    self.plugins = {}
    if plugins.__all__:
      for name in plugins.__all__:
        plugin = plugins.__dict__[ name]
        self.plugins[ plugin.name] = plugin

        # support for tuning of piddle
        if plugin.name.endswith( "(Piddle)"):
          from .plugins import tk2piddle
          from . import tuning
          tk2piddle.tk2piddle.text_x_shift = tuning.Tuning.Piddle.text_x_shift

    self.paper = None





  def init_plugins_menu( self):
    # PLUGINS
    names = sorted(self.plugins.keys())
    for name in names:
      plugin = self.plugins[ name]
      local_name = hasattr( plugin, "local_name") and getattr( plugin, "local_name") or plugin.name
      if ('importer' in  plugin.__dict__) and plugin.importer:
        doc_string = hasattr( plugin.importer, "doc_string") and getattr( plugin.importer, "doc_string") or plugin.importer.__doc__
        self.menu.addmenuitem( _("Import"), 'command', label=local_name,
                               statusHelp=doc_string,
                               command=misc.lazy_apply( self.plugin_import, (plugin.name,)))
      if ('exporter' in plugin.__dict__) and plugin.exporter:
        doc_string = hasattr( plugin.exporter, "doc_string") and getattr( plugin.exporter, "doc_string") or plugin.exporter.__doc__
        self.menu.addmenuitem( _("Export"), 'command', label=local_name,
                               statusHelp=doc_string,
                               command=misc.lazy_apply( self.plugin_export, (plugin.name,)))





  def init_singletons( self):
    # preference manager - must be initialized first!
    Store.pm = pref_manager.pref_manager()
    
    # logger
    Store.logger = logger.logger()
    Store.log = Store.logger.log

    # id_manager
    Store.id_manager = id_manager()

    # template_manager
    Store.tm = template_manager()
    Store.tm.add_template_from_CDML( "templates.cdml")

    # manager for user user defined templates
    Store.utm = template_manager()
    self.read_user_templates()

    # groups manager
    Store.gm = template_manager()
    Store.gm.add_template_from_CDML( "groups.cdml")
    Store.gm.add_template_from_CDML( "groups2.cdml")

    self.plug_man = plugin_manager()
    plugs = self.plug_man.get_available_plugins()
    #print >> sys.stderr, "loaded plugins:", plugs



  def init_preferences( self):
    # save_dir must be set after the preference manager is initiated
    # we set the old directory only when the current working directory is
    # the same as the installation directory and the install was really performed
    # this is very common on windows, where you mostly start the program via an icon
    # it is not easy to guess when the right situation occured
    if os.path.abspath( os_support.get_bkchem_run_dir()) == os.path.abspath( os.getcwd()):
      # we are running from the installation directory
      if os_support.site_config != None:
        # we are probably on Linux after install, go ahead
        self.save_dir = Store.pm.get_preference( "default-dir")
      elif sys.path[0].endswith( ".exe"):
        # we are running on windows from an exe file, good as well
        self.save_dir = Store.pm.get_preference( "default-dir")
      else:
        # otherwise we do not want to reset the path - it could confuse the user
        pass
    for i in range( 5):
      path = Store.pm.get_preference( "recent-file%d" % (i+1))
      if path:
        self._recent_files.append( path)
        self.menu.addmenuitem( _("Recent files"), 'command', label=path,
                               command=misc.lazy_apply( self.load_CDML, (path,)))
    if not self.in_batch_mode:
      # we do not load (or save) handling info when in batch mode
      for key in Store.logger.handling:
        value = Store.pm.get_preference( "logging_%s"%key)
        if value:
          Store.logger.set_handling( key, value)



  def init_modes( self):
    self.modes = { 'draw': modes.draw_mode(),
                   'edit': modes.edit_mode(),
                   'arrow': modes.arrow_mode(),
                   'plus': modes.plus_mode(),
                   'template': modes.template_mode(),
                   'text': modes.text_mode(),
                   'rotate': modes.rotate_mode(),
                   'bondalign': modes.bond_align_mode(),
                   'vector': modes.vector_mode(),
                   'mark': modes.mark_mode(),
                   'atom': modes.atom_mode(),
                   #'reaction': modes.reaction_mode(),
                   'usertemplate': modes.user_template_mode(),
                   'misc': modes.misc_mode(),
                   'bracket': modes.bracket_mode(),
                   #'externaldata': modes.external_data_mode(),
                   #'rapiddraw': modes.rapid_draw_mode()
                   }
    self.modes_sort = ['edit', 'draw', 'template', 'usertemplate', 'atom', 'mark', 'arrow',
                       'plus', 'text', 'bracket', 'rotate', 'bondalign', 'vector', 'misc']#  'reaction', 'externaldata'] #, 'rapiddraw']

    # import plugin modes
    # import plugin modes
    import sys
    import string

    for plug_name in self.plug_man.get_names(type="mode"):
        plug = self.plug_man.get_plugin_handler(plug_name)
        module_name = plug.get_module_name()
        
        # no invalid characters in mode_name
        mode_name = ''.join([x if x in string.ascii_letters else "X" for x in module_name])
        
        try:
            # VERSION CHECK & MERGED LOGIC
            if sys.version_info >= (3, 12):
                # Modern way for Python 3.12+
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, plug.filename)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                else:
                    continue
            else:
                # Legacy way for Python 3.10 and older (avoids warnings on 3.12+)
                import imp
                module = imp.load_source(module_name, plug.filename)
        
        except Exception as e:
            # Log or skip on error
            continue
        else:
            if hasattr(module, 'plugin_mode'):
                self.modes[module_name.replace("_", "")] = module.plugin_mode()
                self.modes_sort.append(module_name.replace("_", ""))
    
  def init_mode_buttons( self):
    # mode selection panel     
    radioFrame = Frame( self.main_frame)
    radioFrame.grid( row=1, sticky='we')
    self.radiobuttons = Pmw.RadioSelect(radioFrame,
                                        buttontype = 'button',
                                        selectmode = 'single',
                                        orient = 'horizontal',
                                        command = self.change_mode,
                                        hull_borderwidth = 0,
                                        padx = 0,
                                        pady = 0,
                                        hull_relief = 'flat',
                                        
             )
    self.radiobuttons.pack( side=LEFT)
    # Add some buttons to the radiobutton RadioSelect.
    for m in self.modes_sort:
      if m in pixmaps.images:
        recent = self.radiobuttons.add( m, image=pixmaps.images[m], text=self.modes[m].name, activebackground='grey',
                                        relief='flat', borderwidth=config.border_width)
        self.balloon.bind( recent, self.modes[ m].name)
      else:
        self.radiobuttons.add( m, text=self.modes[ m].name, borderwidth=config.border_width)
    # sub-mode support
    self.subFrame = Frame( self.main_frame)
    self.subFrame.grid( row=2, sticky='we')
    self.subbuttons = []
    # the remaining of sub modes support is now in self.change_mode





  def init_status_bar( self):
    status_frame = Frame( self.main_frame)
    status_frame.grid( row=5, sticky="we")
    status = Label( status_frame, relief=SUNKEN, bd=config.border_width, textvariable=self.stat, anchor='w', height=2, justify='l')
    status.pack( side="left", expand=1, fill="both")
    position = Label( status_frame, relief=SUNKEN, bd=config.border_width, textvariable=self.cursor_position, anchor='w', height=2, justify='l')
    position.pack( side="right")





  def about( self):
    dialog = Pmw.MessageDialog(self,
                               title = _('About BKChem'),
                               defaultbutton = 0,
                               buttons=(_("OK"),),
                               message_text = "BKChem " + _("version") + " " + config.current_BKChem_version + "\n\n" + messages.about_text)
    dialog.iconname('BKChem')
    dialog.activate()






  def change_mode( self, tag):
    old_mode = self.mode
    self.mode = self.modes[ tag]
    if type( old_mode) != str:
      old_mode.cleanup()
      self.mode.copy_settings( old_mode)

    if self.subbuttons:
      for butts in self.subbuttons:
        if hasattr( butts, 'deleteall()'):
          butts.deleteall()
        butts.destroy()
    self.subbuttons = []
    m = self.mode
    for i in range( len( m.submodes)):
      if i not in m.pulldown_menu_submodes:
        # these are normal button like menus
        self.subbuttons.append( Pmw.RadioSelect( self.subFrame,
                                                 buttontype = 'button',
                                                 selectmode = 'single',
                                                 orient = 'horizontal',
                                                 command = self.change_submode,
                                                 hull_borderwidth = 0,
                                                 padx = 0,
                                                 pady = 0,
                                                 hull_relief = 'ridge',
                                                 ))
        if i % 2:
          self.subbuttons[i].pack( side=LEFT, padx=10)
        else:
          self.subbuttons[i].pack( side=LEFT)
        for sub in m.submodes[i]:
          img_name = m.__class__.__name__.replace("_mode","") + "-" + sub
          if img_name in pixmaps.images:
            img = pixmaps.images[img_name]
          elif sub in pixmaps.images:
            img = pixmaps.images[sub]
          else:
            img = None
          if img:
            recent = self.subbuttons[i].add( sub, image=img, activebackground='grey', borderwidth=config.border_width)
            self.balloon.bind( recent, m.submodes_names[i][m.submodes[i].index(sub)])
          else:
            self.subbuttons[i].add( sub, text=m.submodes_names[i][m.submodes[i].index(sub)], borderwidth=config.border_width)
        # black magic???
        j = m.submodes[i][ m.submode[i]]
        self.subbuttons[i].invoke( j)
      else:
        # these are pulldown menus, to save space for text-only items
        self.subbuttons.append( Pmw.OptionMenu( self.subFrame,
                                                items = m.submodes_names[i],
                                                command = self.change_submode))
        if i % 2:
          self.subbuttons[i].pack( side=LEFT, padx=10)
        else:
          self.subbuttons[i].pack( side=LEFT)

    self.paper.mode = self.mode
    #Store.log( _('mode changed to ')+self.modes[ tag].name)
    self.mode.startup()





  def change_submode( self, tag):
    self.mode.set_submode( tag)




  def update_status( self, signal, time=None):
    """if time is none it is calculated based on the string length"""
    if time == None and signal:
      time = 4 + 0.05 * len( signal)
    if signal:
      self.stat.set( signal)
      if self._after:
        self.after_cancel( self._after)
      self._after = self.after( int( time*1000), func=self.clear_status)





  def change_paper( self, name):
    if self.papers:
      old_paper = self.paper
      # de-highlighting of current tab
      try:
        i = self.papers.index( old_paper)
        self.notebook.tab( i).configure( background=config.background_color, fg="black")
      except:
        pass
      i = self.notebook.index( name)
      # highlighting of current tab
      self.notebook.tab( i).configure( background="#777777", fg="white")
      # the rest
      self.paper = self.papers[i]
      if hasattr( self, 'mode') and not type( self.mode) == str and old_paper in self.papers and self.paper != old_paper:
        # this is not true on startup and tab closing
        self.mode.on_paper_switch( old_paper, self.paper)



  def add_new_paper( self, name=''):
    # check if the same file is opened
    p = self.check_if_the_file_is_opened( name)
    if p:
      Store.log( _("Sorry but I cannot open the same file twice: ")+"\n"+name, message_type="error")
      return False
    name_dic = self.get_name_dic( name=name)
    # create the tab
    _tab_name = self.get_new_tab_name()
    page = self.notebook.add( _tab_name, tab_text = chem_paper.create_window_name( name_dic))
    paper = chem_paper( page,
                        scrollregion=(-100,-100,'300m','400m'),
                        background="grey",
                        closeenough=3,
                        file_name=name_dic)
    self.__tab_name_2_paper[ _tab_name] = paper
    # the scrolling
    scroll_y = Scrollbar( page, orient = VERTICAL, command = paper.yview, bd=config.border_width)
    scroll_x = Scrollbar( page, orient = HORIZONTAL, command = paper.xview, bd=config.border_width)
    paper.grid( row=0, column=0, sticky="news")
    page.grid_rowconfigure( 0, weight=1, minsize = 0)
    page.grid_columnconfigure( 0, weight=1, minsize = 0)
    scroll_x.grid( row=1, column=0, sticky='we')
    scroll_y.grid( row=0, column=1, sticky='ns')
    paper['yscrollcommand'] = scroll_y.set
    paper['xscrollcommand'] = scroll_x.set

    self.papers.append( paper)
    self.change_paper( _tab_name)
    self.notebook.selectpage( Pmw.END)
    paper.bind( "<<selection-changed>>", self.update_menu_after_selection_change)
    paper.bind( "<<clipboard-changed>>", self.update_menu_after_selection_change)
    paper.bind( "<<undo>>", self.update_menu_after_selection_change)
    paper.bind( "<<redo>>", self.update_menu_after_selection_change)
    if not self.paper:
      self.paper = paper  # this is needed for the batch mode, normaly its done in change_paper
    else:
      self.paper.focus_set()
    return True


  def close_current_paper( self, call_quit_if_no_remains=True):
    ret = self.close_paper()
    if self.papers == [] and call_quit_if_no_remains:
      self._quit()
    return ret
  
  def print_file( self):
    print_utils.execute_print( self.paper )


  def close_paper( self, paper=None):
    p = paper or self.paper
    if hasattr( self, "editPool") and self.editPool.active:
      self.editPool._cancel(None)

    if p.changes_made and not self.in_batch_mode:
      name = p.file_name['name']
      dialog = Pmw.MessageDialog( self,
                                  title= _("Really close?"),
                                  message_text = _("There are unsaved changes in file %s, what should I do?") % name,
                                  buttons = (_('Close'),_('Save'),_('Cancel')),
                                  defaultbutton = _('Close'))
      dialog.transient( self)
      dialog.grab_set()
      self.update_idletasks()
      result = dialog.activate()
      if result == _('Save'):
        self.save_CDML()
      elif result == _('Cancel'):
        return 0 # we skip away
      elif result != _('Close'):
        return 0 # cancel if unexpected result
      # if Close, continue with closing
    self.papers.remove( p)

    # cleanup
    # find the name of the tab
    name = self.get_paper_tab_name( p)
    del self.__tab_name_2_paper[ name]
    p.mrproper()
    self.notebook.delete( name or Pmw.SELECT)
    return 1



  def clear_status( self):
    self.stat.set( '')



  def save_CDML( self, name=None, update_default_dir=1):
    """saves content of self.paper (recent paper) under its filename,
    if the filename was automaticaly given by bkchem it will call save_as_CDML
    in order to ask for the name"""
    if not name:
      if self.paper.file_name['auto']:
        new_name = self.save_as_CDML()
        return
      else:
        a = os.path.join( self.paper.file_name['dir'], self.paper.file_name['name'])
        return self._save_according_to_extension( a, update_default_dir=update_default_dir)
    else:
      return self._save_according_to_extension( name, update_default_dir=update_default_dir)


  def save_as_CDML( self):
    """asks the user the name for a file and saves the current paper there,
    dir and name should be given as starting values"""
    dir = self.paper.file_name['dir']
    name = self.paper.file_name['name']
    a = asksaveasfilename( defaultextension = ".svg", initialdir = dir, initialfile = name,
                           title = _("Save As..."), parent = self,
                           filetypes=((_("CD-SVG file"),".svg"),
                                      (_("Gzipped CD-SVG file"),".svgz"),
                                      (_("CDML file"),".cdml"),
                                      (_("Gzipped CDML file"),".cdgz")))
    if a != '' and a!=():
      if self._save_according_to_extension( a):
        name = self.get_name_dic( a)
        if self.check_if_the_file_is_opened( name['name'], check_current=0):
          tkMessageBox.showerror( _("File already opened!"), _("Sorry but you are already editing a file with this name (%s), please choose a different name or close the other file.") % name['name'])
          return None
        self.paper.file_name = self.get_name_dic( a)
        self.notebook.tab( self.get_paper_tab_name( self.paper)).configure( text = self.paper.file_name['name'])
        return self.paper.file_name
      else:
        return None
    else:
      return None
    
    


  def _save_according_to_extension( self, filename, update_default_dir=1):
    """decides the format from the file extension and saves self.paper in it"""
    save_dir, save_file = os.path.split( filename)
    if update_default_dir:
      self.save_dir = save_dir
    ext = os.path.splitext( filename)[1]
    if ext == '.cdgz':
      type = _('gzipped CDML')
      success = export.export_CDML( self.paper, filename, gzipped=1)
    elif ext == '.cdml':
      type = _('CDML')
      success = export.export_CDML( self.paper, filename, gzipped=0)        
    elif ext == '.svgz':
      type = _('gzipped CD-SVG')
      success = export.export_CD_SVG( self.paper, filename, gzipped=1)
    else:
      type = _('CD-SVG')
      success = export.export_CD_SVG( self.paper, filename, gzipped=0)
    if success:
      Store.log( _("saved to %s file: %s") % (type, os.path.abspath( os.path.join( save_dir, save_file))))
      self._record_recent_file( os.path.abspath( os.path.join( save_dir, save_file)))
      self.paper.changes_made = 0
      return 1
    else:
      Store.log( _("failed to save to %s file: %s") % (type, save_file))
      return 0



  def set_file_name( self, name, check_ext=0):
    """if check_ext is true append a .svg extension if no is present"""
    if check_ext and not os.path.splitext( name)[1]:
      self.paper.file_name = self.get_name_dic( name + ".svg", local_file=1)
    else:
      self.paper.file_name = self.get_name_dic( name, local_file=1)
    self.notebook.tab( self.get_paper_tab_name( self.paper)).configure( text = self.paper.file_name['name'])




  def load_CDML( self, file=None, replace=0):
    """loads a file into a new paper or the current one (depending on replace value),
    file is the name of the file to load (if not supplied dialog is fired),
    if replace == 0 the content of the file is added to the current content of the file"""
    if not file:
      if self.paper.changes_made and replace:
        if tkMessageBox.askokcancel( _("Forget changes?"),_("Forget changes in currently visiting file?"), default='ok', parent=self) == 0:
          return 0
      a = askopenfilename( defaultextension = "",
                           initialdir = self.save_dir,
                           title = _("Load"),
                           parent = self,
                           filetypes=((_("All native formats"), (".svg", ".svgz", ".cdml", ".cdgz")),
                                      (_("CD-SVG file"), ".svg"),
                                      (_("Gzipped CD-SVG file"), ".svgz"),
                                      (_("CDML file"),".cdml"),
                                      (_("CDGZ file"),".cdgz"),
                                      (_("Gzipped files"), ".gz"),
                                      (_("All files"),"*")))
    else:
      a = file
    if not a:
      return None
    if self.papers and (replace or (self.paper.file_name['auto'] and not self.paper.changes_made)):
      self.close_paper()
    p = self.add_new_paper( name=a)
    if p != 0:
      self.paper.mode = self.mode # somehow the raise event does not work here
      return self._load_CDML_file( a)
    return 0



  def _load_CDML_file( self, a, draw=True):
    if a != '':
      self.save_dir, save_file = os.path.split( a)
      ## try if the file is gzipped
      # try to open the file
      try:
        import gzip
        inp = gzip.open( a, "rb")
      except IOError:
        # can't read the file
        Store.log( _("cannot open file ") + a)
        return None
      # is it a gzip file?
      it_is_gzip = 1
      try:
        str = inp.read()
      except IOError:
        # not a gzip file
        it_is_gzip = 0
      # if it's gzip file parse it
      if it_is_gzip:
        try:
          doc = dom.parseString( str)
        except:
          Store.log( _("error reading file"))
          inp.close()
          return None
        inp.close()
        del gzip
        doc = [n for n in doc.childNodes if n.nodeType == doc.ELEMENT_NODE][0]
      else:
      ## otherwise it should be normal xml file
        ## try to parse it
        try:
          doc = dom.parse( a)
        except IndexError: 
          Store.log( _("error reading file"))
          return None
        ## if it works check if its CDML of CD-SVG file
        doc = [n for n in doc.childNodes if n.nodeType == doc.ELEMENT_NODE][0]
      ## check if its CD-SVG or CDML
      if doc.nodeName != 'cdml':
        ## first try if there is the right namespace
        if hasattr( doc, 'getElementsByTagNameNS'):
          docs = doc.getElementsByTagNameNS( data.cdml_namespace, 'cdml')
        else:
          Store.log( _("File was not loaded"), message_type="error")
          return None  # I don't know why this happens, but we simply ignore the document
        if docs:
          doc = docs[0]
        else:
          # if not, try it without it
          docs = doc.getElementsByTagName( 'cdml')
          if docs:
            # ask if we should proceed with incorrect namespace
            proceed = tkMessageBox.askokcancel( _("Proceed?"),
                                                _("CDML data seem present in SVG but have wrong namespace. Proceed?"),
                                                default='ok',
                                                parent=self)
            if proceed:
              doc = docs[0]
            else:
              Store.log(_("file not loaded"))
              return None
          else:
            ## sorry but there is no cdml in the svg file
            Store.log(_("cdml data are not present in SVG or are corrupted!"))
            return None
      self.paper.clean_paper()
      self.paper.read_package( doc, draw=draw)
      if type( self.mode) != str:
        self.mode.startup()
      Store.log( _("loaded file: ")+self.paper.full_path)
      self._record_recent_file( os.path.abspath( self.paper.full_path))
      return 1



  def save_SVG( self, file_name=None):
    if not file_name:
      svg_file = self.paper.get_base_name()+".svg"
      a = asksaveasfilename( defaultextension = ".svg", initialdir = self.svg_dir, initialfile = svg_file,
                             title = _("Export SVG"), parent = self, filetypes=((_("SVG file"),"*.svg"),))
    else:
      a = file_name
    if a != '':
      self.svg_dir, svg_file = os.path.split( a)
      try:
        inp = open( a, "wb")
      except IOError as x:
        raise ValueError("unable to open to file ", x)
      exporter = SVG_writer( self.paper)
      exporter.construct_dom_tree( self.paper.top_levels)
      dom_extensions.safe_indent( exporter.document.childNodes[0])
      inp.write( exporter.document.toxml().encode('utf-8'))
      inp.close()
      Store.log( _("exported to SVG file: ")+svg_file)




  def _update_geometry( self, e):
    pass



  def scale( self):
    dialog = dialogs.scale_dialog( self)
    if dialog.result:
      x, y = dialog.result
      self.paper.scale_selected( x/100,
                                 y/100,
                                 fix_centers=dialog.preserve_centers.get(),
                                 scale_font=dialog.scale_fonts.get())


    
  def get_name_dic( self, name='', local_file=0):
    if not name:
      while 1:
        name = 'untitled%d.svg' % self._untitled_counter
        self._untitled_counter += 1
        if not self.check_if_the_file_is_opened( name):
          break
      name_dic = {'name':name, 'dir':self.save_dir, 'auto': 1, 'ord': 0}
    else:
      dir, name = os.path.split( name)
      if not dir and not local_file:
        dir = self.save_dir
      elif not dir:
        # the file should be in the local directory
        dir = "./"
      name_dic = {'name':name, 'dir':dir, 'auto': 0, 'ord': 0}
      i = self.check_number_of_opened_same_names( name_dic)
      name_dic['ord'] = i
    return name_dic



  def _quit( self):
    while self.papers:
      if not self.close_current_paper( call_quit_if_no_remains=False):
        return
    if not self.in_batch_mode:
      # we dont save configuration if we are in batch mode
      # this leads to window having size 0x0 and similar problems
      if self.svg_dir:
        Store.pm.add_preference( "default-dir", os.path.abspath( self.save_dir))
      i = 0
      # save recent files
      for name in self._recent_files:
        i += 1
        Store.pm.add_preference( "recent-file%d" % i, name)
      self.save_configuration()
    self.quit()
    if os.name != "nt":
      sys.exit(0)

      
  def plugin_import( self, pl_id, filename=None):
    plugin = self.plugins[ pl_id]
    if not filename:
      if self.paper.changes_made:
        if tkMessageBox.askokcancel( _("Forget changes?"),_("Forget changes in currently visiting file?"), default='ok', parent=self) == 0:
          return 0
      types = []
      if 'extensions' in plugin.__dict__ and plugin.extensions:
        for e in plugin.extensions:
          types.append( (plugin.name+" "+_("file"), e))
      types.append( (_("All files"),"*"))
      a = askopenfilename( defaultextension = "",
                           initialdir = self.save_dir,
                           initialfile = self.save_file,
                           title = _("Load")+" "+plugin.name,
                           parent = self,
                           filetypes=types)
      if a:
        filename = a
      else:
        return 0
    # we have filename already
    if plugin.importer.gives_molecule:
      # plugins returning molecule need paper instance for molecule initialization
      importer = plugin.importer( self.paper)
    else:
      importer = plugin.importer()
    if importer.on_begin():
      cdml = None
      # some importers give back a cdml dom object
      if importer.gives_cdml:
        cdml = 1
        try:
          doc = importer.get_cdml_dom( filename)
        except plugins.plugin.import_exception as detail:
          tkMessageBox.showerror( _("Import error"), _("Plugin failed to import with following error:\n %s") % detail) 
          return 0
      # others give directly a molecule object
      elif importer.gives_molecule:
        cdml = 0
        try:
          doc = importer.get_molecules( filename)
        except plugins.plugin.import_exception as detail:
          tkMessageBox.showerror( _("Import error"), _("Plugin failed to import with following error:\n %s") % detail) 
      self.paper.clean_paper()
      if cdml == 0:
        # doc is a molecule
        self.paper.create_background()
        for m in doc:
          self.paper.stack.append( m)
          m.draw()
        self.paper.add_bindings()
        self.paper.start_new_undo_record()
      elif cdml:
        self.paper.read_package( doc)

      Store.log( _("loaded file: ")+filename)
      return 1


  def plugin_export( self, pl_id, filename=None, interactive=True, on_begin_attrs=None):
    """interactive attribute tells whether the plugin should be run in interactive mode"""
    plugin = self.plugins[ pl_id]
    exporter = plugin.exporter( self.paper)
    exporter.interactive = interactive and not self.in_batch_mode
    attrs = on_begin_attrs or {}
    if not exporter.on_begin( **attrs):
      return False
    if not filename:
      file_name = self.paper.get_base_name()
      types = []
      if 'extensions' in plugin.__dict__ and plugin.extensions:
        file_name += plugin.extensions[0]
        for e in plugin.extensions:
          types.append( (plugin.name+" "+_("file"), e))
      types.append( (_("All files"),"*"))

      a = asksaveasfilename( defaultextension = types[0][1],
                             initialdir = self.save_dir,
                             initialfile = file_name,
                             title = _("Export")+" "+plugin.name,
                             parent = self,
                             filetypes=types)
    else:
      a = filename
    if a:
      if not config.debug:
        try:
          doc = exporter.write_to_file( a)
        except:
          tkMessageBox.showerror( _("Export error"), _("Plugin failed to export with following error:\n %s") % sys.exc_info()[1])
          return False
      else:
        doc = exporter.write_to_file( a)
      Store.log( _("exported file: ")+a)
      return True
    return False



  def change_properties( self):
    dial = dialogs.file_properties_dialog( self, self.paper)



  def standard_values( self):
    dial = dialogs.standard_values_dialog( self, self.paper.standard)
    if dial.change:
      old_standard = self.paper.standard
      self.paper.standard = dial.standard
      # apply all values or only the changed ones
      if dial.apply_all:
        old_standard = None
      if not dial.apply:
        return
      elif dial.apply == 2:
        [o.redraw() for o in self.paper.apply_current_standard( old_standard=old_standard)]
      elif dial.apply == 1:
        [o.redraw() for o in self.paper.apply_current_standard( objects=self.paper.selected, old_standard=old_standard)]
      self.paper.add_bindings()
      self.paper.start_new_undo_record()
  



  def request( self, type, **options):
    """used by submodules etc. for requests of application wide resources such as pixmaps etc."""
    from . import pixmaps
    if type == 'pixmap':
      if 'name' in options:
        name = options['name']
        if name in pixmaps.images:
          return pixmaps.images[ name]
        else:
          return None
      return None
    

  def read_smiles( self, smiles=None):
    if not oasa_bridge.oasa_available:
      return 
    lt = _("""Before you use this tool, be warned that not all features of SMILES are currently supported.
There is no support for stereo-related information, for the square brackets [] and a few more things.

Enter SMILES:""")
    if not smiles:
      dial = Pmw.PromptDialog( self,
                               title='Smiles',
                               label_text=lt,
                               entryfield_labelpos = 'n',
                               buttons=(_('OK'),_('Cancel')))
      res = dial.activate()
      if res == _('OK'):
        text = dial.get()
      else:
        return
    else:
      text = smiles

    if text:
      #      try:
      mol = oasa_bridge.read_smiles( text, self.paper)
##       except :
##      if not smiles:
##        tkMessageBox.showerror( _("Error processing %s") % 'SMILES',
##                                _("The oasa library ended with error:\n%s") % sys.exc_info()[1])
##      return
      self.paper.stack.append( mol)
      mol.draw()
      self.paper.add_bindings()
      self.paper.start_new_undo_record()
      return mol



  def read_inchi( self, inchi=None):
    if not oasa_bridge.oasa_available:
      return 
    lt = _("""Before you use his tool, be warned that not all features of InChI are currently supported.
There is no support for stereo-related information, isotopes and a few more things.
The InChI should be entered in the plain text form, e.g.- 1/C7H8/1-7-5-3-2-4-6-7/1H3,2-6H

Enter InChI:""")
    text = None
    if not inchi:
      dial = Pmw.PromptDialog( self,
                               title='InChI',
                               label_text=lt,
                               entryfield_labelpos = 'n',
                               buttons=(_('OK'),_('Cancel')))
      res = dial.activate()
      if res == _('OK'):
        text = dial.get()
    else:
      text = inchi

    if text:
      if config.devel:
        # in development mode we do not want to catch the exceptions
        mol = oasa_bridge.read_inchi( text, self.paper)
      else:
        try:
          mol = oasa_bridge.read_inchi( text, self.paper)
        except oasa.oasa_exceptions.oasa_not_implemented_error as e:
          if not inchi:
            tkMessageBox.showerror( _("Error processing %s") % 'InChI',
                                    _("Some feature of the submitted InChI is not supported.\n\nYou have most probaly submitted a multicomponent structure (having a . in the sumary layer"))
            return
          else:
            raise ValueError("the processing of inchi failed with following error %s" % sys.exc_info()[1])
        except oasa.oasa_exceptions.oasa_inchi_error as e:
          if not inchi:
            tkMessageBox.showerror( _("Error processing %s") % 'InChI',
                                    _("There was an error reading the submitted InChI.\n\nIf you are sure it is a valid InChI, please send me a bug report."))
            return
          else:
            raise ValueError("the processing of inchi failed with following error %s" % sys.exc_info()[1])
        except oasa.oasa_exceptions.oasa_unsupported_inchi_version_error as e:
          if not inchi:
            tkMessageBox.showerror( _("Error processing %s") % 'InChI',
                                    _("The submitted InChI has unsupported version '%s'.\n\nYou migth try resubmitting with the version string (the first part of InChI) changed to '1'.") % e.version)
            return
          else:
            raise ValueError("the processing of inchi failed with following error %s" % sys.exc_info()[1])
        except:
          
          if not inchi:
            tkMessageBox.showerror( _("Error processing %s") % 'InChI',
                                    _("The reading of InChI failed with following error:\n\n'%s'\n\nIf you are sure you have submitted a valid InChI, please send me a bug report.") % sys.exc_info()[1])
            return
          else:
            raise ValueError("the processing of inchi failed with following error %s" % sys.exc_info()[1])

      self.paper.stack.append( mol)
      mol.draw()
      self.paper.add_bindings()
      self.paper.start_new_undo_record()




  def gen_smiles( self):
    if not oasa_bridge.oasa_available:
      return
    u, i = self.paper.selected_to_unique_top_levels()
    if not interactors.check_validity( u):
      return
    sms = []
    for m in u:
      if m.object_type == 'molecule':
        try:
          sms.append( oasa_bridge.mol_to_smiles( m))
        except Exception as e:
          tkMessageBox.showerror( _("Error generating %s") % 'SMILES',
                                _("The oasa library ended with error:\n%s") % str(e))
          return
    text = '\n\n'.join( sms)
    dial = Pmw.TextDialog( self,
                           title=_('Generated SMILES'),
                           buttons=(_('OK'),))
    dial.insert( 'end', text)
    dial.activate()
    

  def put_to_clipboard( self, xml, pos):
    self._clipboard = xml
    self._clipboard_pos = pos

  def get_clipboard( self):
    return self._clipboard

  def get_clipboard_pos( self):
    return self._clipboard_pos


##   def get_named_paper( self, name):
##     for p in self.papers:
##       if p.get_base_name() == name:
##         return p
##     return None


  def check_if_the_file_is_opened( self, name, check_current=1):
    """check_current says if the self.paper should be also included into the check,
    this is usefull to make it 0 for renames"""
    for p in self.papers:
      if not check_current and p == self.paper:
        continue
      if p.full_path == os.path.abspath( name):
        return p
    return None
      
  def check_number_of_opened_same_names( self, name):
    """checks if there are papers with same name and returns the highest value"""
    ps = [p.file_name['ord'] for p in self.papers if p.file_name['name'] == name['name']]
    if not ps:
      return 0
    else:
      return max( ps)+1



  def start_server( self):

    import http_server2 as http_server
    
    server_address = ('', 8008)
    httpd = http_server.bkchem_http_server( server_address, http_server.bkchem_http_handler)

    import threading

    t = threading.Thread( target=httpd.serve_forever, name='server')
    t.setDaemon( 1)
    t.start()


    # soap
    import SOAPpy as SOAP
    CAL_NS = "http://beda.zirael.org/pokusy"
    server = SOAP.SOAPServer(("localhost", 8888))
    server.registerObject(self, CAL_NS)
    print("Starting server...")
    t = threading.Thread( target=server.serve_forever, name='soap')
    t.setDaemon( 1)
    t.start()




  def get_new_tab_name( self):
    self.__last_tab += 1
    return "tab"+str(self.__last_tab)




  def get_paper_tab_name( self, paper):
    for k in self.__tab_name_2_paper:
      if self.__tab_name_2_paper[ k] == paper:
        return k
    return None



  def read_user_templates( self):
    [Store.utm.add_template_from_CDML( n) for n in os_support.get_local_templates()]



  def gen_inchi( self):
    program = Store.pm.get_preference( "inchi_program_path")
    self.paper.swap_sides_of_selected("horizontal")
    if not oasa_bridge.oasa_available:
      return
    u, i = self.paper.selected_to_unique_top_levels()
    sms = []
    if not interactors.check_validity( u):
      return

    try:
      for m in u:
        if m.object_type == 'molecule':
            inchi, key, warning = oasa_bridge.mol_to_inchi( m, program)
            sms = sms + warning
            sms.append(inchi)
            sms.append("InChIKey="+key)
            sms.append("")
    except oasa.oasa_exceptions.oasa_inchi_error as e:
      sms = [_("InChI generation failed,"),_("make sure the path to the InChI program is correct in 'Options/InChI program path'"), "", str( e)]
    except:
      sms = [_("Unknown error occured during InChI generation, sorry."), _("Please, try to make sure the path to the InChI program is correct in 'Options/InChI program path'")]
    self.paper.swap_sides_of_selected("horizontal")
    text = '\n'.join( sms)
    dial = Pmw.TextDialog( self,
                           title=_('Generated InChIs'),
                           buttons=(_('OK'),))
    dial.insert( 'end', text)
    dial.activate()


  def save_configuration( self):
    Store.pm.add_preference( 'geometry', self.winfo_geometry())
    # store logging settings
    if not self.in_batch_mode:
      # we do not save (or load) handling info when in batch mode
      for key,value in Store.logger.handling.items():
        Store.pm.add_preference( "logging_%s"%key, value)
    f = os_support.get_opened_config_file( "prefs.xml", level="personal", mode="w")
    if f:
      Store.pm.write_to_file( f)
      f.close()


  def run_plugin( self, name):
    p = self.paper
    self.plug_man.run_plugin( name)
    if p == self.paper:
      # we update bindings and start_new_undo_record only if the paper did not change during the run
      self.paper.add_bindings()
      self.paper.start_new_undo_record()



  def save_as_template( self):
    name = interactors.save_as_template( self.paper)
    if name:
      self.save_CDML( name=name, update_default_dir=0)
      Store.log( _("The file was saved as a template %s") % name)




  def clean( self):
    self.paper.clean_selected()

    

  def update_cursor_position( self, x, y):
    self.cursor_position.set( "(%d, %d)" % (x,y))

    

  def update_menu_after_selection_change( self, e):
    for temp in self.menu_template:
      if temp[1] == "command" and temp[6] != None:
        state = temp[6]
        if callable( state):
          state = state() and 'normal' or 'disabled'
        elif state not in  ('normal', 'disabled'):
          state = getattr( self.paper, temp[6]) and 'normal' or 'disabled'
        try:
          self.menu.component( temp[0] + "-menu").entryconfigure( temp[2], state=state)
        except:
          pass  # Silently ignore if menu item doesn't exist yet




  def _record_recent_file( self, name):
    if name in self._recent_files:
      self._recent_files.remove( name)
    self._recent_files.insert( 0, name)
    if len( self._recent_files) > 5:
      self._recent_files = self._recent_files[0:5]



  def ask_preferences( self):
    pd = dialogs.preferences_dialog( self, Store.pm)
    if pd.result == 1:
      for i in self.papers:
        i._paper_properties['use_real_minus'] = Store.pm.get_preference("use_real_minus")
        [j.redraw() for j in i.stack]



  ## ------------------------------ THE BATCH MODE ------------------------------


  def process_batch( self, opts):

    if opts[0] == "-b":
      plugin = opts[1]

      the_globals = {'App': Store.app,
                     'Args': opts[2:]}

      exec(compile(open(plugin).read(), plugin, "exec"), the_globals)



def main():
  """Entry point for the BKChem application."""
  import sys
  import os
  
  # Create and run the application
  app = BKChem()
  app.initialize()  # This is the missing call!
  app.mainloop()


if __name__ == "__main__":
  main()
