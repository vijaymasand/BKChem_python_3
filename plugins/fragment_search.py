
from singleton_store import Store
import os
import logger
import time
import tkinter.filedialog as tkFileDialog
import dialogs



def process_directory( directory):
  files = 0
  matching = 0

  dialog = dialogs.progress_dialog( App, title=_("Search progress"))

  files_to_go = [f for f in [os.path.join( directory, filename) for filename in os.listdir( directory)] if os.path.isfile( f) and os.path.splitext( f)[1] in (".svg",".cdml")]

  for f in files_to_go: 
    #print f
    dialog.update( files/len(files_to_go), top_text=os.path.split( f)[1], bottom_text=_("Found: %d matching") % matching)
    files += 1
    App.in_batch_mode = True
    if App.add_new_paper( name=f):
      if App._load_CDML_file( f, draw=False):
        found = False
        for mol in App.paper.molecules:
          gen = mol.select_matching_substructures( fragment, implicit_freesites=True)
          try:
            next(gen)
          except StopIteration:
            pass
          else:
            found = True
            matching += 1
            mol.clean_after_search( fragment)
            break
        if not found:
          App.close_current_paper()
        else:
          App.in_batch_mode = False
          [o.draw() for o in App.paper.stack]
          App.paper.set_bindings()
          App.paper.add_bindings()
      else:
        App.close_current_paper()          

  App.in_batch_mode = False
  dialog.close()
  return files



t = time.time()
selected_mols = [o for o in App.paper.selected_to_unique_top_levels()[0] if o.object_type == 'molecule']
if not selected_mols and len( App.paper.molecules) == 1:
  selected_mols = App.paper.molecules


if len( selected_mols) > 1:
  Store.log( _("Select only one molecule"), message_type="error")

elif len( selected_mols) == 0:
  Store.log( _("Draw a molecule that you want to use as the fragment for search"), message_type="error")

else:
  # we may proceed
  fragment = selected_mols[0]

  directory = tkFileDialog.askdirectory( parent=App,
                                         initialdir=App.save_dir or "./")

  if directory:
    Store.logger.handling = logger.ignorant
    files = process_directory( directory)

    t = time.time() - t
    #print "%d files, %.2fs, %.2fms per file" % (files, t, 1000*(t/files))

    Store.logger.handling = logger.normal
    if files:
      Store.log( _("Searched %d files, %.2fs, %.2fms per file") % (files, t, 1000*(t/files)))
    else:
      Store.log( _("No files to search in were found"))
