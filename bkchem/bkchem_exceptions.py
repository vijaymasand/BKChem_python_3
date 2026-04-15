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


class bkchem_error( Exception):

  def __init__( self):
    Exception.__init__( self)    




class bkchem_graph_error( bkchem_error):
  """exception for reporting graph related exceptions"""

  def __init__( self, id, value):
    self.id = id
    self.value = value


  def __str__( self):
    print("BKChem graph error, id=%s, value=%s" % (self.id, self.value))





class bkchem_fragment_error( bkchem_error):
  """exceptions related to fragments consistency etc.
  ids: inconsistent"""

  def __init__( self, id, value):
    self.id = id
    self.value = value


  def __str__( self):
    print("BKChem fragments error, id=%s, value=%s" % (self.id, self.value))


  
