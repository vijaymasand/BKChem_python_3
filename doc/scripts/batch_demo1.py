
import os



def update_svgs_in_path( dir):
  """calls update_svg for an argument file,
  in case of directory for all .svg files in the directory"""

  made = 0
  ignored = 0

  if os.path.isfile( dir):
    # a filename was given
    update_svg( dir)

  elif os.path.isdir( dir):
    # a directory name was given
    for f in os.listdir( dir):
      if os.path.splitext( f)[1] == ".svg":
        i = update_svg( os.path.join( dir, f))

        # just count the processed / invalid files
        if i:
          made += 1
        else:
          ignored += 1

  print("resaved %d files, ignored %d" % (made, ignored))



def update_svg( f):
  """tries to open a file in BKChem, in case of success sets font size of
  all atoms to 12 and resaves the file."""

  print(f, "...", end="")
  # App.load_CDML returns true on successful load;
  # if replace argument is set to 1 the file is loaded to the same tab,
  # instead of opening a new one;
  # this prevents memory comsumption to raise to incredible values
  # when many files are processed
  if App.load_CDML( f, replace=1):
    print("OK")
    for mol in App.paper.molecules:
      for atom in mol.atoms:
        atom.font_size = 12
    App.save_CDML()
    return 1
  else:
    print("ignoring")
    return 0



# this starts the script base on the command line arguments given

if Args:
  for arg in Args:
    update_svgs_in_path( arg)
else:
  print("You must supply a path as first argument to the batch script")

