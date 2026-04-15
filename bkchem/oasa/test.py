import oasa
#print oasa.CAIRO_AVAILABLE

def cairo_out_test2():
    mol = oasa.smiles.text_to_mol( "c1ccccc1Cl.c1ccccc1OC.CCCl")
    mol.normalize_bond_length( 30)
    mol.remove_unimportant_hydrogens()
    c = oasa.cairo_out.cairo_out( color_bonds=True, color_atoms=True)
    c.show_hydrogens_on_hetero = True
    c.font_size = 20
    mols = list( mol.get_disconnected_subgraphs())
    c.mols_to_cairo( mols, "test.pdf", format="pdf")
    c.mols_to_cairo( mols, "test.png")
    c.mols_to_cairo( mols, "test.svg", format="svg")

def inchi_test():
    mol = oasa.smiles.text_to_mol( "c1ccccc1\C=C/CC")
    print(oasa.inchi.mol_to_text( mol, program="stdinchi-1.exe", fixed_hs=False))

cairo_out_test2()
#inchi_test()
