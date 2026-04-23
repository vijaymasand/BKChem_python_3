import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as tkMessageBox
import Pmw
import csv
import os
import multiprocessing
from .fingerprints import FingerprintGenerator
from .oasa import smiles
from .oasa_bridge import bkchem_mol_to_oasa_mol

def _calculate_fingerprint_worker(args):
    """ Worker function for multiprocessing """
    smiles_str, name, fp_type, size, radius = args
    from .oasa import smiles as oasa_smiles
    from .fingerprints import FingerprintGenerator
    generator = FingerprintGenerator(size=size)
    try:
        mol = oasa_smiles.text_to_mol(smiles_str)
        if fp_type == 'Morgan':
            fp = generator.get_morgan_fingerprint(mol, radius=radius)
        else:
            fp = generator.get_path_fingerprint(mol)
        
        fp_str = generator.bitset_to_string(fp)
        return {'Molecule Name': name, 'SMILES': smiles_str, 'Fingerprint': fp_str}
    except Exception as e:
        return None

class FingerprintDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = Pmw.Dialog(parent,
                                 buttons=('Close',),
                                 defaultbutton='Close',
                                 title='Molecular Fingerprints Calculator',
                                 command=self.close)
        
        self.generator = FingerprintGenerator()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        interior = self.dialog.interior()
        
        # Batch Processing Group
        batch_group = Pmw.Group(interior, tag_text='Batch Processing')
        batch_group.pack(fill='both', expand=1, padx=10, pady=5)
        
        # Input selection
        input_frame = tk.Frame(batch_group.interior())
        input_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(input_frame, text="Input File (.smi, .csv):").pack(side='left')
        tk.Entry(input_frame, textvariable=self.input_file, width=40).pack(side='left', padx=5)
        tk.Button(input_frame, text="Browse...", command=self.browse_input).pack(side='left')
        
        # Output selection
        output_frame = tk.Frame(batch_group.interior())
        output_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(output_frame, text="Output CSV:").pack(side='left')
        tk.Entry(output_frame, textvariable=self.output_file, width=40).pack(side='left', padx=5)
        tk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side='left')
        
        # Settings Group
        settings_group = Pmw.Group(interior, tag_text='Settings')
        settings_group.pack(fill='both', expand=1, padx=10, pady=5)
        
        s_interior = settings_group.interior()
        
        # Fingerprint Type
        self.fp_type = tk.StringVar(value='Morgan')
        tk.Label(s_interior, text="Type:").grid(row=0, column=0, sticky='w', padx=5)
        tk.OptionMenu(s_interior, self.fp_type, 'Morgan', 'Path').grid(row=0, column=1, sticky='w', padx=5)
        
        # Size
        self.fp_size = tk.IntVar(value=1024)
        tk.Label(s_interior, text="Size (bits):").grid(row=1, column=0, sticky='w', padx=5)
        tk.OptionMenu(s_interior, self.fp_size, 512, 1024, 2048).grid(row=1, column=1, sticky='w', padx=5)
        
        # Radius for Morgan
        self.fp_radius = tk.IntVar(value=2)
        tk.Label(s_interior, text="Radius (Morgan):").grid(row=2, column=0, sticky='w', padx=5)
        tk.Spinbox(s_interior, from_=1, to=5, textvariable=self.fp_radius, width=5).grid(row=2, column=1, sticky='w', padx=5)
        
        # Multiprocessing Settings
        mp_frame = tk.Frame(s_interior)
        mp_frame.grid(row=3, column=0, columnspan=2, sticky='w', pady=5)
        tk.Label(mp_frame, text="Processors:").pack(side='left', padx=5)
        max_cpus = multiprocessing.cpu_count()
        self.cpu_count = tk.IntVar(value=max(1, max_cpus // 2))
        tk.Spinbox(mp_frame, from_=1, to=max_cpus, textvariable=self.cpu_count, width=5).pack(side='left', padx=5)
        
        tk.Button(batch_group.interior(), text="Start Batch Processing", 
                  command=self.process_batch, bg='#e1f5fe').pack(pady=10)
        
        # Current Selection Group
        current_group = Pmw.Group(interior, tag_text='Canvas Selection')
        current_group.pack(fill='both', expand=1, padx=10, pady=5)
        tk.Button(current_group.interior(), text="Calculate for Selected", 
                  command=self.process_selected).pack(pady=5)
        
        self.status = tk.Label(interior, text="Ready", bd=1, relief='sunken', anchor='w')
        self.status.pack(fill='x', side='bottom')

    def browse_input(self):
        filename = filedialog.askopenfilename(filetypes=[("Chemical files", "*.smi *.csv"), ("All files", "*.*")])
        if filename:
            self.input_file.set(filename)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            self.output_file.set(filename)

    def process_batch(self):
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not input_path or not output_path:
            tkMessageBox.showerror("Error", "Please select both input and output files.")
            return
            
        try:
            self.status.config(text="Processing...")
            self.dialog.update()
            
            is_csv = input_path.lower().endswith('.csv')
            with open(input_path, 'r', newline='') as f:
                if is_csv:
                    sample = f.read(1024); f.seek(0)
                    has_header = False
                    try: has_header = csv.Sniffer().has_header(sample)
                    except: pass
                    reader = csv.reader(f)
                    if has_header: next(reader)
                    rows = list(reader)
                else:
                    rows = [line.strip().split() for line in f if line.strip()]

            tasks = []
            for i, row in enumerate(rows):
                if not row: continue
                if is_csv and len(row) >= 2:
                    name, smiles_str = row[0], row[1]
                elif not is_csv and len(row) >= 2:
                    smiles_str, name = row[0], row[1]
                else:
                    smiles_str, name = row[0], f"Mol_{i+1}"
                tasks.append((smiles_str, name, self.fp_type.get(), self.fp_size.get(), self.fp_radius.get()))

            num_procs = self.cpu_count.get()
            self.status.config(text=f"Calculating with {num_procs} cores...")
            self.dialog.update()
            
            with multiprocessing.Pool(processes=num_procs) as pool:
                results = pool.map(_calculate_fingerprint_worker, tasks)
            
            all_results = [r for r in results if r]
            if not all_results:
                tkMessageBox.showwarning("Warning", "No molecules were successfully processed.")
                return

            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['Molecule Name', 'SMILES', 'Fingerprint'])
                writer.writeheader()
                writer.writerows(all_results)
                
            self.status.config(text="Finished")
            tkMessageBox.showinfo("Success", f"Processed {len(all_results)} molecules.\nResults saved to {output_path}")
            
        except Exception as e:
            self.status.config(text="Error")
            tkMessageBox.showerror("Error", f"An error occurred: {str(e)}")

    def process_selected(self):
        try:
            # This is simplified, in real main.py we'd get selected objects
            paper = self.parent.get_active_paper()
            selected = paper.get_selected_molecules()
            if not selected:
                tkMessageBox.showwarning("Warning", "No molecules selected on canvas.")
                return
            
            gen = FingerprintGenerator(size=self.fp_size.get())
            res_text = ""
            for mol_obj in selected:
                oasa_mol = bkchem_mol_to_oasa_mol(mol_obj)
                if self.fp_type.get() == 'Morgan':
                    fp = gen.get_morgan_fingerprint(oasa_mol, radius=self.fp_radius.get())
                else:
                    fp = gen.get_path_fingerprint(oasa_mol)
                
                fp_str = gen.bitset_to_string(fp)
                res_text += f"Mol: {mol_obj.id}\nFingerprint: {fp_str[:64]}...\n\n"
            
            # Show in a simple dialog
            top = tk.Toplevel(self.parent)
            top.title("Calculated Fingerprints")
            txt = tk.Text(top, height=10, width=80)
            txt.insert('1.0', res_text)
            txt.pack(padx=10, pady=10)
            
        except Exception as e:
            tkMessageBox.showerror("Error", f"Could not process selection: {str(e)}")

    def close(self, result=None):
        self.dialog.destroy()
