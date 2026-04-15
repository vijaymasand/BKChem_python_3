#--------------------------------------------------------------------------
#     This file is part of OASA - a free chemical python library
#     Copyright (C) 2003 Beda Kosata <beda@zirael.org>

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

try:
  import oasa
except ImportError:
  print("Sorry, but Python 2.5 or higher is required for OASA.")


# small helper function
def bug_message():
  sys.stderr.write( "Error: the library crashed with the following exception:\n%s\n" % sys.exc_info()[1])
  sys.stderr.write( "If you are sure your input is OK, please send me a bugreport to beda@zirael.org\n")


# the program
usage_text ="""usage: python convert.py xy [infile] [outfile or stdout]

  where x and y is input and output format, respectively
  - possible values for x are 's' (smiles), 'i' (INChI), 'm' (molfile), 'c' (CDML)
  - possible values for y are 's' (smiles), 'i' (INChI), 'm' (molfile)

  if not infile is given the program is started in interactive mode

example: python convert.py is naftalen.ichi naftalen.smiles
"""

import sys
if len( sys.argv) < 2:
  print(usage_text)
  sys.exit()

# initialization
conv = sys.argv[1]

if len( sys.argv) > 2:
  inname = sys.argv[2]
else:
  inname = None


if len( sys.argv) > 3:
  outname = sys.argv[3]
else:
  outname = None

# checking of the input values
try:
  inmode, outmode = conv
except:
  print(usage_text)
  print("error: 'xy' input field should be exactly 2 characters long")
  print()
  sys.exit()

if inmode not in "csim":
  print(usage_text)
  print("error: the input format should be one of s,i,m")
  print()
  sys.exit()

if outmode not in "sim":
  print(usage_text)
  print("error: the output format should be one of s,m")
  print()
  sys.exit()

if inname:
  try:
    infile = file( inname, 'r')
  except:
    print("error: cannot open file %s for reading" % inname)
    print()
    sys.exit()
else:
  infile = None

if outname:
  try:
    outfile = file( outname, 'w')
  except:
    print("error: cannot open file %s for writing" % inname)
    print()
    sys.exit()
else:
  outfile = sys.stdout

# the code itself

recoding = {'s':'smiles', 'i':'inchi', 'm':'molfile', 'c':'cdml'}

in_recoder = oasa.__dict__[ recoding[ inmode]]
out_recoder = oasa.__dict__[ recoding[ outmode]]

import time

if inname:
  # normal mode
  t = time.time()
  try:
    mol = in_recoder.file_to_mol( infile)
    out_recoder.mol_to_file( mol, outfile)
  except:
    bug_message()
  infile.close()
  if outname:
    outfile.close()
  else:
    print()
  sys.stderr.write( "processing time %.2f ms\n" % ((time.time()-t)*1000))

else:
  # interactive mode
  import readline
  try:
    text = raw_input( recoding[inmode]+": ")
  except:
    text = ''
  while text:
    t = time.time()
    try:
      mol = in_recoder.text_to_mol( text)
      out_recoder.mol_to_file( mol, outfile)  # outfile is stdout
    except:
      bug_message()
    outfile.write("\n")
    sys.stderr.write( "processing time %.2f ms\n" % ((time.time()-t)*1000))
    try:
      text = raw_input( recoding[inmode]+": ")
    except:
      text = ''

    
# end
  
