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
