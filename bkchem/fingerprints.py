import hashlib
from .oasa import graph

class FingerprintGenerator:
    """ Generates molecular fingerprints using OASA graph objects """

    def __init__(self, size=1024):
        self.size = size

    def get_morgan_fingerprint(self, mol, radius=2):
        """ 
        Implementation of Morgan-like (Circular) fingerprints.
        Uses atom environments of increasing radius.
        """
        mol.add_missing_hydrogens()
        mol.mark_aromatic_bonds()
        
        # 1. Initialize atom identifiers
        # Using atom symbol, degree, explicit H count, formal charge, and aromaticity
        atom_identifiers = {}
        for v in mol.vertices:
            # (symbol, degree, hydrogens, charge, aromatic)
            h_count = len([n for n in v.get_neighbors() if n.symbol == 'H'])
            deg = v.get_degree()
            is_aro = 1 if v.has_aromatic_bonds() else 0
            # Basic invariant
            ident = f"{v.symbol}{deg}{h_count}{v.charge}{is_aro}"
            atom_identifiers[v] = hashlib.sha256(ident.encode()).hexdigest()

        # Final set of bit hashes
        bit_hashes = set(atom_identifiers.values())

        # 2. Iteratively update identifiers for each radius
        for r in range(1, radius + 1):
            new_identifiers = {}
            for v in mol.vertices:
                # Collect neighbor identifiers
                neigh_idents = []
                for e in v.neighbor_edges:
                    # Find neighbor (the other vertex in the edge)
                    v1, v2 = list(e.vertices)
                    neigh = v2 if v1 == v else v1
                    
                    # Environment depends on neighbor ident and bond order
                    order = e.order if not e.aromatic else 4
                    neigh_idents.append(f"{order}{atom_identifiers[neigh]}")
                
                # Sort to ensure canonicality
                neigh_idents.sort()
                
                # Combine current ident with sorted neighbor idents
                combined = atom_identifiers[v] + "".join(neigh_idents)
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_identifiers[v] = new_hash
                bit_hashes.add(new_hash)
            
            atom_identifiers = new_identifiers

        return self._fold_to_bits(bit_hashes)

    def get_path_fingerprint(self, mol, max_length=7):
        """ 
        Generates path-based fingerprints (similar to Daylight).
        Explores all paths up to max_length.
        """
        mol.add_missing_hydrogens()
        mol.mark_aromatic_bonds()
        
        bit_hashes = set()
        
        def find_paths(v, current_path, current_path_idents, visited_edges):
            if len(current_path) > max_length:
                return
            
            # Record the path
            if len(current_path) >= 1:
                # Path identifier: symbols and bond orders
                bit_hashes.add(hashlib.sha256("".join(current_path_idents).encode()).hexdigest())
            
            for e in v.neighbor_edges:
                if e in visited_edges:
                    continue
                
                v1, v2 = list(e.vertices)
                neigh = v2 if v1 == v else v1
                
                order = e.order if not e.aromatic else 4
                
                new_idents = current_path_idents + [str(order), neigh.symbol]
                find_paths(neigh, current_path + [neigh], new_idents, visited_edges | {e})

        for v in mol.vertices:
            find_paths(v, [v], [v.symbol], set())
            
        return self._fold_to_bits(bit_hashes)

    def get_atom_pairs_fingerprint(self, mol):
        """ Implementation of Atom Pairs fingerprints """
        mol.add_missing_hydrogens()
        
        # 1. Get atom invariants (element, degree, pi-electrons)
        atom_invariants = []
        for v in mol.vertices:
            pi = sum(1 for e in v.neighbor_edges if e.order > 1 or e.aromatic)
            # Invariant: (element, degree, pi)
            atom_invariants.append(f"{v.symbol}{v.get_degree()}{pi}")
            
        # 2. Get all-pairs shortest paths
        bit_hashes = set()
        for i in range(len(mol.vertices)):
            mol.mark_vertices_with_distance_from(mol.vertices[i])
            for j in range(i + 1, len(mol.vertices)):
                # Get distance 'd' set by OASA BFS
                d = mol.vertices[j].properties_.get('d', float('inf'))
                if d < float('inf'):
                    # Pair identifier: (Inv1, Inv2, distance)
                    p1, p2 = sorted([atom_invariants[i], atom_invariants[j]])
                    ident = f"{p1}{p2}{int(d)}"
                    bit_hashes.add(hashlib.sha256(ident.encode()).hexdigest())
                    
        return self._fold_to_bits(bit_hashes)

    def get_torsions_fingerprint(self, mol):
        """ Implementation of Topological Torsions fingerprints (paths of length 3) """
        mol.add_missing_hydrogens()
        
        bit_hashes = set()
        
        def get_atom_inv(v):
            pi = sum(1 for e in v.neighbor_edges if e.order > 1 or e.aromatic)
            return f"{v.symbol}{v.get_degree()}{pi}"

        for v1 in mol.vertices:
            inv1 = get_atom_inv(v1)
            for e1 in v1.neighbor_edges:
                v2 = list(e1.vertices)[1] if list(e1.vertices)[0] == v1 else list(e1.vertices)[0]
                inv2 = get_atom_inv(v2)
                for e2 in v2.neighbor_edges:
                    if e2 == e1: continue
                    v3 = list(e2.vertices)[1] if list(e2.vertices)[0] == v2 else list(e2.vertices)[0]
                    if v3 == v1: continue
                    inv3 = get_atom_inv(v3)
                    for e3 in v3.neighbor_edges:
                        if e3 == e2: continue
                        v4 = list(e3.vertices)[1] if list(e3.vertices)[0] == v3 else list(e3.vertices)[0]
                        if v4 == v2 or v4 == v1: continue
                        inv4 = get_atom_inv(v4)
                        
                        # Torsion identifier: (Inv1, Inv2, Inv3, Inv4)
                        # Canonicalize path
                        path = [inv1, inv2, inv3, inv4]
                        rev_path = path[::-1]
                        canonical = min(path, rev_path)
                        bit_hashes.add(hashlib.sha256("".join(canonical).encode()).hexdigest())
                        
        return self._fold_to_bits(bit_hashes)

    def _fold_to_bits(self, hashes):
        """ Fold long hashes into a fixed-size bitset (vector of 0/1) """
        bitset = [0] * self.size
        for h in hashes:
            # Convert hex hash to integer
            idx = int(h, 16) % self.size
            bitset[idx] = 1
        return bitset

    def bitset_to_string(self, bitset):
        """ Convert bitset list to a string of 0s and 1s """
        return "".join(map(str, bitset))

    def calculate_tanimoto(self, fp1, fp2):
        """ Calculate Tanimoto similarity between two bitsets """
        intersection = sum(1 for b1, b2 in zip(fp1, fp2) if b1 == 1 and b2 == 1)
        union = sum(1 for b1, b2 in zip(fp1, fp2) if b1 == 1 or b2 == 1)
        if union == 0:
            return 0.0
        return float(intersection) / union
