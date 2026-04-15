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



import os
import sys

env_vars = {'template': 'BKCHEM_TEMPLATE_PATH',
            'pixmap': 'BKCHEM_PIXMAP_PATH',
            'image': 'BKCHEM_IMAGE_PATH',
            'plugin': 'BKCHEM_PLUGIN_PATH'}

std_dirs = {'template': 'templates',
            'pixmap': 'pixmaps',
            'image': '../images',
            'plugin': '../plugins'}


class os_support_store:
  private_dir_override = None



try:
  import site_config
except:
  site_config = None


def get_path( filename, file_category):
  dir = None
  dirs = get_dirs( file_category)
  for dir in dirs:
    path = os.path.join( dir, filename)
    if os.path.isfile( path):
      break

  if dir:
    path = os.path.join( dir, filename)
    if os.path.isfile( path):
      return path
  return None



def get_config_filename( name, level="global", mode="r"):
  dir = None
  if level == "global":
    if os.name in ('posix', 'nt'):
      dir = (site_config and site_config.BKCHEM_MODULE_PATH) or os.getenv( 'BKCHEM_MODULE_PATH') or os.path.join('..','.bkchem')
  elif level == "local":
    if os.name in ('posix', 'nt'):
      dir = (site_config and site_config.BKCHEM_MODULE_PATH) or os.getenv( 'BKCHEM_MODULE_PATH') or None
  if level == "personal":
    if os.name in ('posix', 'nt'):
      dir = get_personal_config_directory()

  if dir:
    if mode == "w":
      if not os.path.isdir( dir):
        try:
          os.mkdir( dir)
        except:
          return None
      if os.access( dir, os.W_OK):
        return os.path.join( dir, name)
      else:
        return None
    elif mode == "r":
      path = os.path.join( dir, name)
      if os.access( path, os.R_OK):
        return path
      else:
        return None
  return None





def get_dirs( file_category):
  if os.name in ('posix', 'nt'):
    if os.getenv( env_vars[ file_category]):
      dirs = [os.getenv( env_vars[ file_category])]
    elif site_config:
      dirs = [site_config.__dict__[ env_vars[ file_category]]]
    else:
      dirs = []
    dirs.extend( (os.path.join( get_bkchem_run_dir(), std_dirs[ file_category]),))
  else:
    dirs = std_dirs[ file_category]

  return dirs



def get_local_templates():
  dir = get_local_templates_path()
  if os.path.isdir( dir):
    return [os.path.join( dir, d) for d in os.listdir( dir) if os.path.splitext( d)[1] in ('.cdml', '.cdgz', '.svg', '.svgz')] 
  return []




def get_personal_config_directory():
  return get_bkchem_private_dir()
  



def create_personal_config_directory( path=""):
  if not path:
    dir = get_personal_config_directory()
  else:
    dir = os.path.join( get_personal_config_directory(), path)
  if dir:
    if not os.path.isdir( dir):
      try:
        os.mkdir( dir)
      except:
        return None
    if os.access( dir, os.W_OK):
      return dir
    else:
      return None
  return None




def get_local_templates_path():
  return os.path.join( get_personal_config_directory(), 'templates')
  



def get_module_path():
  dir = (site_config and site_config.BKCHEM_MODULE_PATH) or os.getenv( 'BKCHEM_MODULE_PATH') or './'
  return dir


def get_opened_config_file( name, level="global", mode="r"):
  fname = get_config_filename( name, level=level, mode=mode)
  if fname:
    f = open( fname, mode=mode)
    return f


def set_bkchem_private_dir( dir):
  if os.path.exists( dir):
    os_support_store.private_dir_override = dir


def get_bkchem_private_dir():
  # this allows users to override the private dir
  if os_support_store.private_dir_override and os.path.exists( os_support_store.private_dir_override):
    return os_support_store.private_dir_override
  dir = ""
  if os.name == "nt":
    try:
      import winreg as reg
      dir = reg.QueryValueEx( reg.OpenKey( reg.HKEY_CURRENT_USER, "Volatile Environment"), "APPDATA")[0]
      dir = os.path.join( dir, "bkchem")
    except EnvironmentError:
      pass

  if not dir:
    dir = os.getenv( 'HOME') or '../'
    dir = os.path.join( dir, ".bkchem/")
  return dir
  



def get_bkchem_run_dir():
  """returns directory from which BKChem is run"""
  # When installed as a package, use the package directory
  # This handles both 'python -m bkchem.main' and running from source
  path = os.path.dirname(os.path.abspath(__file__))
  return path

