
# at first we cancel all selections
App.paper.unselect_all()

# App.paper is the current paper
# App.paper.molecules is a list of all molecules on this paper
for mol in App.paper.molecules:

  # the aromaticity of bonds is not checked by default
  # therefore we must at first call the mark_aromatic_bonds() method
  mol.mark_aromatic_bonds()

  # then we can loop over all the bonds
  # and change the color of all the aromatic ones
  for b in mol.bonds:
    if b.aromatic:
      b.line_color = "#aa0000"
      b.redraw()


