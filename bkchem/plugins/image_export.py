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

"""Export plugin for raster image formats (PNG, JPEG, BMP) with DPI settings.
Uses Tkinter's Postscript export and PIL for format conversion."""

import tkinter
from tkinter import ttk
from . import plugin
from PIL import Image
import io
import os
import Pmw
from bkchem.singleton_store import Screen


class image_exporter(plugin.exporter):
    """Exports raster image files (PNG, JPEG, BMP) with configurable DPI settings.
    Uses Tkinter's Postscript export and PIL for format conversion and DPI metadata."""

    doc_string = _("Exports PNG, JPEG, or BMP image files with configurable DPI settings. High resolution export is supported for print-quality output.")

    def __init__(self, paper):
        self.paper = paper
        self.interactive = True
        self.output_format = 'PNG'
        self.dpi = 300
        self.jpeg_quality = 95
        self.background_color = 'white'

    def on_begin(self):
        self.paper.unselect_all()
        # Show dialog to get DPI and format settings
        x = self.paper.winfo_width()
        y = self.paper.winfo_height()
        result = self.get_scaling(x, y)
        return result is not None

    def get_scaling(self, x, y):
        """Show dialog to get export settings."""
        if self.interactive:
            d = image_export_dialog(self.paper, x, y)
            if d.result:
                self.output_format = d.output_format
                self.dpi = d.dpi
                self.jpeg_quality = d.jpeg_quality
                self.background_color = d.background_color
                return d.result
            else:
                return None, None
        else:
            return 1.0, 1.0

    def write_to_file(self, name):
        """Export the paper to an image file using piddlePIL with anti-aliasing."""
        from .piddle.piddlePIL import PILCanvas
        from . import tk2piddle
        from bkchem.singleton_store import Store
        
        # Calculate dimensions at target DPI
        scale = self.dpi / Screen.dpi
        
        # Get paper dimensions in pixels at target DPI
        if self.paper.get_paper_property('crop_svg'):
            bbox = self.paper.get_cropping_bbox()
            width_px = int((bbox[2] - bbox[0]) * scale)
            height_px = int((bbox[3] - bbox[1]) * scale)
        else:
            sx = self.paper._paper_properties['size_x']
            sy = self.paper._paper_properties['size_y']
            width_px = int(Screen.mm_to_px(sx) * scale)
            height_px = int(Screen.mm_to_px(sy) * scale)
        
        # Render at 2x resolution for anti-aliasing, then downscale
        aa_scale = 2.0
        aa_width = int(width_px * aa_scale)
        aa_height = int(height_px * aa_scale)
        
        # Create a transformer to scale the output (accounting for 2x AA)
        from bkchem.oasa.oasa import transform
        tr = transform.transform()
        tr.set_scaling(72.0 * scale * aa_scale / Screen.dpi)
        
        # Create PIL canvas at 2x size for anti-aliasing
        canvas = PILCanvas(size=(aa_width, aa_height))
        
        # Create converter and export
        converter = tk2piddle.tk2piddle()
        converter.export_to_piddle_canvas(self.paper, canvas, transformer=tr)
        
        # Get the PIL image and downscale with anti-aliasing
        img = canvas.getImage()
        if img.size != (width_px, height_px):
            img = img.resize((width_px, height_px), Image.Resampling.LANCZOS)
        
        # Process based on output format
        if self.output_format == 'JPEG':
            if img.mode != 'RGB':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img.convert('RGBA'))
                img = bg
        elif self.output_format == 'PNG' and self.background_color == 'transparent':
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        else:
            if img.mode != 'RGB':
                img = img.convert('RGB')
        
        # Set DPI metadata and save
        dpi_tuple = (self.dpi, self.dpi)
        
        # Ensure file extension matches selected format
        base_name = os.path.splitext(name)[0]
        if self.output_format == 'PNG':
            name = base_name + '.png'
            img.save(name, format='PNG', dpi=dpi_tuple)
        elif self.output_format == 'JPEG':
            name = base_name + '.jpg'
            img.save(name, format='JPEG', dpi=dpi_tuple, quality=self.jpeg_quality, optimize=True)
        elif self.output_format == 'BMP':
            name = base_name + '.bmp'
            img.save(name, format='BMP', dpi=dpi_tuple)
        
        Store.log(_('Exported image: ') + name)


# PLUGIN INTERFACE SPECIFICATION
name = "Export as Image"
extensions = [".png", ".jpg", ".jpeg", ".bmp"]
exporter = image_exporter
local_name = _("Export as Image")


class image_export_dialog:
    """Dialog for configuring image export settings including format, DPI, and quality."""

    def __init__(self, parent, x, y):
        self.orig_x = int(x)
        self.orig_y = int(y)
        self.orig_dpi = round(Screen.dpi)

        # Default values
        self.dpi = 300
        self.output_format = 'PNG'
        self.jpeg_quality = 95
        self.background_color = 'white'
        self.result = None

        self.dialog = Pmw.Dialog(
            parent,
            buttons=(_('OK'), _('Cancel')),
            defaultbutton=_('OK'),
            title=_('Export as Image'),
            command=self.done
        )

        # Main instruction label
        tkinter.Label(
            self.dialog.interior(),
            text=_("Configure image export settings for high resolution output."),
            wraplength=400
        ).pack(pady=10, anchor="w", expand="1", padx=5)

        # Format selection
        format_frame = tkinter.LabelFrame(self.dialog.interior(), text=_("Output Format"), padx=5, pady=5)
        format_frame.pack(pady=5, anchor='n', padx=10, fill='x')

        self.format_var = tkinter.StringVar(value='PNG')
        formats = [
            ('PNG (Best quality, transparency support)', 'PNG'),
            ('JPEG (Smaller file size, no transparency)', 'JPEG'),
            ('BMP (Uncompressed, Windows format)', 'BMP')
        ]

        for text, value in formats:
            tkinter.Radiobutton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value,
                command=self._format_changed
            ).pack(anchor='w', pady=2)

        # JPEG quality slider (only visible for JPEG)
        self.quality_frame = tkinter.Frame(format_frame)
        self.quality_frame.pack(anchor='w', pady=5, fill='x')

        tkinter.Label(self.quality_frame, text=_("JPEG Quality:")).pack(side='left')
        self.quality_var = tkinter.IntVar(value=95)
        self.quality_slider = tkinter.Scale(
            self.quality_frame,
            from_=1,
            to=100,
            orient='horizontal',
            variable=self.quality_var,
            length=200
        )
        self.quality_slider.pack(side='left', padx=5)
        self.quality_label = tkinter.Label(self.quality_frame, text="95")
        self.quality_label.pack(side='left')

        # Bind quality slider to update label
        self.quality_var.trace('w', lambda *args: self.quality_label.config(text=str(self.quality_var.get())))

        # Initially hide quality frame (shown only for JPEG)
        self.quality_frame.pack_forget()

        # Resolution settings frame
        res_frame = tkinter.LabelFrame(self.dialog.interior(), text=_("Resolution Settings"), padx=5, pady=5)
        res_frame.pack(pady=5, anchor='n', padx=10, fill='x')

        # DPI input with presets
        dpi_frame = tkinter.Frame(res_frame)
        dpi_frame.pack(anchor='n', pady=3)

        tkinter.Label(dpi_frame, text=_("DPI (Resolution):")).pack(side='left')

        self.dpi_var = tkinter.IntVar(value=300)
        self.dpi_entry = tkinter.Spinbox(
            dpi_frame,
            from_=72,
            to=2400,
            increment=1,
            textvariable=self.dpi_var,
            width=6,
            command=self._dpi_changed
        )
        self.dpi_entry.pack(side='left', padx=5)

        # DPI presets
        presets_frame = tkinter.Frame(res_frame)
        presets_frame.pack(anchor='n', pady=3)

        tkinter.Label(presets_frame, text=_("Presets:")).pack(side='left')

        presets = [
            ('Screen (72 DPI)', 72),
            ('Print (150 DPI)', 150),
            ('High Quality (300 DPI)', 300),
            ('Very High (600 DPI)', 600)
        ]

        for text, dpi_val in presets:
            tkinter.Button(
                presets_frame,
                text=text,
                command=lambda d=dpi_val: self._set_dpi(d)
            ).pack(side='left', padx=2)

        # Size display
        self.size_frame = tkinter.Frame(res_frame)
        self.size_frame.pack(anchor='n', pady=5)

        tkinter.Label(self.size_frame, text=_("Output Size:")).pack(side='left')
        self.size_label = tkinter.Label(self.size_frame, text=self._calc_size_text())
        self.size_label.pack(side='left', padx=5)

        # Background color
        bg_frame = tkinter.LabelFrame(self.dialog.interior(), text=_("Background"), padx=5, pady=5)
        bg_frame.pack(pady=5, anchor='n', padx=10, fill='x')

        self.bg_var = tkinter.StringVar(value='white')
        tkinter.Radiobutton(
            bg_frame,
            text=_("White background"),
            variable=self.bg_var,
            value='white'
        ).pack(anchor='w', pady=2)
        tkinter.Radiobutton(
            bg_frame,
            text=_("Transparent (PNG only)"),
            variable=self.bg_var,
            value='transparent'
        ).pack(anchor='w', pady=2)

        # Info text
        info_text = _(
            "Note:\n"
            "- Higher DPI = higher quality but larger file\n"
            "- JPEG does not support transparency\n"
            "- PNG is recommended for best quality"
        )
        tkinter.Label(
            self.dialog.interior(),
            text=info_text,
            justify='left',
            fg='gray'
        ).pack(pady=10, anchor="w", padx=10)

        # Bind DPI changes
        self.dpi_var.trace('w', lambda *args: self._update_size_display())

        self.dialog.activate()

    def _format_changed(self):
        """Handle format selection change."""
        fmt = self.format_var.get()
        if fmt == 'JPEG':
            # Show quality frame in format section
            self.quality_frame.pack(anchor='w', pady=5, fill='x')
            # Force white background for JPEG
            self.bg_var.set('white')
        else:
            self.quality_frame.pack_forget()

    def _set_dpi(self, dpi_val):
        """Set DPI to a preset value."""
        self.dpi_var.set(dpi_val)
        self._update_size_display()

    def _dpi_changed(self):
        """Handle DPI entry change."""
        try:
            val = int(self.dpi_entry.get())
            if 72 <= val <= 2400:
                self.dpi_var.set(val)
                self._update_size_display()
        except ValueError:
            pass

    def _calc_size_text(self):
        """Calculate and return the output size text."""
        try:
            dpi = self.dpi_var.get()
        except tkinter.TclError:
            dpi = 300  # default if empty/invalid
        scale = dpi / self.orig_dpi
        width = int(self.orig_x * scale)
        height = int(self.orig_y * scale)
        return f"{width} x {height} pixels"

    def _update_size_display(self):
        """Update the size display label."""
        self.size_label.config(text=self._calc_size_text())

    def done(self, button):
        """Called on dialog exit."""
        if not button or button == _('Cancel'):
            self.result = None
        else:
            # Get values
            self.dpi = self.dpi_var.get()
            self.output_format = self.format_var.get()
            self.jpeg_quality = self.quality_var.get()
            self.background_color = self.bg_var.get()

            # Calculate scale factor (not used directly but returned for compatibility)
            scale = self.dpi / self.orig_dpi
            self.result = (scale, scale)

        self.dialog.deactivate()
