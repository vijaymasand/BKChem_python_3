

import sys

# at first we check the command line
if len( sys.argv) <= 1:
  print("you have to supply a filename")
  sys.exit()

# then we import bkchem and threading
from bkchem.bkchem import bkchem
import threading

# bkchem.myapp is the application instance
app = bkchem.myapp

# we need to set batch mode = 1 if we want to suppress some interactive warnings,
# questions and mouse events
app.in_batch_mode = 1  

# now we start the application in a separate thread to be able to manipulate it
t = threading.Thread( target=app.mainloop, name='app')
t.setDaemon( 1)
t.start()


# here comes the actual code

# we load the file
app.load_CDML( sys.argv[1])

# we take all molecules from the current paper, find all the double bonds,
# change their color to red and
for mol in app.paper.molecules:
  for bond in mol.bonds:
    if bond.order == 2:
      bond.line_color = "#aa0000"
      bond.redraw()

# finally we save the result and quit
app.save_CDML()
app.destroy()




