#!/usr/bin/env python3
"""
BKChem launcher script
This script sets up the Python path and launches BKChem properly.
"""

import sys
import os

# Add the parent directory to Python path so we can import bkchem as a package
parent_dir = os.path.dirname(__file__)
sys.path.insert(0, parent_dir)

print("Starting BKChem...")

# Now we can run bkchem as a module
if __name__ == '__main__':
    print("Importing bkchem.bkchem...")
    import bkchem.bkchem
    print("BKChem imported successfully")
    print("Starting mainloop...")
    
    # Get the application instance and start the mainloop
    from bkchem.singleton_store import Store
    if hasattr(Store, 'app'):
        Store.app.mainloop()
        print("BKChem finished")
    else:
        print("Error: Application not initialized")
