#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#     Copyright (C) 2002-2009 Beda Kosata <beda@zirael.org>

#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     Complete text of GNU GPL can be found in the file gpl.txt in the
#     main directory of the program

#--------------------------------------------------------------------------

"""messages for use throughout the program"""

# Internationalization
try:
    _
except NameError:
    _ = lambda x: x

# -------------------- HELP MESSAGES FOR MODES --------------------

edit_mode_startup = _("use SHIFT to drag only in X, CTRL to drag only in Y")

# DRAW

draw_mode_single = _("click on atom to add a new single bond, click on bond to change its order (or change direction)\nShift+click on a double bond to move the position of the second line")
draw_mode_fixed = _("length of the drawn bond is fixed to a preset value")
draw_mode_freestyle = _("freestyle drawing - no bond length or angle restrictions are applied")


# ARROW

arrow_mode_fixed = _("length of the drawn arrow (arrow part) is fixed to a preset value")
arrow_mode_freestyle = _("freestyle drawing - no arrow length or angle restrictions are applied")
arrow_mode_anormal = _("arrow is composed of straight lines")
arrow_mode_spline = _("arrow is drawn as a b-spline")


# ROTATION

rotate_mode_2D = _("drag an atom or a bond to 2D-rotate a molecule around its geometrical center")
rotate_mode_3D = _("drag an atom or a bond to 3D-rotate a molecule around its geometrical center \nPlease note that it is not possible to add a template to an atom with z-coordinate other than 0")
rotate_mode_fixsomething = _("select a bond and then start rotating - the molecule will rotate around the selected bond \nby holding shift, you will trigger rotation only of one part of the molecule.")

# VECTOR

vector_mode_square = _("click and drag to draw the corresponding shape")
vector_mode_rect = _("click and drag to draw the corresponding shape")
vector_mode_oval = _("click and drag to draw the corresponding shape")
vector_mode_circle = _("click and drag to draw the corresponding shape")
vector_mode_polygon = _("each left-button click creates one point of the polygon, right click closes it")


# MARKS

mark_mode_radical = _("click an atom to add a radical mark to it, it will be removed in case it is already present")
mark_mode_biradical = _("click an atom to add a biradical mark to it, it will be removed in case it is already present")
mark_mode_electronpair = _("click an atom to add a free electron pair mark to it, it will be removed in case it is already present")
mark_mode_plusincircle = _("click an atom to add a plus mark to it, it will be removed in case it is already present")
mark_mode_minusincircle = _("click an atom to add a minus mark to it, it will be removed in case it is already present")


# BOND ALIGN

bond_align_mode_tovert = _("click a bond or two atoms to align the specified line into vertical position")
bond_align_mode_tohoriz = _("click a bond or two atoms to align the specified line into horizontal position")
bond_align_mode_invertthrough = _("click an atom or bond to perform an inversion of the molecule through this atom (center of the bond)")
bond_align_mode_mirrorthrough = _("click a bond or two atoms to mirror the molecule through the specified line")




# -------------------- OTHER MESSAGES --------------------


about_text = _("""BKChem was conceived and written by Beda Kosata
and is performed by Python, Pmw & (optionally) Cairo.
Later maintained by Reinis Danne <rei4dan@gmail.com>.

BKChem is free software and is distributed under GNU GPL.
BKChem is provided as is without warranty of any kind.
- see the file 'gpl.txt' in distribution directory for more info.

Among other things GNU GPL allows you to study, modify
and redistribute BKChem as long as you do it under GNU GPL.

Maintained by Dr. Vijay Masand (Amravati, India), Mr. Gaurav Masand (Amravati, India), and Mr. Krish Masand (Amravati, India)
since 2026.
""")


no_pmw_text = _("""UNABLE TO IMPORT PMW

Sorry, but BKChem relies too heavily on Pmw to be usable without it. Please install Pmw and try again.
(for more info on Pmw see documentation)""")


no_oasa_text = _("""UNABLE TO IMPORT OASA

Sorry, but from version 0.10 BKChem uses the OASA library internally and therefor cannot run without it.""")


low_python_version_text = _("""Python version too low!

From version 0.14 BKChem needs Python 2.5 or higher to run properly. You only have Python version %s.
Sorry for the inconvenience, but you would need to upgrade Python in order to run BKChem.""")



splash_text = _("""BKChem is starting.

Unfortunately,
the splash image was not found :(""")


standards_differ_text = _('''This CDML document was created using different standard values than you are currently using. To retain the same drawing style it could be more convenient to use these new values for this file. Your global preferences will be unaffected. \n\nDo you want set these new standard values?''')


usage_text = _("""usage: bkchem [options] [filenames]

options:

 -h, --help      show this help message and exit
 -H DIR          overrides the BKChem home dir
                 (where standard drawing setting, user-defined templates etc. are stored.)
 -b SCRIPT       start BKChem in batch mode, run SCRIPT and exit
 -v, --version   show program version and exit
""")
