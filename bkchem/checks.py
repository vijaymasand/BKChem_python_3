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


"""this module contains functions used for various checks and maintanence
throughout BKChem - mainly from paper and modules"""



from . import interactors
from .singleton_store import Store



def check_linear_fragments( paper):
  """checks the state of linear fragments present on the paper and resets their appearance"""
  #mols = paper.um.get_changed_molecules()
  last_record = paper.um.get_last_record()
  for mol in paper.molecules:
    to_del = set()
    fs = [f for f in mol.fragments if f.type == "linear_form"]
    if fs and (last_record == None or last_record.object_changed( mol)):
      for f in fs:
        if mol.check_linear_form_fragment( f) == False:
          to_del.add( f)
    for f in to_del:
      Store.log( _('The linear form was no longer consistent - it has been removed'))
      mol.delete_fragment( f)
