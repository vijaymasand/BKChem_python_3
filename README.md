# BKChem (Python 3 Modernized)

**BKChem** is a free (open source) 2D molecular drawing program. It was originally developed by Beda Kosata and has been a staple in the open-source chemical informatics community for years. 

This repository contains a modernized version of BKChem, fully ported to **Python 3.10+** and stabilized for modern operating systems.

## Key Features

- **Intuitive Drawing**: Easy creation of bonds, atoms, and complex molecular structures.
- **Rich Export Formats**:
    - **Vector**: SVG, PDF (via Cairo and Piddle), PostScript, EPS.
    - **Document**: OpenOffice/LibreOffice Draw (ODF), LaTeX.
    - **Image**: PNG (via Cairo).
- **Chemical Intelligence**: Correct handling of atom properties, isotopes, and structure validation.
- **Scalability**: Support for templates and user-defined fragment libraries.
- **Plugin System**: Extensible architecture for custom exporters and importers.

## Recent Modernization & Stability Fixes

This version of BKChem includes significant updates to ensure compatibility with modern environments:

- **Python 3 Port**: Fully refactored from Python 2 to Python 3.10+, resolving all legacy syntax and library incompatibilities.
- **Graphics Export Fixes**:
    - Resolved critical `TypeError: a bytes-like object is required` crashes in Cairo-based exporters (PDF, SVG, PNG, PS).
    - Modernized the internal **Piddle** graphics library to correctly handle binary file I/O in Python 3.
- **Text Rendering Stability**: Fixed a persistent crash (`NoneType object is not iterable`) in the `ftext` engine when handling charges or single-character labels.
- **Modern I/O**: Shifted to standard binary file handling for all PDF and PostScript generation.

## Requirements

To run BKChem, you need Python 3.10 or higher and the following libraries:

- **Tkinter**: (usually comes with Python)
- **Pmw** (Python MegaWidgets): `pip install Pmw`
- **Pillow** (PIL Fork): `pip install Pillow`
- **PyCairo** (Optional, for Cairo-based exports): `pip install pycairo`

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vijaymasand/BKChem_python_3
   cd BKChem_python_3
   ```

2. **Install dependencies**:
   ```bash
   pip install Pmw Pillow pycairo
   ```

3. **Launch BKChem**:
   ```bash
   python start_bkchem.py
   ```

## Support & Contribution

If you find this modernized version of BKChem helpful, please consider:
- 🌟 **Giving it a Star** on GitHub to help others find it.
- ☕ **Buying me a coffee** to support further development: 
  [![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/vijaymasand)

## Documentation

Detailed documentation (though some of it legacy) can be found in the `doc/` directory, including guides on batch mode, custom plugins, and templates.

## License

BKChem is released under the **GNU General Public License (GPL)**. See the `bkchem/import_checker.py` or the original project documentation for more licensing details.

---
*Modernization and maintenance by Dr. Vijay Masand (Amravati, India), Gaurav Masand (Amravati, India), and Krish Masand (Amravati, India)*