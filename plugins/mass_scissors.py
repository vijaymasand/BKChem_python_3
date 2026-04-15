from oasa.oasa.periodic_table import formula_dict
mols, unique = App.paper.selected_to_unique_top_levels()

colors = ["#cc0000","#00ff00","#0000ff","#ff00ff","#00ffff","#ff5500"]

for mol in mols:
  if mol.object_type == "molecule":
    current_selected_bonds = set( mol.bonds) & set( App.paper.selected_bonds)
    if current_selected_bonds:
      for b in current_selected_bonds:
        mol.temporarily_disconnect_edge( b)
      fragments = list( mol.get_connected_components())
      mol.reconnect_temporarily_disconnected_edges()
      for i, fragment in enumerate( fragments):
        color = colors[i%len(colors)]
        frag_bonds = mol.vertex_subgraph_to_edge_subgraph( fragment) - current_selected_bonds
        for x in fragment | frag_bonds:
          x.line_color = color
          x.redraw()
        formula = sum( [atom.get_formula_dict() for atom in fragment], formula_dict())
        text = "%s: %.8f" % (formula.get_html_repr_as_string(), formula.get_exact_molecular_mass())
        text_obj = App.paper.new_text( 0, 0, text)
        text_obj.line_color = color
        text_obj.draw()
        App.paper.place_next_to_bbox( "b", "r", 10+20*i, text_obj, mol.bbox())

