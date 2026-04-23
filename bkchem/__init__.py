## import sys
## import os

## path = os.path.abspath('./bkchem')
## if path not in sys.path:
##   sys.path.append( path)

## import bkchem
## sys.modules['bkchem'] = bkchem

# Internationalization fallback - makes _ available to all submodules
try:
    _
except NameError:
    _ = lambda x: x


from .descriptors import DescriptorCalculator
