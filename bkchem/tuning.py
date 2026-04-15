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


class Tuning:

    ## On screen rendering
    class Screen:
        # how to shift subscript in relation to the baseline (y)
        # it lets you select different values for different font sizes
        # BKChem will inteligently(?) pick the nearest one
        subscript_y_shift = {7:0, 8:1, 9:1, 11:1, 12:1, 18:3}
    
        # when placing subscript or superscript after a letter, how to tweak the x position
        # it lets you select different values for different font sizes
        # BKChem will inteligently(?) pick the nearest one
        supsubscript_x_shift = {7:-1, 8:-1, 9:-1, 11:-1, 12:-1}

        # how to modify the bbox of atoms etc. when substraction of font descent is used
        drawable_chem_vertex_bbox_mod_after_descent_removal = (0,0,0,1)

        # do not edit this! (unless you know what you are doing)
        def pick_best_value( self, name, font_size):
            if not hasattr( self, name):
                raise AttributeError("attribute %s does not exist" % name)
            d = getattr( self, name)
            # check if proper value is already present
            if font_size in d:
                return d[font_size]
            # it isn't
            keys = d.keys()
            diffs = [abs(k-font_size) for k in keys]
            best_i = diffs.index( min( diffs))
            best_key = keys[best_i]
            #d[font_size] = d[best_key]
            #print "cache miss", font_size, d[best_key]
            return d[best_key]
            
        pick_best_value = classmethod( pick_best_value)
        

    ## SVG export
    class SVG:
        text_x_shift = 1.3
        text_y_shift = 0
    

    ## Piddle export
    class Piddle:
        # how to shift texts x coordinate when exporting via piddle
        text_x_shift = 0.7
