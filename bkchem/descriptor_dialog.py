
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as tkMessageBox
import Pmw
import csv
import os
from .descriptors import DescriptorCalculator
from .oasa import smiles
from .oasa_bridge import bkchem_mol_to_oasa_mol
import multiprocessing

def _calculate_smiles_worker(args):
    """ Worker function for multiprocessing """
    smiles_str, name = args
    from .oasa import smiles as oasa_smiles
    from .descriptors import DescriptorCalculator
    calculator = DescriptorCalculator()
    try:
        mol = oasa_smiles.text_to_mol(smiles_str)
        res = calculator.calculate_all(mol)
        res['Molecule Name'] = name
        return res
    except Exception as e:
        return None

class DescriptorDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = Pmw.Dialog(parent,
                                 buttons=('Close',),
                                 defaultbutton='Close',
                                 title='Molecular Descriptors Calculator',
                                 command=self.close)
        
        self.calculator = DescriptorCalculator()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        interior = self.dialog.interior()
        
        # Batch processing section
        batch_group = Pmw.Group(interior, tag_text='Batch Processing')
        batch_group.pack(fill='both', expand=1, padx=10, pady=10)
        
        # Input file
        input_frame = tk.Frame(batch_group.interior())
        input_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(input_frame, text="SMILES Input File:").pack(side='left')
        tk.Entry(input_frame, textvariable=self.input_file).pack(side='left', fill='x', expand=1, padx=5)
        tk.Button(input_frame, text="Browse...", command=self.browse_input).pack(side='left')
        
        # Output file
        output_frame = tk.Frame(batch_group.interior())
        output_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(output_frame, text="CSV Output File:").pack(side='left')
        tk.Entry(output_frame, textvariable=self.output_file).pack(side='left', fill='x', expand=1, padx=5)
        tk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side='left')
        
        # Process button
        self.process_btn = tk.Button(batch_group.interior(), text="Start Processing", command=self.process_batch)
        self.process_btn.pack(pady=10)
        
        # Current molecule section
        current_group = Pmw.Group(interior, tag_text='Process Current Selection')
        current_group.pack(fill='both', expand=1, padx=10, pady=10)
        
        tk.Button(current_group.interior(), text="Calculate for Selected", command=self.process_selected).pack(pady=5)
        
        # Multiprocessing Settings
        mp_group = Pmw.Group(interior, tag_text='Multiprocessing Settings')
        mp_group.pack(fill='both', expand=1, padx=10, pady=10)
        
        mp_frame = tk.Frame(mp_group.interior())
        mp_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(mp_frame, text="Number of Processors:").pack(side='left')
        
        max_cpus = multiprocessing.cpu_count()
        default_cpus = max(1, max_cpus // 2)
        self.cpu_count = tk.IntVar(value=default_cpus)
        
        tk.Spinbox(mp_frame, from_=1, to=max_cpus, textvariable=self.cpu_count, width=5).pack(side='left', padx=5)
        tk.Label(mp_frame, text=f"(Max: {max_cpus})").pack(side='left')
        
        self.status = tk.Label(interior, text="Ready", bd=1, relief='sunken', anchor='w')
        self.status.pack(fill='x', side='bottom')

    def browse_input(self):
        filename = filedialog.askopenfilename(title="Select SMILES or CSV file",
                                              filetypes=(("SMILES/CSV files", "*.smi *.smiles *.csv"), ("CSV files", "*.csv"), ("SMILES files", "*.smi *.smiles"), ("Text files", "*.txt"), ("All files", "*.*")))
        if filename:
            self.input_file.set(filename)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(title="Save CSV file",
                                                defaultextension=".csv",
                                                filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if filename:
            self.output_file.set(filename)

    def close(self, button):
        self.dialog.deactivate()

    def activate(self):
        self.dialog.activate()

    def process_batch(self):
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not input_path or not output_path:
            tkMessageBox.showerror("Error", "Please select both input and output files.")
            return
            
        if not os.path.exists(input_path):
            tkMessageBox.showerror("Error", "Input file does not exist.")
            return

        try:
            all_results = []
            all_keys = set()
            
            self.status.config(text="Processing...")
            self.dialog.update()
            
            is_csv = input_path.lower().endswith('.csv')
            
            with open(input_path, 'r', newline='') as f:
                if is_csv:
                    # Try to detect if there's a header
                    sample = f.read(1024)
                    f.seek(0)
                    has_header = False
                    try:
                        has_header = csv.Sniffer().has_header(sample)
                    except:
                        pass
                    
                    reader = csv.reader(f)
                    if has_header:
                        next(reader) # skip header
                    
                    rows = list(reader)
                else:
                    rows = [line.strip().split() for line in f if line.strip()]

            # Prepare data for multiprocessing
            tasks = []
            for i, row in enumerate(rows):
                if not row: continue
                
                if is_csv and len(row) >= 2:
                    name = row[0]
                    smiles_str = row[1]
                elif not is_csv and len(row) >= 2:
                    smiles_str = row[0]
                    name = row[1]
                else:
                    smiles_str = row[0]
                    name = f"Mol_{i+1}"
                tasks.append((smiles_str, name))

            # Run with multiprocessing
            num_procs = self.cpu_count.get()
            self.status.config(text=f"Processing with {num_procs} cores...")
            self.dialog.update()
            
            with multiprocessing.Pool(processes=num_procs) as pool:
                results_list = pool.map(_calculate_smiles_worker, tasks)
            
            # Filter out None results and update all_keys
            for res in results_list:
                if res:
                    all_results.append(res)
                    all_keys.update(res.keys())
            
            if not all_results:
                tkMessageBox.showwarning("Warning", "No molecules were successfully processed.")
                return
            
            # Sort keys to have Name first, then others
            keys = sorted(list(all_keys))
            if 'Molecule Name' in keys:
                keys.remove('Molecule Name')
                keys = ['Molecule Name'] + keys
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys, restval=0)
                writer.writeheader()
                writer.writerows(all_results)
            
            self.status.config(text=f"Finished! Processed {len(all_results)} molecules.")
            tkMessageBox.showinfo("Success", f"Successfully processed {len(all_results)} molecules and saved to {output_path}")
            
        except Exception as e:
            tkMessageBox.showerror("Error", f"An error occurred during batch processing: {e}")
            self.status.config(text="Error")

    def process_selected(self):
        from .singleton_store import Store
        paper = Store.app.paper
        s_mols = [m for m in paper.selected_to_unique_top_levels()[0] if m.object_type == 'molecule']
        
        if not s_mols:
            tkMessageBox.showwarning("No Selection", "Please select at least one molecule.")
            return
            
        output_path = filedialog.asksaveasfilename(title="Save CSV file",
                                                defaultextension=".csv",
                                                filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if not output_path:
            return
            
        try:
            all_results = []
            all_keys = set()
            
            for m in s_mols:
                oasa_mol = bkchem_mol_to_oasa_mol(m)
                res = self.calculator.calculate_all(oasa_mol)
                res['Molecule Name'] = m.name or m.id
                all_results.append(res)
                all_keys.update(res.keys())
                
            keys = sorted(list(all_keys))
            if 'Molecule Name' in keys:
                keys.remove('Molecule Name')
                keys = ['Molecule Name'] + keys
                
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys, restval=0)
                writer.writeheader()
                writer.writerows(all_results)
                
            tkMessageBox.showinfo("Success", f"Successfully saved descriptors for {len(all_results)} selected molecules to {output_path}")
            
        except Exception as e:
            tkMessageBox.showerror("Error", f"An error occurred: {e}")
