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
#
#
#
#--------------------------------------------------------------------------

"""parent classes for import-export plugins"""

import sys
sys.path.append('../')

import xml.dom.minidom as dom


class importer:

  gives_cdml = 1
  gives_molecule = 0

  def __init__( self):
    pass

  def on_begin( self):
    """this method is called before every import"""
    return 1

  def get_cdml_dom( self, file_name):
    return None

  def get_molecules( self, file_name):
    return []
 
  
class exporter:

  def __init__( self, paper):
    self.paper = paper
    self.interactive = True # whether the exporter should ask anything

  def on_begin( self):
    return 1

  def write_to_file( self, file_name):
    pass


class import_exception( Exception):
  def __init__( self, value):
    self.value = value

  def __str__( self):
    return self.value


class export_exception( Exception):
  def __init__( self, value):
    self.value = value

  def __str__( self):
    return self.value

  
