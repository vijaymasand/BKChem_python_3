#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#--------------------------------------------------------------------------

# Internationalization
try:
    _
except NameError:
    _ = lambda x: x

import os
import tempfile
import sys
import tkinter
from tkinter import Label
import Pmw
from .singleton_store import Store

def execute_print(paper):
    dialog = PrintPreviewDialog(Store.app.main_frame, paper)
    dialog.activate()

class PrintPreviewDialog(Pmw.Dialog):
    def __init__(self, parent, paper, **kw):
        Pmw.Dialog.__init__(self, parent, buttons=(_('Print via PDF Viewer'), _('Cancel')), defaultbutton=_('Print via PDF Viewer'), title=_("Print"), command=self.execute)
        self.paper = paper
        self.parent = parent
        
        self.interior().pack(expand=1, fill='both')
        lbl = Label(self.interior(), text=_("A temporary high resolution PDF will be generated and opened in the default PDF viewer so you can preview and print it."))
        lbl.pack(pady=20, padx=20)
        
    def execute(self, result):
        if result == _('Print via PDF Viewer'):
            self.do_print()
        self.withdraw()
        self.destroy()

    def do_print(self):
        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        try:
            # We use the internal export mechanism. 
            # We prefer Cairo over Piddle as it yields better high res output.
            plugin_id = None
            if Store.app.plug_man.get_plugin_handler("PDF (Cairo)"):
                plugin_id = "PDF (Cairo)"
            elif Store.app.plug_man.get_plugin_handler("PDF (Piddle)"):
                plugin_id = "PDF (Piddle)"
            
            if plugin_id:
                # non-interactive export to avoid additional dialogs
                Store.app.plugin_export(plugin_id, filename=path, interactive=False)
                
                # Open PDF with default viewer which has print functionality
                if os.name == 'nt':
                    try:
                        os.startfile(path)
                    except AttributeError:
                        Store.log(_("Could not automatically open PDF for printing. PDF saved directly to {}").format(path), message_type="error")
                elif os.name == 'posix':
                    if sys.platform == 'darwin':
                        import subprocess
                        subprocess.call(["open", path])
                    else:
                        import subprocess
                        subprocess.call(["xdg-open", path])
            else:
                Store.log(_("PDF exporter required for printing is not available."), message_type="error")
        except Exception as e:
            Store.log(_("Failed to print: {}").format(str(e)), message_type="error")

