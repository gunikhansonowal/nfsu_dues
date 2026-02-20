#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import psutil
import subprocess
import threading
import time
import os
import csv
import signal
import glob
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ProfilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Profiler GUI - Forensic File Analyzer")
        self.root.geometry("1200x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables
        self.program_path = tk.StringVar(value="./dues")
        self.base_args = ["store", "-d", "./Testdata"]
        self.input_file = tk.StringVar(value="")
        self.selected_file_type = tk.StringVar(value="All Forensic Files")
        self.working_dir = tk.StringVar(value=os.getcwd())
        self.sample_rate = tk.DoubleVar(value=0.1)
        self.output_file = tk.StringVar(value="profile_results.csv")
        self.is_profiling = False
        self.proc = None
        self.monitor_thread = None
        self.running = True
        
        # Queue for multiple files
        self.processing_queue = []
        
        # Track processed artifacts and output files - use SET to avoid duplicates
        self.processed_artifacts = set()  # Changed to set to avoid duplicates
        self.all_output_files = {}  # Dict mapping artifact -> list of output files
        self.current_artifact = ""  # Currently processing artifact
        
        # Track output files
        self.output_files = []
        self.data_dir = os.path.join(os.getcwd(), "Testdata")
        
        # Store metrics for each artifact - use dict with artifact name as key to avoid duplicates
        self.artifact_metrics = {}  # Changed to dict with artifact name as key
        
        # File type mapping for dropdown - Enhanced with archive formats
        self.file_types = {
            "All Forensic Files": "*.*",
            "Archive Files": "*.zip *.rar *.7z *.tar *.gz *.xz *.bz2 *.zst *.tgz *.txz",
            "Images": "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp *.heic *.raw",
            "Documents": "*.pdf *.doc *.docx *.txt *.rtf *.odt *.xls *.xlsx *.ppt *.pptx",
            "Memory Dumps": "*.mem *.dump *.dmp *.raw *.vmem *.bin",
            "Disk Images": "*.dd *.img *.iso *.vmdk *.vhd *.vhdx *.qcow2 *.raw *.dmg",
            "Forensic Formats": "*.e01 *.ex01 *.l01 *.ad1 *.aff *.awu",
            "Network Captures": "*.pcap *.pcapng *.cap *.netxml",
            "Executables": "*.exe *.bin *.elf *.out *.app *.msi",
            "Log Files": "*.log *.csv *.txt *.json *.xml",
            "Database Files": "*.db *.sqlite *.mdb *.accdb *.sql",
            "Email Files": "*.pst *.ost *.mbox *.eml *.msg",
            "Registry Files": "*.reg *.dat *.hiv"
        }
        
        # Data storage for real-time plotting
        self.timestamps = []
        self.cpu_data = []
        self.memory_data = []
        self.thread_data = []
        
        # Lock for thread-safe data access
        self.data_lock = threading.Lock()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel - Controls
        left_frame = ttk.Frame(main_frame, padding="10", width=450)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_frame.grid_propagate(False)
        
        # Right panel - Results and Charts
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ========== LEFT PANEL CONTROLS ==========
        row = 0
        
        # Title
        title_label = ttk.Label(left_frame, text="Forensic File Profiler", 
                                font=('Arial', 14, 'bold'))
        title_label.grid(row=row, column=0, pady=(0, 15))
        row += 1
        
        # Working directory
        ttk.Label(left_frame, text="Working Directory:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(0,5))
        row += 1
        
        dir_frame = ttk.Frame(left_frame)
        dir_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0,10))
        
        ttk.Entry(dir_frame, textvariable=self.working_dir, width=40).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).pack(side=tk.LEFT)
        row += 1
        
        # Program selection
        ttk.Label(left_frame, text="Program to profile:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,5))
        row += 1
        
        prog_frame = ttk.Frame(left_frame)
        prog_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0,10))
        
        ttk.Entry(prog_frame, textvariable=self.program_path, width=40).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(prog_frame, text="Browse", command=self.browse_program).pack(side=tk.LEFT)
        row += 1
        
        # Base Arguments
        ttk.Label(left_frame, text="Base Arguments:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,5))
        row += 1
        
        args_frame = ttk.Frame(left_frame)
        args_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0,10))
        
        self.base_args_var = tk.StringVar(value="store -d ./Testdata")
        ttk.Entry(args_frame, textvariable=self.base_args_var, width=40).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(args_frame, text="Reset", command=self.reset_args).pack(side=tk.LEFT)
        row += 1
        
        # Input File with Dropdown
        ttk.Label(left_frame, text="Input File (Archives supported):", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,5))
        row += 1
        
        # File type dropdown
        type_frame = ttk.Frame(left_frame)
        type_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0,5))
        
        ttk.Label(type_frame, text="Filter by:").pack(side=tk.LEFT, padx=(0,5))
        file_type_combo = ttk.Combobox(type_frame, textvariable=self.selected_file_type, 
                                       values=list(self.file_types.keys()), 
                                       state="readonly", width=25)
        file_type_combo.pack(side=tk.LEFT)
        row += 1
        
        # File selection with current file display
        file_frame = ttk.Frame(left_frame)
        file_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5,5))
        
        # Entry for file path
        self.file_entry = ttk.Entry(file_frame, textvariable=self.input_file, width=35)
        self.file_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        
        # Browse button
        ttk.Button(file_frame, text="Browse", command=self.browse_input_file).pack(side=tk.LEFT)
        row += 1
        
        # Selected file info
        self.selected_file_label = ttk.Label(left_frame, text="No file selected", 
                                             font=('Arial', 8), foreground='blue')
        self.selected_file_label.grid(row=row, column=0, sticky=tk.W, pady=(0,5))
        row += 1
        
        # Quick add button
        quick_frame = ttk.Frame(left_frame)
        quick_frame.grid(row=row, column=0, sticky=tk.W, pady=(0,10))
        
        ttk.Button(quick_frame, text="Add to Queue", command=self.add_to_queue).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Process Queue", command=self.process_queue).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Clear Queue", command=self.clear_queue).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Queue display
        self.queue_label = ttk.Label(left_frame, text="Queue: 0 files", font=('Arial', 9))
        self.queue_label.grid(row=row, column=0, sticky=tk.W, pady=(0,5))
        row += 1
        
        # Archive info
        archive_info = ttk.Label(left_frame, 
                               text="✓ Supports: ZIP, RAR, 7Z, TAR, GZ, XZ, BZ2, TGZ, TXZ and more",
                               font=('Arial', 8), foreground='green')
        archive_info.grid(row=row, column=0, sticky=tk.W, pady=(0,5))
        row += 1
        
        # File type info
        file_types_label = ttk.Label(left_frame, 
                                     text="All forensic formats: Images, PDFs, Documents,\nMemory dumps, Disk images, E01, PCAP, Archives, Registry, Email",
                                     font=('Arial', 8), foreground='gray', justify=tk.LEFT)
        file_types_label.grid(row=row, column=0, sticky=tk.W, pady=(0,10))
        row += 1
        
        # Sample rate
        ttk.Label(left_frame, text="Sample rate (seconds):", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,5))
        row += 1
        
        rate_frame = ttk.Frame(left_frame)
        rate_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0,10))
        
        ttk.Spinbox(rate_frame, from_=0.01, to=10, increment=0.01, 
                   textvariable=self.sample_rate, width=10).pack(side=tk.LEFT)
        ttk.Label(rate_frame, text="seconds").pack(side=tk.LEFT, padx=(5,0))
        row += 1
        
        # Output file
        ttk.Label(left_frame, text="Output CSV file:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,5))
        row += 1
        
        output_frame = ttk.Frame(left_frame)
        output_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0,20))
        
        ttk.Entry(output_frame, textvariable=self.output_file, width=30).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(output_frame, text="Save As", command=self.browse_output).pack(side=tk.LEFT)
        row += 1
        
        # Control buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=row, column=0, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Start Profiling", 
                                       command=self.start_profiling, width=15)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Profiling", 
                                      command=self.stop_profiling, width=15, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_results, width=15).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Status
        self.status_label = ttk.Label(left_frame, text="Ready", font=('Arial', 10))
        self.status_label.grid(row=row, column=0, pady=10)
        
        # ========== RIGHT PANEL RESULTS ==========
        # Notebook for tabs
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Real-time Charts
        charts_frame = ttk.Frame(notebook)
        notebook.add(charts_frame, text="Real-time Charts")
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(8, 8))
        self.fig.tight_layout(pad=3.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize plots
        self.cpu_line, = self.ax1.plot([], [], 'b-', label='CPU %')
        self.ax1.set_ylabel('CPU Usage %')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.grid(True)
        self.ax1.legend()
        
        self.memory_line, = self.ax2.plot([], [], 'g-', label='Memory (MB)')
        self.ax2.set_ylabel('Memory (MB)')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.grid(True)
        self.ax2.legend()
        
        self.thread_line, = self.ax3.plot([], [], 'r-', label='Threads')
        self.ax3.set_ylabel('Thread Count')
        self.ax3.set_xlabel('Time (s)')
        self.ax3.grid(True)
        self.ax3.legend()
        
        # Tab 2: Results Summary (Appended)
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary (All Artifacts)")
        
        # Create a paned window for better organization
        summary_paned = ttk.PanedWindow(summary_frame, orient=tk.VERTICAL)
        summary_paned.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for artifact list
        artifact_list_frame = ttk.Frame(summary_paned)
        summary_paned.add(artifact_list_frame, weight=1)
        
        ttk.Label(artifact_list_frame, text="Processed Artifacts:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # Treeview for artifacts
        self.artifact_tree = ttk.Treeview(artifact_list_frame, columns=('Artifact', 'Status', 'Output Files'), show='headings', height=5)
        self.artifact_tree.heading('Artifact', text='Artifact File')
        self.artifact_tree.heading('Status', text='Status')
        self.artifact_tree.heading('Output Files', text='Output Files')
        self.artifact_tree.column('Artifact', width=200)
        self.artifact_tree.column('Status', width=100)
        self.artifact_tree.column('Output Files', width=200)
        
        artifact_scroll = ttk.Scrollbar(artifact_list_frame, orient=tk.VERTICAL, command=self.artifact_tree.yview)
        self.artifact_tree.configure(yscrollcommand=artifact_scroll.set)
        
        self.artifact_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        artifact_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom frame for detailed summary
        summary_text_frame = ttk.Frame(summary_paned)
        summary_paned.add(summary_text_frame, weight=2)
        
        ttk.Label(summary_text_frame, text="Detailed Results:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.results_text = scrolledtext.ScrolledText(summary_text_frame, wrap=tk.WORD, width=60, height=15)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 3: Raw Data
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="Raw Data")
        
        columns = ('Timestamp', 'CPU %', 'Memory (MB)', 'Threads')
        self.data_tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=120)
        
        tree_scroll = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 4: File Info
        file_info_frame = ttk.Frame(notebook)
        notebook.add(file_info_frame, text="File Info")
        
        self.file_info_text = scrolledtext.ScrolledText(file_info_frame, wrap=tk.WORD, width=60, height=20)
        self.file_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 5: Output Files (All artifacts)
        output_files_frame = ttk.Frame(notebook)
        notebook.add(output_files_frame, text="All Output Files")
        
        # Treeview for output files with artifact grouping
        output_columns = ('Artifact', 'File Name', 'Size', 'Modified', 'Path')
        self.output_tree = ttk.Treeview(output_files_frame, columns=output_columns, show='headings', height=15)
        
        self.output_tree.heading('Artifact', text='Source Artifact')
        self.output_tree.heading('File Name', text='File Name')
        self.output_tree.heading('Size', text='Size')
        self.output_tree.heading('Modified', text='Modified')
        self.output_tree.heading('Path', text='Path')
        
        self.output_tree.column('Artifact', width=150)
        self.output_tree.column('File Name', width=150)
        self.output_tree.column('Size', width=100)
        self.output_tree.column('Modified', width=150)
        self.output_tree.column('Path', width=200)
        
        output_tree_scroll = ttk.Scrollbar(output_files_frame, orient=tk.VERTICAL, command=self.output_tree.yview)
        self.output_tree.configure(yscrollcommand=output_tree_scroll.set)
        
        self.output_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button to refresh output files
        ttk.Button(output_files_frame, text="Refresh Output Files", 
                  command=self.scan_output_files).pack(pady=5)
        
        # Bind dropdown selection to update file types
        file_type_combo.bind('<<ComboboxSelected>>', self.on_file_type_selected)
        
        # Bind artifact selection to show details
        self.artifact_tree.bind('<<TreeviewSelect>>', self.on_artifact_selected)
        
    def add_to_queue(self):
        """Add current file to processing queue"""
        if not self.input_file.get():
            self.show_error("Error", "Please select a file first")
            return
        
        file_path = self.input_file.get()
        if file_path not in self.processing_queue:
            self.processing_queue.append(file_path)
            self.update_queue_display()
            self.status_label.config(text=f"Added to queue: {os.path.basename(file_path)}")
    
    def process_queue(self):
        """Process all files in the queue"""
        if not self.processing_queue:
            self.show_error("Error", "Queue is empty")
            return
        
        self.start_profiling(queue_mode=True)
    
    def clear_queue(self):
        """Clear the processing queue"""
        self.processing_queue = []
        self.update_queue_display()
        self.status_label.config(text="Queue cleared")
    
    def update_queue_display(self):
        """Update the queue display label"""
        count = len(self.processing_queue)
        if count == 0:
            self.queue_label.config(text="Queue: 0 files")
        else:
            files_preview = ", ".join([os.path.basename(f) for f in self.processing_queue[:3]])
            if count > 3:
                files_preview += f" and {count-3} more"
            self.queue_label.config(text=f"Queue: {count} files - {files_preview}")
        
    def on_artifact_selected(self, event):
        """Handle artifact selection to show details"""
        selection = self.artifact_tree.selection()
        if not selection:
            return
        
        item = self.artifact_tree.item(selection[0])
        artifact_name = item['values'][0]
        
        # Find the artifact in processed list
        for artifact in self.processed_artifacts:
            if os.path.basename(artifact) == artifact_name:
                # Show details in results text
                if artifact in self.all_output_files:
                    output_files = self.all_output_files[artifact]
                    details = f"\nDetails for {artifact_name}:\n"
                    details += f"Output files ({len(output_files)}):\n"
                    for f in output_files[:10]:
                        details += f"  - {os.path.basename(f)} ({self.format_bytes(os.path.getsize(f))})\n"
                    if len(output_files) > 10:
                        details += f"  ... and {len(output_files)-10} more\n"
                    
                    # Append to results text
                    self.results_text.insert(tk.END, details)
                    self.results_text.see(tk.END)
                break
        
    def on_file_type_selected(self, event):
        """Handle file type dropdown selection"""
        selected = self.selected_file_type.get()
        self.status_label.config(text=f"File filter: {selected}")
        
    def reset_args(self):
        """Reset base arguments to default"""
        self.base_args_var.set("reset -d ./Testdata")
        self.base_args = ["reset", "-d", "./Testdata"]
        self.data_dir = os.path.join(self.working_dir.get(), "Testdata")
        
    def browse_directory(self):
        try:
            directory = filedialog.askdirectory(title="Select Working Directory")
            if directory:
                self.working_dir.set(directory)
                os.chdir(directory)
                # Update data_dir based on base_args
                args = self.base_args_var.get().split()
                if len(args) >= 3 and args[1] == "-d":
                    self.data_dir = os.path.join(directory, args[2])
                else:
                    self.data_dir = os.path.join(directory, "Testdata")
                self.scan_output_files()
        except Exception as e:
            self.show_error("Directory Error", str(e))
            
    def browse_program(self):
        try:
            filename = filedialog.askopenfilename(
                title="Select Program to Profile",
                initialdir=self.working_dir.get()
            )
            if filename:
                try:
                    rel_path = os.path.relpath(filename, self.working_dir.get())
                    self.program_path.set(rel_path)
                except:
                    self.program_path.set(filename)
        except Exception as e:
            self.show_error("File Selection Error", str(e))
                
    def browse_input_file(self):
        try:
            # Get the selected file type filter
            selected_filter = self.selected_file_type.get()
            file_pattern = self.file_types.get(selected_filter, "*.*")
            
            # Create filetypes list for the dialog
            filetypes = [
                (selected_filter, file_pattern),
                ("All Files", "*.*")
            ]
            
            # Add all other types as additional options
            for name, pattern in self.file_types.items():
                if name != selected_filter and name != "All Forensic Files":
                    filetypes.append((name, pattern))
            
            filename = filedialog.askopenfilename(
                title=f"Select Input File ({selected_filter})",
                initialdir=self.working_dir.get(),
                filetypes=filetypes
            )
            
            if filename:
                try:
                    rel_path = os.path.relpath(filename, self.working_dir.get())
                    self.input_file.set(rel_path)
                    self.selected_file_label.config(text=f"Selected: {os.path.basename(filename)}")
                    self.display_file_info(filename)
                    
                    # Show archive-specific info if applicable
                    ext = os.path.splitext(filename)[1].lower()
                    archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz', '.xz', '.bz2', '.tgz', '.txz']
                    if ext in archive_exts:
                        self.status_label.config(text=f"Archive file selected: {ext.upper()} format")
                        
                except:
                    self.input_file.set(filename)
                    self.selected_file_label.config(text=f"Selected: {os.path.basename(filename)}")
                    self.display_file_info(filename)
        except Exception as e:
            self.show_error("File Selection Error", str(e))
    
    def display_file_info(self, filepath):
        """Display information about the selected file"""
        try:
            file_size = os.path.getsize(filepath)
            file_ext = os.path.splitext(filepath)[1].lower()
            file_name = os.path.basename(filepath)
            file_dir = os.path.dirname(filepath)
            
            # Get file permissions
            permissions = oct(os.stat(filepath).st_mode)[-3:]
            
            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get file creation time (if available)
            try:
                create_time = datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            except:
                create_time = "Not available"
            
            # Check if it's an archive
            archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz', '.xz', '.bz2', '.tgz', '.txz']
            is_archive = file_ext in archive_exts
            
            archive_note = "\n📦 This is an archive file - contents will be extracted/processed" if is_archive else ""
            
            info_text = f"""
{'='*60}
FILE INFORMATION
{'='*60}

File Name: {file_name}
File Path: {filepath}
File Size: {self.format_bytes(file_size)} ({file_size:,} bytes)
File Extension: {file_ext if file_ext else 'No extension'}
File Type: {self.get_file_type_description(file_ext)}{archive_note}

Directory: {file_dir}
Permissions: {permissions}
Created: {create_time}
Modified: {mod_time}

{'='*60}
"""
            
            self.file_info_text.delete(1.0, tk.END)
            self.file_info_text.insert(1.0, info_text)
            
        except Exception as e:
            self.file_info_text.delete(1.0, tk.END)
            self.file_info_text.insert(1.0, f"Error reading file info: {str(e)}")
    
    def get_file_type_description(self, extension):
        """Get a description of the file type based on extension"""
        type_map = {
            # Archives
            '.zip': 'ZIP Archive', '.rar': 'RAR Archive', 
            '.7z': '7-Zip Archive', '.tar': 'TAR Archive',
            '.gz': 'GZIP Compressed', '.xz': 'XZ Compressed',
            '.bz2': 'BZIP2 Compressed', '.tgz': 'TAR+GZIP Archive',
            '.txz': 'TAR+XZ Archive', '.zst': 'Zstandard Archive',
            
            # Images
            '.png': 'PNG Image', '.jpg': 'JPEG Image', '.jpeg': 'JPEG Image',
            '.gif': 'GIF Image', '.bmp': 'BMP Image', '.tiff': 'TIFF Image',
            '.webp': 'WebP Image', '.heic': 'HEIC Image', '.raw': 'Raw Image',
            
            # Documents
            '.pdf': 'PDF Document', '.doc': 'Word Document (Legacy)', 
            '.docx': 'Word Document', '.txt': 'Text File',
            '.rtf': 'Rich Text Format', '.odt': 'OpenDocument Text',
            '.xls': 'Excel Spreadsheet (Legacy)', '.xlsx': 'Excel Spreadsheet',
            '.ppt': 'PowerPoint (Legacy)', '.pptx': 'PowerPoint',
            
            # Memory dumps
            '.mem': 'Memory Dump', '.dump': 'Memory Dump', 
            '.dmp': 'Windows Memory Dump', '.raw': 'Raw Memory Dump',
            '.vmem': 'VMware Memory Dump',
            
            # Disk images
            '.dd': 'DD Disk Image', '.img': 'Raw Disk Image', 
            '.iso': 'ISO Disk Image', '.vmdk': 'VMware Virtual Disk',
            '.vhd': 'Virtual Hard Disk', '.vhdx': 'Virtual Hard Disk v2',
            '.qcow2': 'QEMU Disk Image', '.dmg': 'Apple Disk Image',
            
            # Forensic files
            '.e01': 'EnCase Evidence File', '.ex01': 'EnCase Evidence File',
            '.l01': 'Logical Evidence File', '.ad1': 'AccessData Image',
            '.aff': 'Advanced Forensic Format', '.awu': 'AWF Forensic Image',
            
            # Network captures
            '.pcap': 'Packet Capture', '.pcapng': 'Next Generation Packet Capture',
            '.cap': 'Capture File', '.netxml': 'Network XML',
            
            # Email files
            '.pst': 'Outlook Personal Store', '.ost': 'Outlook Offline Store',
            '.mbox': 'MBOX Email Archive', '.eml': 'Email Message',
            '.msg': 'Outlook Message',
            
            # Registry files
            '.reg': 'Registry File', '.dat': 'Registry Hive',
            
            # Executables
            '.exe': 'Windows Executable', '.bin': 'Binary File',
            '.elf': 'ELF Executable', '.out': 'Executable Output',
            '.app': 'macOS Application', '.msi': 'Windows Installer',
            
            # Logs and data
            '.log': 'Log File', '.csv': 'CSV Data', '.json': 'JSON Data',
            '.xml': 'XML Data',
            
            # Databases
            '.db': 'Database File', '.sqlite': 'SQLite Database',
            '.mdb': 'Microsoft Access Database', '.accdb': 'Access Database',
            '.sql': 'SQL Script'
        }
        
        return type_map.get(extension.lower(), f'Unknown File Type ({extension})')
    
    def browse_output(self):
        try:
            filename = filedialog.asksaveasfilename(
                title="Save CSV File",
                initialdir=self.working_dir.get(),
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                self.output_file.set(filename)
        except Exception as e:
            self.show_error("File Save Error", str(e))
            
    def show_error(self, title, message):
        """Thread-safe error display"""
        if self.running:
            self.root.after(0, lambda: messagebox.showerror(title, message))
            
    def show_info(self, title, message):
        """Thread-safe info display"""
        if self.running:
            self.root.after(0, lambda: messagebox.showinfo(title, message))
            
    def start_profiling(self, queue_mode=False):
        if not self.program_path.get():
            self.show_error("Error", "Please select a program to profile")
            return
            
        # Check if program exists
        program = self.program_path.get()
        full_path = program if os.path.isabs(program) else os.path.join(self.working_dir.get(), program)
        if not os.path.exists(full_path):
            self.show_error("Error", f"Program not found: {program}")
            return
        
        # Check if input file is selected or queue has files
        if not queue_mode and not self.input_file.get():
            self.show_error("Error", "Please select an input file")
            return
        
        # Parse base arguments
        self.base_args = self.base_args_var.get().split()
        
        # Update data_dir based on base_args
        if len(self.base_args) >= 3 and self.base_args[1] == "-d":
            self.data_dir = os.path.join(self.working_dir.get(), self.base_args[2])
        else:
            self.data_dir = os.path.join(self.working_dir.get(), "Testdata")
            
        # Clear previous data if not in queue mode
        if not queue_mode:
            self.clear_data()
        
        # Update UI state
        self.is_profiling = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Profiling in progress...")
        
        # Clear output files list before starting
        self.output_files = []
        
        # Start profiling in a separate thread
        if queue_mode:
            self.monitor_thread = threading.Thread(target=self.run_profiler_queue, daemon=True)
        else:
            self.monitor_thread = threading.Thread(target=self.run_profiler, daemon=True)
        self.monitor_thread.start()
    
    def run_profiler_queue(self):
        """Process multiple files in queue"""
        try:
            total_files = len(self.processing_queue)
            for idx, file_to_process in enumerate(self.processing_queue, 1):
                if not self.is_profiling or not self.running:
                    break
                    
                self.current_artifact = file_to_process
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Processing {idx}/{total_files}: {os.path.basename(file_to_process)}"))
                
                # Process single file
                self._process_single_file(file_to_process)
                
                # Add to processed artifacts (using set)
                self.processed_artifacts.add(file_to_process)
                
                # Update artifact tree (clear and rebuild to avoid duplicates)
                self.root.after(0, self.refresh_artifact_tree)
                
                # Small delay between files
                time.sleep(0.5)
            
            self.root.after(0, lambda: self.status_label.config(text="Queue processing completed"))
            self.root.after(0, self.scan_output_files)
            
        except Exception as e:
            self.show_error("Error", f"Queue processing error: {str(e)}")
        finally:
            if self.running:
                self.root.after(0, self.update_ui_stopped)
    
    def refresh_artifact_tree(self):
        """Refresh the artifact tree to avoid duplicates"""
        # Clear existing items
        for item in self.artifact_tree.get_children():
            self.artifact_tree.delete(item)
        
        # Add all processed artifacts
        for artifact in self.processed_artifacts:
            output_count = len(self.all_output_files.get(artifact, []))
            self.artifact_tree.insert('', 'end', values=(
                os.path.basename(artifact), 'Completed', f"{output_count} files"))
    
    def _process_single_file(self, file_to_process):
        """Process a single file and collect metrics"""
        proc = None  # Local reference to process
        p = None     # Local reference to psutil process
        try:
            # Change to working directory
            os.chdir(self.working_dir.get())
            
            # Build command
            program = self.program_path.get()
            
            cmd = [program] + self.base_args + [file_to_process]
            
            print(f"DEBUG: Running command: {cmd}")
            
            # Show what's being processed
            file_ext = os.path.splitext(file_to_process)[1].lower()
            archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz', '.xz', '.bz2', '.tgz', '.txz']
            if file_ext in archive_exts:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Processing archive: {os.path.basename(file_to_process)}"))
            
            # Record start time
            start_time = time.time()
            
            # Start process with pipes to capture output - use non-blocking mode
            proc = subprocess.Popen(cmd, 
                                   cwd=self.working_dir.get(), 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   stdin=subprocess.PIPE,  # Add stdin to prevent hanging
                                   text=True,
                                   bufsize=1)  # Line buffered
            self.proc = proc  # Store in instance for stop button
            
            # Wait a moment for process to start
            time.sleep(0.5)
            
            # Try to get process metrics immediately
            initial_cpu = 0
            initial_mem = 0
            initial_threads = 0
            
            try:
                p = psutil.Process(proc.pid)
                
                # Get initial metrics right away
                initial_cpu = p.cpu_percent() / os.cpu_count()
                initial_mem = p.memory_info().rss / (1024 * 1024)
                initial_threads = p.num_threads()
                
                print(f"DEBUG: Initial metrics for {os.path.basename(file_to_process)} - CPU: {initial_cpu}, RAM: {initial_mem}, Threads: {initial_threads}")
                
            except psutil.NoSuchProcess:
                print(f"DEBUG: Process ended too quickly - no initial metrics")
                p = None
            
            file_timestamps = []
            file_cpu_data = []
            file_memory_data = []
            file_thread_data = []
            
            # Get input file size
            input_file_size = os.path.getsize(file_to_process) / (1024 * 1024)  # Convert to MB
            output_files_size = 0
            
            # Set a timeout for the entire process (e.g., 30 seconds)
            process_timeout = 30  # seconds
            max_samples = 100  # Maximum number of samples to collect
            
            # If we have a valid process, try to collect data
            if p:
                sample_count = 0
                # Continue sampling while process runs
                while (self.is_profiling and self.running and 
                       sample_count < max_samples and 
                       time.time() - start_time < process_timeout):
                    try:
                        # Check if process is still running with a short timeout
                        try:
                            return_code = proc.poll()
                            if return_code is not None:
                                print(f"DEBUG: Process finished with return code: {return_code}")
                                break
                        except:
                            break
                        
                        current_time = time.time() - start_time
                        sample_count += 1
                        
                        # Collect metrics
                        with self.data_lock:
                            cpu = p.cpu_percent() / os.cpu_count()
                            mem = p.memory_info().rss / (1024 * 1024)
                            threads = p.num_threads()
                            
                            file_timestamps.append(current_time)
                            file_cpu_data.append(cpu)
                            file_memory_data.append(mem)
                            file_thread_data.append(threads)
                            
                            # Store in main data
                            self.timestamps.append(current_time + (len(self.processed_artifacts) * 1000))
                            self.cpu_data.append(cpu)
                            self.memory_data.append(mem)
                            self.thread_data.append(threads)
                            
                            print(f"DEBUG: Sample {sample_count} for {os.path.basename(file_to_process)} - CPU: {cpu:.2f}, RAM: {mem:.2f}")
                        
                        # Update GUI
                        if self.running:
                            self.root.after(0, self.update_plots)
                            self.root.after(0, lambda: self.update_tree(current_time, cpu, mem, threads))
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        print(f"DEBUG: Process access error: {e}")
                        break
                    except Exception as e:
                        print(f"DEBUG: Sampling error: {e}")
                        break
                        
                    # Small sleep to prevent CPU overload
                    time.sleep(max(0.01, self.sample_rate.get()))
                
                # Check if we hit timeout
                if time.time() - start_time >= process_timeout:
                    print(f"DEBUG: Process timeout after {process_timeout}s")
                    # Kill the process if it's still running
                    if proc and proc.poll() is None:
                        try:
                            proc.kill()
                        except:
                            pass
            
            # Get the final execution time
            end_time = time.time()
            exec_time = end_time - start_time
            
            # Kill the process if it's still running (forcefully)
            if proc and proc.poll() is None:
                print(f"DEBUG: Force killing process")
                try:
                    # Try to kill the entire process tree
                    try:
                        parent = psutil.Process(proc.pid)
                        children = parent.children(recursive=True)
                        for child in children:
                            try:
                                child.kill()
                            except:
                                pass
                        parent.kill()
                    except:
                        proc.kill()
                    proc.wait(timeout=2)
                except:
                    pass
            
            # Try to read output with timeout
            try:
                stdout, stderr = proc.communicate(timeout=2)
                if stdout:
                    print(f"DEBUG: stdout: {stdout[:200]}")  # Print first 200 chars
                if stderr:
                    print(f"DEBUG: stderr: {stderr[:200]}")
            except subprocess.TimeoutExpired:
                print(f"DEBUG: communicate timeout")
                proc.kill()
                stdout, stderr = proc.communicate()
            except:
                pass
            
            # Scan for output files created by this artifact and calculate total size
            artifact_outputs = self.scan_output_files_for_artifact(file_to_process)
            for file_path in artifact_outputs:
                if os.path.exists(file_path):
                    output_files_size += os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            
            # Calculate metrics - use collected samples or fallback to final attempt
            if file_timestamps:
                # We have samples - calculate averages
                avg_cpu = sum(file_cpu_data) / len(file_cpu_data)
                avg_mem = sum(file_memory_data) / len(file_memory_data)
                avg_threads = sum(file_thread_data) / len(file_thread_data)
                
                print(f"DEBUG: Using {len(file_timestamps)} samples for {os.path.basename(file_to_process)}")
                
            else:
                # No samples collected
                print(f"DEBUG: No samples for {os.path.basename(file_to_process)}")
                
                # Try to get final metrics if process still exists
                final_cpu = initial_cpu
                final_mem = initial_mem
                final_threads = initial_threads
                
                try:
                    if p and p.is_running():
                        final_cpu = p.cpu_percent() / os.cpu_count()
                        final_mem = p.memory_info().rss / (1024 * 1024)
                        final_threads = p.num_threads()
                except:
                    pass
                
                # Add an entry to the raw data tree
                if self.running:
                    self.root.after(0, lambda: self.update_tree(exec_time, final_cpu, final_mem, final_threads))
                
                avg_cpu = final_cpu
                avg_mem = final_mem
                avg_threads = final_threads
                
                # Add this sample to the data arrays for plotting
                with self.data_lock:
                    self.timestamps.append(exec_time + (len(self.processed_artifacts) * 1000))
                    self.cpu_data.append(final_cpu)
                    self.memory_data.append(final_mem)
                    self.thread_data.append(final_threads)
                
                # Update plots
                if self.running:
                    self.root.after(0, self.update_plots)
            
            # Store metrics for this artifact - use artifact name as key to avoid duplicates
            artifact_name = os.path.basename(file_to_process)
            artifact_metric = {
                'description': artifact_name,
                'execution_time': round(exec_time, 2),
                'avg_cpu': round(avg_cpu, 2),
                'avg_ram': round(avg_mem, 2),
                'avg_threads': round(avg_threads, 2)
            }
            
            # Only add if not already present, or update if needed
            self.artifact_metrics[artifact_name] = artifact_metric
            
            # Append to CSV file (only once per artifact)
            self.append_to_csv(artifact_metric)
            
            # Add file summary to results text
            summary = f"""
{'─'*50}
Artifact: {artifact_name}
Execution Time: {exec_time:.2f}s | Avg CPU: {avg_cpu:.2f}% | Avg RAM: {avg_mem:.2f} MB | Avg Threads: {avg_threads:.1f}
Output Files: {len(artifact_outputs)} | Samples Collected: {len(file_timestamps)}
{'─'*50}
"""
            self.root.after(0, lambda s=summary: self.results_text.insert(tk.END, s))
            self.root.after(0, lambda: self.results_text.see(tk.END))
            
        except Exception as e:
            print(f"Error processing {file_to_process}: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Ensure process is cleaned up
            if proc and proc.poll() is None:
                try:
                    # Try to kill the entire process tree
                    try:
                        parent = psutil.Process(proc.pid)
                        children = parent.children(recursive=True)
                        for child in children:
                            try:
                                child.kill()
                            except:
                                pass
                        parent.kill()
                    except:
                        proc.kill()
                except:
                    pass
            self.proc = None
            print(f"DEBUG: Finished processing {os.path.basename(file_to_process)}")
    
    def run_profiler(self):
        """Process a single file"""
        try:
            file_to_process = self.input_file.get()
            self.current_artifact = file_to_process
            
            # Process the file
            self._process_single_file(file_to_process)
            
            # Add to processed artifacts (using set)
            self.processed_artifacts.add(file_to_process)
            
            # Refresh artifact tree
            self.root.after(0, self.refresh_artifact_tree)
            
        except FileNotFoundError as e:
            self.show_error("Error", f"Program not found: {str(e)}")
        except PermissionError as e:
            self.show_error("Error", f"Permission denied: {str(e)}\nTry running with sudo if needed.")
        except Exception as e:
            self.show_error("Error", f"Profiling error: {str(e)}")
        finally:
            if self.running:
                self.root.after(0, self.update_ui_stopped)
                self.root.after(0, self.scan_output_files)
                self.root.after(0, self.generate_summary)
    
    def append_to_csv(self, metric):
        """Append a single artifact's metrics to the CSV file - ONLY the columns you want"""
        try:
            filename = self.output_file.get()
            if not filename:
                filename = f"profile_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
            # Ensure full path
            if not os.path.isabs(filename):
                filename = os.path.join(self.working_dir.get(), filename)
            
            # Check if file exists to determine if we need to write headers
            file_exists = os.path.isfile(filename)
            
            # Read existing entries to avoid duplicates
            existing_artifacts = set()
            if file_exists:
                try:
                    with open(filename, 'r') as f:
                        reader = csv.reader(f)
                        next(reader)  # Skip header
                        for row in reader:
                            if row and len(row) > 0:
                                existing_artifacts.add(row[0])  # Artifact name is first column
                except:
                    pass
            
            # Only write if this artifact hasn't been written before
            if metric['description'] not in existing_artifacts:
                with open(filename, 'a', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write headers if file is new
                    if not file_exists:
                        headers = [
                            'Artifact Name',
                            'DUES Storing Execution time',
                            'DUES Store CPU Usages (%)',
                            'DUES Store RAM Usages (MB)',
                            'DUES Threads'
                        ]
                        writer.writerow(headers)
                        print(f"DEBUG: Wrote headers: {headers}")
                    
                    # Write the metric data
                    row = [
                        metric['description'],
                        metric['execution_time'],
                        metric['avg_cpu'],
                        metric['avg_ram'],
                        metric['avg_threads']
                    ]
                    writer.writerow(row)
                    print(f"DEBUG: Wrote row for {metric['description']}")
                
                # Update status on GUI
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Appended {metric['description']} to {os.path.basename(filename)}"))
            else:
                print(f"DEBUG: Skipping duplicate entry for {metric['description']}")
            
        except Exception as e:
            print(f"DEBUG: CSV Error - {str(e)}")
            self.show_error("Error", f"Failed to append to CSV: {str(e)}")
    
    def scan_output_files_for_artifact(self, artifact_path):
        """Scan for output files created by a specific artifact"""
        try:
            artifact_outputs = []
            
            # Check if data directory exists
            if os.path.exists(self.data_dir):
                # Get all files in data directory
                for root, dirs, files in os.walk(self.data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Check if file was created recently (within last 2 minutes)
                        mod_time = os.path.getmtime(file_path)
                        if time.time() - mod_time < 120:  # Within last 2 minutes
                            artifact_outputs.append(file_path)
            
            # Store in dictionary
            self.all_output_files[artifact_path] = artifact_outputs
            
            # Update output tree for this artifact
            for file_path in artifact_outputs:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                mod_time_str = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                rel_path = os.path.relpath(file_path, self.working_dir.get())
                
                self.root.after(0, lambda a=artifact_path, f=file_name, s=file_size, m=mod_time_str, p=rel_path: 
                               self.output_tree.insert('', 'end', values=(
                                   os.path.basename(a), f, self.format_bytes(s), m, p)))
            
            return artifact_outputs
            
        except Exception as e:
            print(f"Error scanning output files for artifact: {e}")
            return []
    
    def scan_output_files(self):
        """Scan all output files"""
        try:
            # Clear existing items
            for item in self.output_tree.get_children():
                self.output_tree.delete(item)
            
            self.output_files = []
            
            # Check all processed artifacts
            for artifact in self.processed_artifacts:
                if artifact in self.all_output_files:
                    for file_path in self.all_output_files[artifact]:
                        if os.path.exists(file_path):
                            file_name = os.path.basename(file_path)
                            file_size = os.path.getsize(file_path)
                            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                            rel_path = os.path.relpath(file_path, self.working_dir.get())
                            
                            self.output_files.append(file_path)
                            
                            self.output_tree.insert('', 'end', values=(
                                os.path.basename(artifact),
                                file_name,
                                self.format_bytes(file_size),
                                mod_time,
                                rel_path
                            ))
            
            # Update status if files found
            if self.output_files:
                self.status_label.config(text=f"Found {len(self.output_files)} output files from {len(self.processed_artifacts)} artifacts")
                    
        except Exception as e:
            print(f"Error scanning output files: {e}")
            
    def stop_profiling(self):
        """Stop the current profiling session"""
        self.is_profiling = False
        if self.proc:
            try:
                print(f"DEBUG: Stopping process {self.proc.pid}")
                # Kill the entire process tree
                try:
                    parent = psutil.Process(self.proc.pid)
                    # Kill all children first
                    for child in parent.children(recursive=True):
                        try:
                            child.kill()
                            print(f"DEBUG: Killed child process {child.pid}")
                        except:
                            pass
                    # Kill parent
                    parent.kill()
                    print(f"DEBUG: Killed parent process {self.proc.pid}")
                except psutil.NoSuchProcess:
                    try:
                        self.proc.kill()
                    except:
                        pass
                except Exception as e:
                    print(f"DEBUG: Error killing process: {e}")
                    try:
                        self.proc.kill()
                    except:
                        pass
            except:
                pass
            finally:
                self.proc = None
        
    def update_plots(self):
        if not self.running or not self.timestamps:
            return
            
        try:
            with self.data_lock:
                # Update CPU plot
                self.cpu_line.set_data(self.timestamps, self.cpu_data)
                self.ax1.relim()
                self.ax1.autoscale_view()
                
                # Update Memory plot
                self.memory_line.set_data(self.timestamps, self.memory_data)
                self.ax2.relim()
                self.ax2.autoscale_view()
                
                # Update Thread plot
                self.thread_line.set_data(self.timestamps, self.thread_data)
                self.ax3.relim()
                self.ax3.autoscale_view()
                
            self.canvas.draw_idle()
        except Exception as e:
            print(f"Plot update error: {e}")
        
    def update_tree(self, timestamp, cpu, mem, threads):
        if not self.running:
            return
        
        try:
            # Format the values nicely
            timestamp_str = f"{timestamp:.3f}"
            cpu_str = f"{cpu:.2f}"
            mem_str = f"{mem:.2f}"
            threads_str = str(int(threads))  # Convert to integer for display
        
            # Insert at the end
            self.data_tree.insert('', 'end', values=(
                timestamp_str,
                cpu_str,
                mem_str,
                threads_str
            ))
        
            # Auto-scroll to the latest entry
            self.data_tree.yview_moveto(1)
        
            # Also update the status to show we're still processing
            if hasattr(self, 'current_artifact') and self.current_artifact:
                self.status_label.config(text=f"Processing: {os.path.basename(self.current_artifact)} - Sample {len(self.timestamps)}")
            
        except Exception as e:
            print(f"Tree update error: {e}")
        
    def generate_summary(self):
        if not self.cpu_data or not self.running:
            return
            
        try:
            with self.data_lock:
                avg_cpu = sum(self.cpu_data) / len(self.cpu_data) if self.cpu_data else 0
                peak_cpu = max(self.cpu_data) if self.cpu_data else 0
                
                avg_mem = sum(self.memory_data) / len(self.memory_data) if self.memory_data else 0
                peak_mem = max(self.memory_data) if self.memory_data else 0
                
                avg_threads = sum(self.thread_data) / len(self.thread_data) if self.thread_data else 0
                peak_threads = max(self.thread_data) if self.thread_data else 0
            
            # Overall summary
            summary = f"""
{'='*60}
OVERALL PROFILING SUMMARY
{'='*60}

Program: {self.program_path.get()}
Working Directory: {self.working_dir.get()}

Artifacts Processed: {len(self.processed_artifacts)}
Total Output Files: {len(self.output_files)}

Overall Statistics (all artifacts):
  - Total Execution Samples: {len(self.cpu_data)}
  - Average CPU: {avg_cpu:.2f}%
  - Peak CPU: {peak_cpu:.2f}%
  - Average Memory: {avg_mem:.2f} MB
  - Peak Memory: {peak_mem:.2f} MB
  - Average Threads: {avg_threads:.1f}
  - Peak Threads: {peak_threads}

Output CSV: {self.output_file.get()}
{'='*60}

Processed Artifacts Summary:
"""
            
            # Add each artifact's summary from metrics (using dict values)
            for metric in self.artifact_metrics.values():
                summary += f"\n  • {metric['description']} - Time: {metric['execution_time']}s, CPU: {metric['avg_cpu']}%, RAM: {metric['avg_ram']} MB, Threads: {metric['avg_threads']}"
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, summary)
            
        except Exception as e:
            print(f"Summary generation error: {e}")
        
    def save_to_csv(self):
        """Save raw data to CSV (optional - can be removed if not needed)"""
        if not self.running:
            return
            
        try:
            filename = f"raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            if not os.path.isabs(filename):
                filename = os.path.join(self.working_dir.get(), filename)
                
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'CPU %', 'Memory (MB)', 'Threads'])
                
                with self.data_lock:
                    for i in range(len(self.timestamps)):
                        writer.writerow([
                            f"{self.timestamps[i]:.3f}",
                            f"{self.cpu_data[i]:.2f}",
                            f"{self.memory_data[i]:.2f}",
                            self.thread_data[i] if i < len(self.thread_data) else 0
                        ])
                        
            self.status_label.config(text=f"Raw data saved to {os.path.basename(filename)}")
        except Exception as e:
            self.show_error("Error", f"Failed to save CSV: {str(e)}")
            
    def clear_data(self):
        with self.data_lock:
            self.timestamps = []
            self.cpu_data = []
            self.memory_data = []
            self.thread_data = []
        
        # Clear processed artifacts
        self.processed_artifacts = set()  # Changed to set
        self.all_output_files = {}
        self.output_files = []
        self.artifact_metrics = {}  # Changed to dict
        
        # Clear tree
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        for item in self.artifact_tree.get_children():
            self.artifact_tree.delete(item)
        
        for item in self.output_tree.get_children():
            self.output_tree.delete(item)
            
        # Clear text
        self.results_text.delete(1.0, tk.END)
        self.file_info_text.delete(1.0, tk.END)
        
        # Clear plots
        self.cpu_line.set_data([], [])
        self.memory_line.set_data([], [])
        self.thread_line.set_data([], [])
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.ax3.relim()
        self.ax3.autoscale_view()
        self.canvas.draw_idle()
        
    def clear_results(self):
        self.clear_data()
        self.status_label.config(text="Ready")
        self.selected_file_label.config(text="No file selected")
        self.processing_queue = []
        self.update_queue_display()
        
    def update_ui_stopped(self):
        if not self.running:
            return
            
        self.is_profiling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if self.timestamps:
            self.status_label.config(text="Profiling completed")
        else:
            self.status_label.config(text="Profiling stopped")
            
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.is_profiling = False
        
        # Stop the subprocess if running
        if self.proc:
            try:
                # Kill the entire process tree
                parent = psutil.Process(self.proc.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except:
                        pass
                parent.kill()
            except:
                try:
                    self.proc.kill()
                except:
                    pass
        
        # Close matplotlib figures
        plt.close('all')
        
        # Destroy the window
        self.root.destroy()
            
    @staticmethod
    def format_bytes(bytes_val):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"


def main():
    try:
        root = tk.Tk()
        app = ProfilerGUI(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nProfiler stopped by user")
    except Exception as e:
        print(f"Error starting GUI: {e}")


if __name__ == "__main__":
    main()
