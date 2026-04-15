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


"""This file stores the oldest parents of used classes which are used to provide
mostly the desired meta_behaviour"""


from . import misc
from .singleton_store import Store
import xml.dom.minidom as dom
from . import dom_extensions
from . import ftext


class simple_parent( object):
  """this class only gives reasonable default values to meta attributes"""
  object_type = "object"
  # if a class is a container in paper meaning (is not part of bigger structure)
  meta__is_container = 0

  # class is not made up from smaller parts that define the structure (points etc.)
  # if non zero then specifies the number of coordinate pairs
  meta__has_simple_coords = 1
  # undo related
  meta__undo_fake = () # fakes serve only to force redraw in some cases however do not perform any undo
  meta__undo_simple = ()
  meta__undo_properties = ()
  meta__undo_copy = ()
  meta__undo_children_to_record = ()


  def __init__( self):
    pass


  def copy_settings( self, other):
    pass



class id_enabled( simple_parent):
  """the basic parent that has something to do with the paper, it provides id support"""

  def __init__( self):
    simple_parent.__init__( self)


  def generate_id( self):
    self.id = self._generate_id()


  def _generate_id( self):
    return Store.id_manager.generate_and_register_id( self, prefix=self.object_type)

  # id
  def _get_id( self):
    try:
      return self.__id
    except AttributeError:
      self.__id = self._generate_id()
    return self.__id

  def _set_id( self, id):
    if Store.id_manager.is_registered_object( self):
      Store.id_manager.unregister_object( self) 
    Store.id_manager.register_id( self, id)
    self.__id = id

  id = property( _get_id, _set_id)
  

  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    pass
    #other.id = self.id

    


class meta_enabled( id_enabled):
  """class that has usefull behaviour implemented according to meta infomation"""

  meta__used_standard_values = []

  def __init__( self, standard=None):
    id_enabled.__init__( self)
    if standard:
      self.read_standard_values( standard)

  def read_standard_values( self, standard, old_standard=None):
    """if old_standard is given the recent value is read from standard
    only if it differs from the old one - used for 'inteligent' changes of
    standard properties of existing drawing"""
    for i in self.meta__used_standard_values:
      if old_standard and (standard.__dict__[i] == old_standard.__dict__[i]):
        continue
      else:
	# properties
        is_prop = 0
        for p in self.__class__.mro():
          if i in p.__dict__:
            p.__dict__[i].fset( self, standard.__dict__[i])
            is_prop = 1
            break
        if not is_prop:
          self.__dict__[i] = standard.__dict__[i]





class drawable( simple_parent):
  """basic class for all drawable type - sets the dirty property and the
  move, draw and redraw methods"""

  def __init__( self):
    simple_parent.__init__( self)
    self.dirty = 0


  # public properties

  # dirty
  def _get_dirty( self):
    return self.__dirty

  def _set_dirty( self, dirty):
    self.__dirty = dirty

  dirty = property( _get_dirty, _set_dirty)

  
  # public methods
  def move( self, dx, dy):
    pass

  def draw( self):
    pass

  def redraw( self):
    pass






class point_drawable( drawable):
  """this is a specialized drawable that is of point nature - that is has x,y coords
  that define its position"""

  meta__undo_properties = ("x","y")

  def __init__( self):
    drawable.__init__( self)
    self.x = 0
    self.y = 0

  # public properties

  # x
  def _get_x( self):
    return self.__x

  def _set_x( self, x):
    self.__x = x
    self.dirty = 1

  x = property( _get_x, _set_x)

  # y
  def _get_y( self):
    return self.__y

  def _set_y( self, y):
    self.__y = y
    self.dirty = 1

  y = property( _get_y, _set_y)


  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    drawable.copy_settings( self, other)
    other.x = self.x
    other.y = self.y





class with_line( simple_parent):

  meta__undo_properties = ("line_width",)
  
  # line_width
  def _get_line_width( self):
    return self.__line_width

  def _set_line_width( self, line_width):
    self.__line_width = line_width
    self.dirty = 1

  line_width = property( _get_line_width, _set_line_width)
  

  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    simple_parent.copy_settings( self, other)
    other.line_width = self.line_width





class line_colored( simple_parent):
  """parent for objects having line shape and thus defining only one color -
  the line_color"""

  meta__undo_properties = ("line_color",)
  

  def __init__( self):
    simple_parent.__init__( self)
    self.line_color = '#000'

  # public properties

  # line_color
  def _get_line_color( self):
    return self.__line_color

  def _set_line_color( self, line_color):
    self.__line_color = line_color
    self.dirty = 1

  line_color = property( _get_line_color, _set_line_color)


  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    simple_parent.copy_settings( self, other)
    other.line_color = self.line_color


  


class area_colored( line_colored):

  meta__undo_properties = line_colored.meta__undo_properties + \
                          ("area_color",)
  
  def __init__( self):
    line_colored.__init__( self)
    self.area_color = '#ffffff'

  # public properties

  # area_color
  def _get_area_color( self):
    return self._area_color

  def _set_area_color( self, area_color):
    self._area_color = area_color
    self.dirty = 1

  area_color = property( _get_area_color, _set_area_color)


  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    line_colored.copy_settings( self, other)
    other.area_color = self.area_color




class with_font( simple_parent):
  """for text like objects needing font_size and font_family properties, however not variable text"""

  meta__undo_properties = ("font_size", "font_family")


  def __init__( self):
    simple_parent.__init__( self)
    self.font_size = 10
    self.font_family = 'helvetica'


  # font_size
  def _get_font_size( self):
    return self.__font_size

  def _set_font_size( self, font_size):
    self.__font_size = font_size
    self.dirty = 1

  font_size = property( _get_font_size, _set_font_size)


  # font_family
  def _get_font_family( self):
    return self.__font_family

  def _set_font_family( self, font_family):
    self.__font_family = font_family
    self.dirty = 1

  font_family = property( _get_font_family, _set_font_family)


  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    simple_parent.copy_settings( self, other)
    other.font_family = self.font_family
    other.font_size = self.font_size




class text_like( with_font):
  """for text like objects needing font_size and font_family properties and variable text and xml_ftext"""


  def __init__( self):
    with_font.__init__( self)


  # text
  def _get_text( self):
    doc = dom.parseString( ftext.ftext.sanitize_text( self.xml_ftext))
    return dom_extensions.getAllTextFromElement( doc)

  text = property( _get_text, None, None,
                   "the unmarked plain-text representing the object - it is taken from xml_ftext and the markup is stripped")
 

  # xml_ftext
  def _get_xml_ftext( self):
    return ""

  xml_ftext = property( _get_xml_ftext, None, None, "the text used for rendering using the ftext class")






class interactive( simple_parent):

  def focus( self):
    pass

  def unfocus( self):
    pass

  def select( self):
    pass

  def unselect( self):
    pass




class container( simple_parent):

  # shape_defining_points
  def _get_shape_defining_points( self):
    return []

  shape_defining_points = property( _get_shape_defining_points, None, None,
                                    "should give list of point_drawable instances")


  # children
  def _get_children( self):
    return self.shape_defining_points

  children = property( _get_children, None, None,
                       "should give list of child instances, by default is alias for self.shape_defining_points")

##   # iterator
##   def __iter__( self):
##     return self

##   def next( self):

  



class child( simple_parent):

  # parent
  def _get_parent( self):
    return None

  def _set_parent( self, par):
    pass

  parent = property( _get_parent, _set_parent, None,
                     "should give a container")


  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    simple_parent.copy_settings( self, other)
    other.parent = self.parent



class top_level:

  pass




class with_paper( object):

  # paper
  def _get_paper( self):
    return self._paper

  def _set_paper( self, paper):
    self._paper = paper

  paper = property( _get_paper, _set_paper, None, "the paper that the object is drawn onto")



class child_with_paper( child, with_paper):

  # paper
  def _get_paper( self):
    if self.parent:
      return self.parent.paper
    else:
      return None

  def _set_paper( self, paper):
    raise KeyError("trying to set paper in a child - set it in parent instead")

  paper = property( _get_paper, _set_paper, None, "the paper that the object is drawn onto")





