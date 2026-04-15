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


"""this module contains most of the data that are not module specific.
Serves as central storage of text and other data"""

# Internationalization
try:
    _
except NameError:
    _ = lambda x: x

booleans = ['no', 'yes']
on_off = ['off', 'on']

# note that 'no' is there just to shift the index of single to 1
bond_types = ['no','single', 'double','triple','wedge','hatch']
alternative_bond_types = ['n','s', 'd','t','w','h']
numbered_bond_types = ['no','1', '2','3','W','H']

# support for plugable draw methods
# the remaping to new style of bond type names
bond_type_remap = ['','n1','n2','n3','w1','h1']


special_key_symbols = { 'Control_L':'C',
                        'Control_R':'C',
                        'Alt_L':'A',
                        'Alt_R':'A',
                        'Meta_L':'M',
                        'Meta_R':'M',
                        'Shift_L':'S',
                        'Shift_R':'S'}

#key symbols that have same name, but different character when pressed with Ctrl
#we need to capture them to avoid confusion in mode.register_key_sequence
strange_key_symbols = { 'slash': '/',
                        'backslash': '\\',
                        'grave': '`',
                        'question': '?'}
  

#fonts that are guaranteed by Tk to be always available
always_available_fonts = ('helvetica', 'courier', 'times')

align_modes = { 't': 'Top',
                'b': 'Bottom',
                'l': 'Left',
                'r': 'Right',
                'v': 'Vertical center',
                'h': 'Horizontal center'}



cdml_namespace = 'http://www.freesoftware.fsf.org/bkchem/cdml'


# types of vector graphics
vector_graphics_types = ('oval', 'rect', 'polygon','polyline')


# names of all objects that have their own element under <cdml> in CDML - for reading
loadable_types = ('molecule', 'arrow', 'plus', 'text', 'rect', 'oval', 'polygon', 'circle', 'square', 'reaction','polyline') 


paper_types = {
  'A0': [1189, 841],
  'A1': [841, 594],
  'A10': [37, 26],
  'A2': [594, 420],
  'A3': [420, 297],
  'A4': [297, 210],
  'A5': [210, 148],
  'A6': [148, 105],
  'A7': [105, 74],
  'A8': [74, 52],
  'A9': [52, 37],
  'B0': [1414, 1000],
  'B1': [1000, 707],
  'B10': [44, 31],
  'B2': [707, 500],
  'B3': [500, 353],
  'B4': [353, 250],
  'B5': [250, 176],
  'B6': [176, 125],
  'B7': [125, 88],
  'B8': [88, 62],
  'B9': [62, 44],
  'C0': [1297, 917],
  'C1': [917, 648],
  'C10': [40, 28],
  'C2': [648, 458],
  'C3': [458, 324],
  'C4': [324, 229],
  'C5': [229, 162],
  'C6': [162, 114],
  'C7': [114, 81],
  'C8': [81, 57],
  'C9': [57, 40],
  'Ledger': [279, 432],
  'Legal': [215.9, 355.7],
  'Letter': [215.9, 279.4],
  'Tabloid': [432, 279],
  }






# index codes for meta__configurable

FROM_STRING = 0
TO_STRING = 1


languages = {'en': _('English'),
             'cs': _('Czech'),
             'de': _('German'),
             'fr': _('French'),
             'pl': _('Polish'),
             'tw': _('Traditional Chinese'),
             'it': _('Italian'),
             'es': _('Spanish'),
             'ja': _('Japanese'),
             'lv': _('Latvian'),
             }



roman_numbers = {0: '0',
                 1: 'I',
                 2: 'II',
                 3: 'III',
                 4: 'IV',
                 5: 'V',
                 6: 'VI',
                 7: 'VII',
                 8: 'VIII',
                 9: 'IX',
                 10: 'X',
                 -1: '-I',
                 -2: '-II',
                 -3: '-III',
                 -4: '-IV',
                 -5: '-V',
                 -6: '-VI',
                 -7: '-VII',
                 -8: '-VIII',
                 -9: '-IX',
                 -10: '-X'
                 }
                 
