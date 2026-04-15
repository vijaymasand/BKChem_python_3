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

"""support for backward compatible CDML reading"""

from . import dom_extensions as dom_ext      
from . import data

class CDML_transformer_06_07:

  output_version = '0.7'
  input_version = '0.6'

  def tranform_dom( self, dom):
    for b in dom.getElementsByTagName( 'bond'):
      type = b.getAttribute( 'type')
      if type == 'forth':
        b.setAttribute( 'type', 'up')


class CDML_transformer_07_08:

  output_version = '0.8'
  input_version = '0.7'

  def tranform_dom( self, dom):
    types = { 'single': 's', 'double': 'd', 'triple': 't', 'up': 'w', 'back': 'h'}
    for b in dom.getElementsByTagName( 'bond'):
      type = b.getAttribute( 'type')
      if type in types:
        t = types[ type]
        b.setAttribute( 'type', t)

class CDML_transformer_08_09:

  output_version = '0.9'
  input_version = '0.8'

  def tranform_dom( self, dom):
    pass


class CDML_transformer_09_10:

  output_version = '0.10'
  input_version = '0.9'

  def tranform_dom( self, dom):
    if dom.nodeName == 'cdml':
      cdml = dom
    else:
      cdml = dom.getElementsByTagName('cdml')[0]
    if cdml.getElementsByTagName( 'standard'):
      return
    standard = dom_ext.elementUnder( cdml, 'standard',
                                     (('font_family','helvetica'),
                                      ('font_size','12'),
                                      ('line_width','1.0px')))
    dom_ext.elementUnder( standard, 'bond',
                          (('double-ratio','1'),
                           ('length','1.0cm'),
                           ('width','6.0px'),
                           ('wedge-width','2.0px')))
    dom_ext.elementUnder( standard, 'arrow',
                          (('length','1.6cm'),))


class CDML_transformer_10_11:

  output_version = '0.11'
  input_version = '0.10'
  bond_type_remap = ['','n1','n2','n3','w1','h1']

  def tranform_dom( self, dom):
    for b in dom.getElementsByTagName("bond"):
      # bond remap
      type = b.getAttribute( 'type')
      if not type:
        continue
      elif type in data.alternative_bond_types:
        type = data.alternative_bond_types.index( type)
      elif type in data.bond_types:
        type = data.alternative_bond_types.index( type)
      else:
        try:
          type = int( type)
        except:
          continue
      type = self.bond_type_remap[ type]
      b.setAttribute('type', type)
      # other remaps
      # distance
      d = b.getAttribute( 'distance')
      if d:
        if type[0] == 'n':
          b.setAttribute( 'bond_width', d)
        else:
          d = float( d)
          # the drawing code was changed and divides by 2 now
          b.setAttribute( 'wedge_width', str(2*d))
        b.removeAttribute( 'distance')
      # line_width
      w = b.getAttribute( 'width')
      if w:
        b.setAttribute( 'line_width', w)
        b.removeAttribute( 'width')


class CDML_transformer_11_12:

  output_version = '0.12'
  input_version = '0.11'

  def tranform_dom( self, dom):
    pass



class CDML_transformer_12_13:

  output_version = '0.13'
  input_version = '0.12'

  def tranform_dom( self, dom):
    for a in dom.getElementsByTagName( 'atom'):
      ch = a.getAttribute("charge") or 0
      for m in a.getElementsByTagName( 'mark'):
        if m.getAttribute( 'type') == 'plus':
          ch += 1
        elif m.getAttribute( 'type') == 'minus':
          ch -= 1
      a.setAttribute( 'charge', str( ch))
      


class CDML_transformer_13_14:

  output_version = '0.14'
  input_version = '0.13'

  def tranform_dom( self, dom):
    for a in dom.getElementsByTagName( 'atom'):
      name = a.getAttribute( "name")
      if not name:
        a.tagName = "text"
      elif name in ('OCH3','NO2','COOH','COOCH3','Me','CN','SO3H','PPh3','OMe','Et','Ph','COCl','CH2OH'):
        a.tagName = "group"
        a.setAttribute( "group-type", "builtin")
      else:
        pass
      


class CDML_transformer_14_15:

  """CDML version 0.15 adds line_width attribute to the electronpair mark,
  also multiplicity is now stored explicitly"""

  output_version = '0.15'
  input_version = '0.14'

  def tranform_dom( self, dom):
    for a in dom.getElementsByTagName( 'atom'):
      multiplicity = 1
      for m in a.getElementsByTagName( 'mark'):
        if m.getAttribute( "type") == "electronpair":
          if not m.getAttribute( "line_width"):
            size = float( m.getAttribute( "size"))
            m.setAttribute( "line_width", str( round( round( size /2)/2)))
        if m.getAttribute( "type") == "radical":
          multiplicity += 1
        elif m.getAttribute( "type") == "biradical":
          multiplicity += 2
      if not a.hasAttribute("multiplicity"):
        a.setAttribute( "multiplicity", multiplicity)


class CDML_transformer_15_16:

  """CDML version 0.16 stores rich text as escaped value, not directly in XML -
  that is '&lt;i>x&lt;/i>' instead of '<i>x</i>'
  """

  output_version = '0.16'
  input_version = '0.15'

  def tranform_dom( self, dom):
    for a in dom.getElementsByTagName( 'ftext'):
      text = ""
      for ch in a.childNodes[:]:
        text += ch.toxml()
        a.removeChild( ch)
      a.appendChild( dom.ownerDocument.createTextNode( text))


# LIST OF AVAILABLE TRANSFORMERS

transformers = { '0.6': CDML_transformer_06_07,
                 '0.7': CDML_transformer_07_08,
                 '0.8': CDML_transformer_08_09,
                 '0.9': CDML_transformer_09_10,
                 '0.10': CDML_transformer_10_11,
                 '0.11': CDML_transformer_11_12,
                 '0.12': CDML_transformer_12_13,
                 '0.13': CDML_transformer_13_14,
                 '0.14': CDML_transformer_14_15,
                 '0.15': CDML_transformer_15_16,
                 }

# TRANSFORMING FUNCTION

def transform_dom_to_version( dom, version):
  """does inplace transformation of the dom tree to requested version, returns 1 on success"""
  in_ver = dom.getAttribute( 'version')
  if not in_ver:
    return 0
  out_ver = version
  trans = []
  while in_ver != out_ver:
    if in_ver in transformers:
      trans.append( transformers[ in_ver]())
      in_ver = trans[-1].output_version
    else:
      return 0
  for tr in trans:
    tr.tranform_dom( dom)
  return 1
