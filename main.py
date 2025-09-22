import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import configparser
import json
import os
from typing import Dict, List, Any
import threading
import time
import sv_ttk
from tktooltip import ToolTip
import subprocess



class Editor:
    def __init__(self, root):
        self.root = root
        self.root.title("EasyINI")
        self.root.geometry("1200x800")

        #Set theme and styling
        # self.setup_styling()

        #Data storage
        self.config_data = self.load_config()
        self.current_file = None
        self.current_ini_data = None
        self.config_unlocked = False

        self.main_container = tk.Frame(root, bg='#000B0F')
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.create_config_page()
        self.create_editor_page()
        self.refresh_file_list()

    def setup_styling(self):
        style = ttk.Style()
        style.theme_use("clam")  # clam allows full custom styling

        # --- Core Colors (only 2 total) ---
        BASE = "#1a1a1a"      # Dark background
        ACCENT = "#4CAF50"    # Accent (Green)

        # --- Frames (3D look with relief) ---
        style.configure("Header.TFrame", background=BASE, padding=5, relief="raised", borderwidth=2)
        style.configure("Card.TFrame", background=BASE, relief="groove", borderwidth=2, padding=10)

        # --- Labels ---
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), background=BASE, foreground=ACCENT)
        style.configure("Bold.TLabel", font=("Segoe UI", 10, "bold"), background=BASE, foreground=ACCENT)
        style.configure("TLabel", background=BASE, foreground=ACCENT)

        # --- Buttons (3D, green accent) ---
        style.configure(
            "TButton",
            font=("Segoe UI", 9, "bold"),
            padding=6,
            relief="raised",
            background=ACCENT,
            foreground=BASE,
            borderwidth=2
        )
        style.map(
            "TButton",
            background=[("active", "#45a049"), ("pressed", "#2e7d32")],
            relief=[("pressed", "sunken")],
            foreground=[("disabled", "#555555")]
        )

        # --- Treeview (Dark + 3D) ---
        style.configure(
            "Treeview",
            background=BASE,
            foreground=ACCENT,
            fieldbackground=BASE,
            bordercolor=ACCENT,
            borderwidth=1,
            relief="groove",
            rowheight=25
        )
        style.configure("Treeview.Heading", background=ACCENT, foreground=BASE, relief="raised", borderwidth=1)
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", BASE)])

        # --- Scrollbar (Dark + Minimal 3D) ---
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=BASE,
            darkcolor=ACCENT,
            lightcolor=BASE,
            troughcolor=BASE,
            bordercolor=ACCENT,
            arrowcolor=ACCENT,
            relief="sunken"
        )

    def create_config_page(self):
        """Create the configuration page"""
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Config")
    
        # File configuration section
        file_frame = ttk.Frame(self.config_frame, style="Card.TFrame")
        file_frame.pack(fill=tk.X, padx=15, pady=10)
    
        # Card header
        card_header = ttk.Frame(file_frame, style="Header.TFrame", height=30)
        card_header.pack(fill=tk.X)
        card_header.pack_propagate(False)
    
        # Card content
        card_content = ttk.Frame(file_frame, style="Card.TFrame", padding=15)
        card_content.pack(fill=tk.X)
    
        # File path selection
        path_frame = ttk.Frame(card_content)
        path_frame.pack(fill=tk.X, pady=5)
    
        ttk.Label(
            path_frame,
            text="File Path:",
            style="Bold.TLabel"
        ).pack(side=tk.LEFT)
    
        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(
            path_frame,
            textvariable=self.file_path_var,
            width=50
        )
        self.file_path_entry.pack(side=tk.LEFT, padx=10)
    
        browse_btn = ttk.Button(
            path_frame,
            text="Browse",
            command=self.browse_file,
            style="Action.TButton"
        )
        browse_btn.pack(side=tk.LEFT, padx=5)
    
        # File name
        name_frame = ttk.Frame(card_content)
        name_frame.pack(fill=tk.X, pady=5)
    
        self.file_name_var = tk.StringVar()
    
        # Add file button
        add_btn = ttk.Button(
            path_frame,
            text="Add File",
            command=self.add_file,
            style="Action.TButton"
        )
        add_btn.pack(side=tk.LEFT, padx=5)

        dwvci_btn = ttk.Button(
            path_frame,
            text="Launch DWVCIUtility_3.0.1.exe",
            command=lambda: launch_exe("DWVCIUtility_3.0.1.exe"),
            style="Action.TButton"
        )
        dwvci_btn.pack(side=tk.RIGHT, padx=5)
        
        playback_btn = ttk.Button(
            path_frame,
            text="Launch PlaybackXE.exe",
            command=lambda: launch_exe("PlaybackXE.exe"),
            style="Action.TButton"
        )
        playback_btn.pack(side=tk.RIGHT, padx=5)
    
        # Files list
        files_list_frame = ttk.Frame(self.config_frame, style="Card.TFrame")
        files_list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    
        # Card header
        files_header = ttk.Frame(files_list_frame, style="Header.TFrame", height=30)
        files_header.pack(fill=tk.X)
        files_header.pack_propagate(False)
    
        ttk.Label(
            files_header,
            text="Configured Files",
            style="Header.TLabel"
        ).pack(side=tk.LEFT, padx=10, pady=5)
    
        # Card content
        files_content = ttk.Frame(files_list_frame)
        files_content.pack(fill=tk.BOTH, expand=True)
    
        # Treeview for files
        columns = ("Name", "Path", "Fields")
        self.files_tree = ttk.Treeview(files_content, columns=columns, show="headings", height=8)
    
        for col in columns:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=200)
    
        self.files_tree.pack(fill=tk.BOTH, expand=True)
    
        # Buttons for file management
        file_buttons_frame = ttk.Frame(files_content)
        file_buttons_frame.pack(fill=tk.X, pady=10)
    
        edit_btn = ttk.Button(
            file_buttons_frame,
            text="Edit",
            command=self.edit_fields,
            style="Action.TButton"
        )
        edit_btn.pack(side=tk.LEFT, padx=5)
    
        remove_btn = ttk.Button(
            file_buttons_frame,
            text="Remove File",
            command=self.remove_file,
            style="Danger.TButton"
        )
        remove_btn.pack(side=tk.LEFT, padx=5)

    def check_config_password(self):
        """Check password for configuration access"""
        if self.config_unlocked:
            return True
            
        password = simpledialog.askstring("Configuration Access", 
                                        "Enter password to access configuration:", 
                                        show='*')
        if password == "admin123":  # Hardcoded password
            self.config_unlocked = True
            return True
        else:
            messagebox.showerror("Access Denied", "Incorrect password!")
            return False        

    def browse_file(self):
        """Browse for INI file"""
        filename = filedialog.askopenfilename(
            title="Select INI File",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            # Auto-fill display name
            if not self.file_name_var.get():
                self.file_name_var.set(os.path.basename(filename))

    def add_file(self):
        """Add a new file to configuration"""
        # Check password protection
        if not self.check_config_password():
            return
            
        path = self.file_path_var.get().strip()
        name = self.file_name_var.get().strip()
        
        if not path or not name:
            messagebox.showerror("Error", "Please provide both file path")
            return
        
        if not os.path.exists(path):
            messagebox.showerror("Error", "File does not exist")
            return
        
        # Check if file already exists
        for file_config in self.config_data["files"]:
            if file_config["path"] == path:
                messagebox.showerror("Error", "File already configured")
                return
        
        # Add new file
        new_file = {
            "name": name,
            "path": path,
            "fields": []
        }
        
        self.config_data["files"].append(new_file)
        self.save_config()
        self.refresh_file_list()
        
        # Clear form
        self.file_path_var.set("")
        self.file_name_var.set("")
        
        messagebox.showinfo("Success", f"File '{name}' added successfully")
    
    def remove_file(self):
        """Remove selected file from configuration"""
        # Check password protection
        if not self.check_config_password():
            return
            
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to remove")
            return
        
        item = self.files_tree.item(selection[0])
        file_name = item['values'][0]
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to remove '{file_name}'?"):
            # Remove from config
            self.config_data["files"] = [f for f in self.config_data["files"] if f["name"] != file_name]
            self.save_config()
            self.refresh_file_list()

    def edit_fields(self):
        """Edit fields for selected file"""
        # Check password protection
        if not self.check_config_password():
            return
            
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to edit fields")
            return
        
        item = self.files_tree.item(selection[0])
        file_name = item['values'][0]
        
        # Find file config
        file_config = None
        for f in self.config_data["files"]:
            if f["name"] == file_name:
                file_config = f
                break
        
        if file_config:
            self.show_fields_dialog(file_config)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists('editor_config.json'):
                with open('editor_config.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"files": []}

    def save_config(self):
        """Save configuration to JSON file"""
        with open('editor_config.json', 'w') as f:
            json.dump(self.config_data, f, indent=2)

    def refresh_file_list(self):
        """Refresh the files list in config page"""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Add files
        for file_config in self.config_data["files"]:
            field_count = len(file_config.get("fields", []))
            self.files_tree.insert("", "end", values=(
                file_config["name"],
                file_config["path"],
                f"{field_count} fields"
            ))
        
        # Update editor file selector
        self.file_selector['values'] = [f["name"] for f in self.config_data["files"]]

    def show_fields_dialog(self, file_config):
        """Show dialog to edit fields for a file"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Fields - {file_config['name']}")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()

        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(file_config["path"], encoding='utf-8-sig')

            # ── Main container
            main_frame = ttk.Frame(dialog, padding=15)
            main_frame.pack(fill=tk.BOTH, expand=True)


            # ── File path editor
            path_editor = ttk.Frame(main_frame)
            path_editor.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(path_editor, text="File Path:", style="Bold.TLabel").pack(side=tk.LEFT)
            path_var = tk.StringVar(value=file_config.get("path", ""))
            path_entry = ttk.Entry(path_editor, textvariable=path_var)
            path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

            def _browse_new_path():
                new_path = filedialog.askopenfilename(title="Select INI File", filetypes=[("INI files", "*.ini"), ("All files", "*.*")])
                if new_path:
                    path_var.set(new_path)

            ttk.Button(path_editor, text="Browse", command=_browse_new_path, style="TButton").pack(side=tk.LEFT)

            # ── Fields card
            fields_card = ttk.Frame(main_frame)
            fields_card.pack(fill=tk.BOTH, expand=True, pady=10)

            # Card header
            card_header = ttk.Frame(fields_card, style="Header.TFrame", height=30)
            card_header.pack(fill=tk.X)
            card_header.pack_propagate(False)


            # Card content
            card_content = ttk.Frame(fields_card, padding=10, style="Card.TFrame")
            card_content.pack(fill=tk.BOTH, expand=True)

            # Headers
            headers_frame = ttk.Frame(card_content)
            headers_frame.pack(fill=tk.X, pady=5)

            header_style = "Bold.TLabel"
            ttk.Label(headers_frame, text="Section Name", style=header_style, width=20).grid(row=0, column=0, padx=5)
            ttk.Label(headers_frame, text="Key", style=header_style, width=20).grid(row=0, column=1, padx=5)
            ttk.Label(headers_frame, text="Value (CSV)", style=header_style, width=30).grid(row=0, column=2, padx=5)
          
            # Scrollable area (limited height so buttons remain visible)
            scroll_container = ttk.Frame(card_content, style="Card.TFrame")
            scroll_container.pack(fill=tk.BOTH, expand=True, pady=5)

            canvas = tk.Canvas(scroll_container, highlightthickness=0)
            scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
            self.scrollable_fields_frame = ttk.Frame(canvas)

            self.scrollable_fields_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=self.scrollable_fields_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Limit height so buttons always visible
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            scroll_container.configure(height=200)  # 👈 Keeps card scrollable instead of pushing buttons down

            # Buttons frame (always visible)
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill=tk.X, pady=10)

            ttk.Button(
                buttons_frame,
                text="Edit",
                command=lambda: self.add_field_row(self.scrollable_fields_frame),
                style="TButton"
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                buttons_frame,
                text="Save",
                command=lambda: self.save_fields(dialog, file_config, path_var),
                style="TButton"
            ).pack(side=tk.LEFT, padx=5)

            # Load existing fields
            for field in file_config.get("fields", []):
                self.create_field_row(self.scrollable_fields_frame, field)

        except Exception as e:
            messagebox.showerror("Error", f"Could not load INI file: {str(e)}")
            dialog.destroy()

    def create_field_row(self, parent, field_data=None):
        """Create a row for field configuration"""
        if field_data is None:
            field_data = {"section": "", "option": "", "domain": ""}

        # ── Row container (card-like style)
        row_frame = ttk.Frame(parent, style="Card.TFrame", padding=5)
        row_frame.pack(fill=tk.X, pady=3, padx=5)

        # Section Name
        section_var = tk.StringVar(value=field_data.get("section", ""))
        section_entry = ttk.Entry(
            row_frame,
            textvariable=section_var,
            width=20
        )
        section_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Key
        option_var = tk.StringVar(value=field_data.get("option", ""))
        option_entry = ttk.Entry(
            row_frame,
            textvariable=option_var,
            width=20
        )
        option_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Value (CSV) → use Text for multiline
        domain_text = tk.Text(
            row_frame,
            height=2,  # 👈 small text box
            width=30,
            font=("Arial", 9),
            relief="solid",
            bd=1,
            wrap="word"
        )
        domain_text.insert("1.0", field_data.get("domain", ""))
        domain_text.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Remove button
        remove_btn = ttk.Button(
            row_frame,
            text="✕",
            command=lambda: self.remove_field_row(row_frame),
            style="Danger.TButton",
            width=3
        )
        remove_btn.grid(row=0, column=3, padx=5, pady=5)

        # Helper functions to sync Text widget
        def get_domain():
            return domain_text.get("1.0", "end-1c").strip()

        def set_domain(value):
            domain_text.delete("1.0", "end")
            domain_text.insert("1.0", value)

        # Store variables + custom getter/setter
        row_frame.field_vars = {
            "section": section_var,
            "option": option_var,
            "get_domain": get_domain,
            "set_domain": set_domain
        }

    def add_field_row(self, parent):
        """Add a new field row"""
        self.create_field_row(parent)
    
    def remove_field_row(self, row_frame):
        """Remove a field row"""
        row_frame.destroy()
    
    def save_fields(self, dialog, file_config, path_var=None):
       """Save fields configuration and file path"""
       fields = []
    
       # Collect all field rows
       for widget in self.scrollable_fields_frame.winfo_children():
           if hasattr(widget, "field_vars"):
               section = widget.field_vars["section"].get().strip()
               option = widget.field_vars["option"].get().strip()
               domain = widget.field_vars["get_domain"]().strip()  # 👈 Use getter for Text
    
               if section and option:  # Only valid fields
                   fields.append({
                       "section": section,
                       "option": option,
                       "domain": domain,
                       "display": f"{section}.{option}"
                   })
    
       # Update file config
       file_config["fields"] = fields
       # Update path if provided
       if path_var is not None:
           new_path = path_var.get().strip()
           if new_path:
               file_config["path"] = new_path
       self.save_config()
       self.refresh_file_list()
    
       dialog.destroy()
       messagebox.showinfo(
           "Success",
           f"Saved {len(fields)} fields for '{file_config['name']}'"
       )
       # Reload if currently selected
       try:
           if self.current_file and isinstance(self.current_file, dict) and self.current_file.get("name") == file_config.get("name"):
               self.load_ini_file(file_config)
       except Exception:
           pass

    def create_editor_page(self):
        """Create the editor page with themed ttk widgets"""
        self.editor_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.editor_frame, text="Editor")

        # ── File Selection Card
        file_select_card = ttk.Frame(self.editor_frame, style="Card.TFrame", padding=10)
        file_select_card.pack(fill=tk.X, pady=10)
        
        # Card content
        select_content = ttk.Frame(file_select_card, padding=5)
        select_content.pack(fill=tk.X)

        ttk.Label(select_content, text="Select File:", style="Bold.TLabel").pack(side=tk.LEFT)
        self.file_selector = ttk.Combobox(select_content, state="readonly", width=40, font=("Quicksand", 10))
        self.file_selector.pack(side=tk.LEFT, padx=10)
        self.file_selector.bind("<<ComboboxSelected>>", self.on_file_selected)

        ttk.Button(select_content, text="Refresh", command=self.refresh_file_list, style="Action.TButton").pack(side=tk.LEFT, padx=10)

        # ── Main Content Area
        content_frame = ttk.Frame(self.editor_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # ── Left Panel: Preview
        preview_card = ttk.Frame(content_frame, style="Card.TFrame", padding=5)
        preview_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        preview_canvas_frame = ttk.Frame(preview_card)
        preview_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_canvas = tk.Canvas(preview_canvas_frame, highlightthickness=0)
        self.preview_scrollbar = ttk.Scrollbar(preview_canvas_frame, orient="vertical", command=self.preview_canvas.yview)
        self.preview_tables_frame = ttk.Frame(self.preview_canvas)

        self.preview_tables_frame.bind(
            "<Configure>",
            lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
        )

        self.preview_canvas.create_window((0, 0), window=self.preview_tables_frame, anchor="nw")
        self.preview_canvas.configure(yscrollcommand=self.preview_scrollbar.set)

        self.preview_canvas.pack(side="left", fill="both", expand=True)
        self.preview_scrollbar.pack(side="right", fill="y")

        # ── Right Panel: Editor
        editor_card = ttk.Frame(content_frame, style="Card.TFrame", padding=5)
        editor_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(editor_card, text="Edit Fields", style="Header.TLabel").pack(fill=tk.X)

        editor_canvas_frame = ttk.Frame(editor_card)
        editor_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.editor_canvas = tk.Canvas(editor_canvas_frame, highlightthickness=0)
        self.editor_scrollbar = ttk.Scrollbar(editor_canvas_frame, orient="vertical", command=self.editor_canvas.yview)
        self.editor_scrollable_frame = ttk.Frame(self.editor_canvas)

        self.editor_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox("all"))
        )

        self.editor_canvas.create_window((0, 0), window=self.editor_scrollable_frame, anchor="nw")
        self.editor_canvas.configure(yscrollcommand=self.editor_scrollbar.set)

        self.editor_canvas.pack(side="left", fill="both", expand=True)
        self.editor_scrollbar.pack(side="right", fill="y")

        # ── Separate status bar below preview/editor area
        status_bar = ttk.Frame(self.editor_frame)
        status_bar.pack(fill=tk.X, pady=(4, 0))
        self.preview_status = tk.Label(status_bar, text="Changes are saved automatically", anchor='w', fg="#e4e4e4")
        self.preview_status.pack(fill=tk.X)
    
    def on_file_selected(self, event):
        """Handle file selection in editor"""
        selected_name = self.file_selector.get()
        if not selected_name:
            return
        
        # Find file config
        file_config = None
        for f in self.config_data["files"]:
            if f["name"] == selected_name:
                file_config = f
                break
        
        if file_config:
            self.load_ini_file(file_config)

    def save_changes(self):
        """Save changes to INI file"""
        if not self.current_file or not self.current_ini_data:
            messagebox.showwarning("Warning", "No file loaded")
            return
        
        try:
            # Update values from editor fields
            for widget in self.editor_scrollable_frame.winfo_children():
                if hasattr(widget, 'field_data'):
                    section = widget.field_data["section"]
                    option = widget.field_data["option"]
                    new_value = widget.field_data["value_var"].get()
                    
                    if section in self.current_ini_data:
                        self.current_ini_data[section][option] = new_value
            
            # Write to file
            with open(self.current_file["path"], 'w') as f:
                self.current_ini_data.write(f)
            
            # Refresh preview
            self.load_ini_file(self.current_file)
            
          
            messagebox.showinfo("Success", "Changes saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")

    def load_ini_file(self, file_config):
        """Load and display INI file"""
        try:
            self.current_file = file_config
            config = configparser.ConfigParser()
            # Preserve original key case
            config.optionxform = str
            config.read(file_config["path"], encoding="utf-8-sig")
            
            # Store current data
            self.current_ini_data = config
            # for i in config:
                # print(i)
            
            # Update preview display
            self.update_preview_display()
            
            # Create editor fields
            self.create_editor_fields(file_config)

        except Exception as e:
            messagebox.showerror("Error", f"Could not load INI file: {str(e)}")

    def create_editor_fields(self, file_config):
        """Create editor fields based on configuration"""
        # Clear existing fields
        for widget in self.editor_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.current_ini_data:
            return
        
        # Create fields for each configured field
        for field_config in file_config.get("fields", []):
            section = field_config["section"]
            option = field_config["option"]
            display = field_config["display"]
            domain = field_config["domain"]
            
            # Get current value, create section if it doesn't exist
            current_value = ""
            if section not in self.current_ini_data:
                self.current_ini_data.add_section(section)
            elif option in self.current_ini_data[section]:
                current_value = self.current_ini_data[section][option]
            
            # Create field frame with minimal styling
            field_frame = tk.Frame(self.editor_scrollable_frame)
            field_frame.pack(fill=tk.X, pady=3, padx=5)
            
            # Field label
            label_frame = tk.Frame(field_frame, height=25, width=40)
            label_frame.pack(fill=tk.X, expand=True)
            label_frame.pack_propagate(False)
            
            tk.Label(label_frame, 
                    text=f"{display or f'{section}.{option}'}", 
                    font=('Arial', 9, 'bold'),
                    fg="#FFFFFF").pack(side=tk.LEFT, padx=8, pady=3)
            
            # Value input frame
            input_frame = tk.Frame(field_frame, padx=8, pady=8)
            input_frame.pack(fill=tk.X)
            
            # Value input
            if domain and not (section == "DECODE" and option.upper() == "CALIBRATION"): 
                # Dropdown for predefined values 
                values = [v.strip() for v in domain.split(",")] 
                value_var = tk.StringVar(value=current_value) 
                value_combo = ttk.Combobox(input_frame, textvariable=value_var, values=values, state="readonly", font=('Arial', 9), width=40) 
                value_combo.pack(fill=tk.X, pady=2, expand=True) 
                # Bind for live preview 
                value_combo.bind("<<ComboboxSelected>>", lambda e, var=value_var, s=section, o=option: self.update_live_preview(var, s, o)) 
            else: 
                # Textbox (for DECODE.CALIBRATION or when no domain is provided) 
                value_var = tk.StringVar(value=current_value) 
                value_entry = tk.Entry(input_frame, textvariable=value_var, font=('Arial', 9), width=40) 
                value_entry.pack(fill=tk.X, pady=2, expand=True) 
                # Bind for live preview on text change 
                value_entry.bind("<KeyRelease>", lambda e, var=value_var, s=section, o=option: self.update_live_preview(var, s, o))
                # Store reference for saving
            field_frame.field_data = {
                "section": section,
                "option": option,
                "value_var": value_var
            }
    
    def update_live_preview(self, value_var, section, option):
        """Update live preview when field values change"""
        if not self.current_ini_data:
            return
            
        try:
            new_value = value_var.get()
            
            # Create section if it doesn't exist
            if section not in self.current_ini_data:
                self.current_ini_data.add_section(section)
            
            # Update the in-memory data
            self.current_ini_data[section][option] = new_value
            
            # Update the preview text
            self.update_preview_display()

            # Persist immediately for durability
            if self.current_file and 'path' in self.current_file:
                with open(self.current_file['path'], 'w') as f:
                    self.current_ini_data.write(f)
            
            # Update status
            self.preview_status.config(text="File saved", fg="#1fff23")
            
            # Reset status after 2 seconds
            self.root.after(2000, lambda: self.preview_status.config(text="Changes are saved automatically", fg='#e4e4e4'))
            
        except Exception as e:
            print(f"Error updating live preview: {e}")
    
    def update_preview_display(self):
        """Render a non-editable preview as tables per section (Key/Value)."""
        if not self.current_ini_data:
            return

        # Clear existing tables
        for widget in self.preview_tables_frame.winfo_children():
            widget.destroy()

        try:
            # Build set of configured editable fields to highlight
            configured_fields = set()
            if self.current_file and isinstance(self.current_file, dict):
                for f in self.current_file.get('fields', []):
                    configured_fields.add((f.get('section', ''), f.get('option', '')))
            print(configured_fields)
            for section in self.current_ini_data.sections():
                # Section header
                header = tk.Frame(self.preview_tables_frame, bg="#1a1a1a")
                header.pack(fill=tk.X, pady=(0, 4))
                tk.Label(header, text=section, font=('Arial', 10, 'bold'), bg='#15141d', fg="#FFFFFF").pack(anchor='w')

                # Table
                table_frame = tk.Frame(self.preview_tables_frame, bg='white')
                table_frame.pack(fill=tk.X, pady=(0, 10))

                columns = ('Key', 'Value')
                tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=6)
                tree.heading('Key', text='Key')
                tree.heading('Value', text='Value')
                # Disable stretch so horizontal scrollbar becomes effective
                tree.column('Key', width=200, anchor='w', stretch=False)
                tree.column('Value', width=600, anchor='w', stretch=False)

                # Minimal style - strip editing; Treeview is read-only by default
                # Configure highlight tag for fields present in config
                tree.tag_configure('highlight', background="#75a3db", foreground="black")  # subtle highlight

                for option, value in self.current_ini_data.items(section):
                    tag = ()
                    if (section, option) in configured_fields:
                        tag = ('highlight',)
                    # print(option, value)
                    tree.insert('', 'end', values=(option, value), tags=tag)

                # Scrollbars for table (horizontal and vertical)
                vscroll = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
                hscroll = ttk.Scrollbar(table_frame, orient='horizontal', command=tree.xview)
                tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

                # Layout
                tree.pack(side='left', fill='both', expand=True)
                vscroll.pack(side='right', fill='y')
                hscroll.pack(side='bottom', fill='x')

                # Hover status updater at bottom (shows full key/value)
                def _on_tree_motion(event, _tree=tree):
                    row_id = _tree.identify_row(event.y)
                    if not row_id:
                        self.preview_status.config(text="Changes are saved automatically")
                        return
                    values = _tree.item(row_id, 'values')
                    if not values:
                        self.preview_status.config(text="Changes are saved automatically")
                        return
                    key_text = str(values[0]) if len(values) > 0 else ""
                    value_text = str(values[1]) if len(values) > 1 else ""
                    self.preview_status.config(text=f"{key_text} = {value_text}")

                def _on_tree_leave(event):
                    self.preview_status.config(text="Changes are saved automatically")

                tree.bind('<Motion>', _on_tree_motion)
                tree.bind('<Leave>', _on_tree_leave)

        except Exception as e:
            print(f"Error updating preview display: {e}")

import os, sys, subprocess

def launch_exe(exe_name):
    # Get the folder where the main exe is running from
    base_path = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    exe_path = os.path.join(base_path, exe_name)

    try:
        subprocess.Popen([exe_path], shell=False)
    except Exception as e:
        print(f"Error launching {exe_name}: {e}")

def main():
    root = tk.Tk()
    sv_ttk.set_theme("dark") 
    app = Editor(root)
    root.mainloop()


if __name__ == "__main__":
    main()