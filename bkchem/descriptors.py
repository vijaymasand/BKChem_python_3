
import math
from .oasa import periodic_table as PT

class DescriptorCalculator:
    def __init__(self):
        pass

    def calculate_all(self, mol):
        """ mol is an OASA molecule object """
        # Add missing hydrogens to make them explicit for accurate descriptor calculation
        mol.add_missing_hydrogens()
        # Mark aromatic bonds for accurate bond type counting
        mol.mark_aromatic_bonds()
        
        results = {}
        
        # Atom counts
        results['Atoms Count'] = len(mol.vertices)
        results['Heavy Atoms Count'] = len([v for v in mol.vertices if v.symbol != 'H'])
        
        element_counts = {}
        for v in mol.vertices:
            element_counts[v.symbol] = element_counts.get(v.symbol, 0) + 1
        
        for symbol in ['C', 'H', 'N', 'O', 'P', 'S', 'F', 'Cl', 'Br', 'I']:
            results[f'Count of {symbol}'] = element_counts.get(symbol, 0)
            
        # Ratios
        c_count = element_counts.get('C', 0)
        n_count = element_counts.get('N', 0)
        o_count = element_counts.get('O', 0)
        h_count = element_counts.get('H', 0)
        s_count = element_counts.get('S', 0)
        halogens_count = sum([element_counts.get(s, 0) for s in ['F', 'Cl', 'Br', 'I']])
        
        results['Ratio C/N'] = self.safe_ratio(c_count, n_count)
        results['Ratio C/O'] = self.safe_ratio(c_count, o_count)
        results['Ratio C/H'] = self.safe_ratio(c_count, h_count)
        results['Ratio C/S'] = self.safe_ratio(c_count, s_count)
        results['Ratio C/Halogens'] = self.safe_ratio(c_count, halogens_count)
            
        # Molecular Weight and Exact Mass
        results['Molecular Weight'] = mol.weight
        results['Exact Mass'] = mol.exact_mass
        
        # Bond counts
        results['Bonds Count'] = len(mol.edges)
        results['Single Bonds'] = len([e for e in mol.edges if e.order == 1])
        results['Double Bonds'] = len([e for e in mol.edges if e.order == 2])
        results['Triple Bonds'] = len([e for e in mol.edges if e.order == 3])
        results['Aromatic Bonds'] = len([e for e in mol.edges if e.aromatic])
        
        # Atom pairs (Bond types)
        pair_counts = {}
        for e in mol.edges:
            v1, v2 = e.get_vertices()
            symbols = sorted([v1.symbol, v2.symbol])
            pair = f"{symbols[0]}-{symbols[1]}"
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
        
        for pair, count in pair_counts.items():
            results[f'Atom Pair: {pair}'] = count
        
        # Rings and advanced ring descriptors
        # Use edge-based SSSR for easier edge iteration
        sssr_e = mol.get_smallest_independent_cycles_e()
        results['Ring Count'] = len(sssr_e)
        
        ring_sizes = {}
        ring_atoms = set()
        for ring_edges in sssr_e:
            size = len(ring_edges)
            ring_sizes[size] = ring_sizes.get(size, 0) + 1
            for e in ring_edges:
                ring_atoms.update(e.get_vertices())
            
        for size in range(3, 9):
            results[f'{size}-membered Rings'] = ring_sizes.get(size, 0)
        
        results['Ring Atoms Count'] = len(ring_atoms)
        results['Non-Ring Atoms Count'] = results['Atoms Count'] - len(ring_atoms)
        results['Ratio Ring/Non-Ring Atoms'] = self.safe_ratio(len(ring_atoms), results['Non-Ring Atoms Count'])
        
        ring_c = len([v for v in ring_atoms if v.symbol == 'C'])
        ring_n = len([v for v in ring_atoms if v.symbol == 'N'])
        ring_o = len([v for v in ring_atoms if v.symbol == 'O'])
        
        results['Ring Carbon Count'] = ring_c
        results['Ring Nitrogen Count'] = ring_n
        results['Ring Oxygen Count'] = ring_o
        
        results['Ratio Ring C / Total C'] = self.safe_ratio(ring_c, c_count)
        results['Ratio Ring C / Ring N'] = self.safe_ratio(ring_c, ring_n)
        results['Ratio Ring C / Ring O'] = self.safe_ratio(ring_c, ring_o)
        
        # Heteroatoms and Aromaticity
        heteroatoms = [v for v in mol.vertices if v.symbol not in ('C', 'H')]
        results['Heteroatom Count'] = len(heteroatoms)
        results['Ratio Heteroatoms / Total Atoms'] = self.safe_ratio(len(heteroatoms), results['Atoms Count'])
        
        aromatic_atoms = [v for v in mol.vertices if v.has_aromatic_bonds()]
        results['Aromatic Atoms Count'] = len(aromatic_atoms)
        results['Ratio Aromatic Atoms / Total Atoms'] = self.safe_ratio(len(aromatic_atoms), results['Atoms Count'])
        
        # New Descriptors: Rotatable Bonds, H-Bond Donors/Acceptors, Fsp3, Aromatic Rings
        results['Rotatable Bond Count'] = self.calculate_rotatable_bonds(mol, sssr_e)
        results['H-Bond Donors'] = self.calculate_h_bond_donors(mol)
        results['H-Bond Acceptors'] = self.calculate_h_bond_acceptors(mol)
        results['Fsp3'] = self.calculate_fsp3(mol)
        results['Aromatic Ring Count'] = self.calculate_aromatic_rings(mol, sssr_e)

        # Drug-likeness and Complexity
        results['Lipinski RO5 Violations (Partial)'] = self.calculate_lipinski_violations(results)
        results['Molecular Complexity (Bertz-like)'] = self.calculate_complexity(mol, sssr_e)

        # Topological Descriptors
        results['Wiener Index'] = self.calculate_wiener_index(mol)
        results['Randic Index'] = self.calculate_randic_index(mol)
        results['Balaban J Index'] = self.calculate_balaban_j(mol)
        
        # Groups Count
        try:
            from .oasa import subsearch
            ssm = subsearch.substructure_search_manager()
            groups = ssm.find_substructures_in_mol(mol)
            group_counts = {}
            for group in groups:
                name = group.substructure.name
                group_counts[name] = group_counts.get(name, 0) + 1
            
            for name, count in group_counts.items():
                results[f'Group: {name}'] = count
        except Exception as e:
            # If subsearch fails, skip groups
            pass
            
        return results

    def calculate_rotatable_bonds(self, mol, sssr_e):
        """ Count single bonds between non-terminal heavy atoms, not in a ring """
        ring_edges = set()
        for ring in sssr_e:
            for e in ring:
                ring_edges.add(e)
        
        count = 0
        for e in mol.edges:
            if e.order == 1 and not getattr(e, 'aromatic', False) and e not in ring_edges:
                v1, v2 = e.get_vertices()
                if v1.symbol != 'H' and v2.symbol != 'H':
                    # Check if they are non-terminal
                    if v1.get_degree() > 1 and v2.get_degree() > 1:
                        count += 1
        return count

    def calculate_h_bond_donors(self, mol):
        """ Count OH and NH groups """
        count = 0
        for v in mol.vertices:
            if v.symbol in ('O', 'N'):
                # Count hydrogens attached to this atom
                h_count = len([neigh for neigh in v.get_neighbors() if neigh.symbol == 'H'])
                if h_count > 0:
                    count += 1
        return count

    def calculate_h_bond_acceptors(self, mol):
        """ Count O and N atoms """
        return len([v for v in mol.vertices if v.symbol in ('O', 'N')])

    def calculate_fsp3(self, mol):
        """ Fraction of sp3 carbons: sp3 carbons / total carbons """
        total_c = len([v for v in mol.vertices if v.symbol == 'C'])
        if total_c == 0:
            return 0.0
        
        sp3_c = 0
        for v in mol.vertices:
            if v.symbol == 'C':
                # sp3 carbon has 4 single bonds (or total degree 4 including H)
                # In OASA with explicit H, it's just the degree
                if v.get_degree() == 4:
                    # Check if all bonds are single
                    if all([e.order == 1 for e in v.neighbor_edges]):
                        sp3_c += 1
        return float(sp3_c) / total_c

    def calculate_aromatic_rings(self, mol, sssr_e):
        """ Count aromatic rings in SSSR """
        count = 0
        for ring in sssr_e:
            # A ring is aromatic if all its bonds are aromatic
            is_aromatic = True
            for e in ring:
                if not getattr(e, 'aromatic', False):
                    is_aromatic = False
                    break
            if is_aromatic:
                count += 1
        return count

    def calculate_lipinski_violations(self, res):
        """ Partial Lipinski RO5: MW < 500, H-donors < 5, H-acceptors < 10 """
        violations = 0
        if res.get('Molecular Weight', 0) > 500:
            violations += 1
        if res.get('H-Bond Donors', 0) > 5:
            violations += 1
        if res.get('H-Bond Acceptors', 0) > 10:
            violations += 1
        return violations

    def calculate_complexity(self, mol, sssr_e):
        """ Simple complexity: edges + nodes + rings + heteroatoms + aromatic atoms """
        n_edges = len(mol.edges)
        n_nodes = len(mol.vertices)
        n_rings = len(sssr_e)
        n_hetero = len([v for v in mol.vertices if v.symbol not in ('C', 'H')])
        n_aromatic = len([v for v in mol.vertices if v.has_aromatic_bonds()])
        return n_edges + n_nodes + n_rings + n_hetero + n_aromatic

    def safe_ratio(self, numerator, denominator):
        if not denominator:
            return 0.0
        return float(numerator) / float(denominator)

    def calculate_wiener_index(self, mol):
        w = 0
        for i in range(len(mol.vertices)):
            mol.mark_vertices_with_distance_from(mol.vertices[i])
            for j in range(i + 1, len(mol.vertices)):
                d = mol.vertices[j].properties_.get('d', 0)
                w += d
        return w

    def calculate_randic_index(self, mol):
        r = 0
        for e in mol.edges:
            v1, v2 = e.get_vertices()
            d1 = v1.get_degree()
            d2 = v2.get_degree()
            if d1 > 0 and d2 > 0:
                r += 1.0 / math.sqrt(d1 * d2)
        return r

    def calculate_balaban_j(self, mol):
        """ Balaban's J index """
        num_edges = len(mol.edges)
        num_vertices = len(mol.vertices)
        num_rings = num_edges - num_vertices + 1 # cyclomatic number
        
        if num_vertices <= 1:
            return 0
            
        # Calculate distance sums for each vertex
        distance_sums = []
        for v in mol.vertices:
            mol.mark_vertices_with_distance_from(v)
            d_sum = sum([vv.properties_.get('d', 0) for vv in mol.vertices])
            distance_sums.append(d_sum)
            
        j = 0
        if num_rings < 0: num_rings = 0 # should not happen
        
        factor = num_edges / (num_rings + 1.0)
        
        for e in mol.edges:
            v1, v2 = e.get_vertices()
            i1 = mol.vertices.index(v1)
            i2 = mol.vertices.index(v2)
            s1 = distance_sums[i1]
            s2 = distance_sums[i2]
            if s1 > 0 and s2 > 0:
                j += 1.0 / math.sqrt(s1 * s2)
        
        return factor * j
