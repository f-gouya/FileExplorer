from ttkbootstrap import Frame, Menubutton, Menu, Treeview, Scrollbar, PanedWindow, Label, Button, Entry
from ttkbootstrap.dialogs import Messagebox, Querybox
from pathlib import Path
import pyzipper
import psutil
import time


class Home(Frame):
    def __init__(self, window, view):
        super().__init__(window)

        self.main_view = view

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.menu_bar = Frame(self)
        self.menu_bar.grid(row=0, column=0, pady=(1, 0), sticky="ew")

        self.menu_bar.grid_columnconfigure(8, weight=1)

        self.theme_button = Menubutton(self.menu_bar, text="Themes")
        self.theme_button.grid(row=0, column=0)

        self.theme_menu = Menu(self.theme_button, tearoff=0)
        self.theme_button["menu"] = self.theme_menu

        themes = ["flatly", "darkly", "cosmo"]
        for theme in themes:
            self.theme_menu.add_command(label=theme.capitalize(),
                                        command=lambda select=theme: self.change_theme(select))

        self.create_folder_button = Button(self.menu_bar, text="Create", width=11, command=self.create_item)
        self.create_folder_button.grid(row=0, column=1, padx=(1, 0))

        self.rename_items_button = Button(self.menu_bar, text="Rename", width=11, command=self.rename_item)
        self.rename_items_button.grid(row=0, column=3, padx=(1, 0))

        self.delete_items_button = Button(self.menu_bar, text="Delete", width=11, command=self.delete_item)
        self.delete_items_button.grid(row=0, column=4, padx=(1, 0))

        self.zip_button = Button(self.menu_bar, text="Zip", width=11, command=self.zip_files)
        self.zip_button.grid(row=0, column=5, padx=(1, 0))

        self.extract_button = Button(self.menu_bar, text="Extract", width=11, command=self.extract_zip)
        self.extract_button.grid(row=0, column=6, padx=(1, 0))

        self.search_label = Label(self.menu_bar, text="Search")
        self.search_label.grid(row=0, column=7, padx=(20, 0))

        self.search_entry = Entry(self.menu_bar)
        self.search_entry.grid(row=0, column=8, padx=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.search)

        # Create a PanedWindow for the file explorer
        self.paned_window = PanedWindow(self, orient='horizontal')
        self.paned_window.grid(row=1, column=0, pady=1, sticky="nsew")

        # Left pane for folder hierarchy
        self.left_pane = Frame(self.paned_window)
        self.paned_window.add(self.left_pane, weight=1)

        self.left_pane.grid_columnconfigure(0, weight=1)
        self.left_pane.grid_rowconfigure(0, weight=1)

        self.folder_tree = Treeview(self.left_pane)
        self.folder_tree.grid(row=0, column=0, sticky="nsew")

        self.folder_scrollbar = Scrollbar(self.left_pane, orient='vertical', command=self.folder_tree.yview)
        self.folder_scrollbar.grid(row=0, column=1, sticky="ns")
        self.folder_tree.config(yscrollcommand=self.folder_scrollbar.set)

        # Right pane for files and folders
        self.right_pane = Frame(self.paned_window)
        self.paned_window.add(self.right_pane, weight=20)

        self.right_pane.grid_columnconfigure(0, weight=1)
        self.right_pane.grid_rowconfigure(0, weight=1)

        self.file_tree = Treeview(self.right_pane, columns=("Name", "Date Modified", "Date Created", "Type", "Size"),
                                  show="headings", selectmode='extended')
        self.file_tree.grid(row=0, column=0, sticky="nsew")

        self.file_tree.heading("Name", text="Name", anchor="w")
        self.file_tree.heading("Date Modified", text="Date Modified", anchor="w")
        self.file_tree.heading("Date Created", text="Date Created", anchor="w")
        self.file_tree.heading("Type", text="Type", anchor="w")
        self.file_tree.heading("Size", text="Size", anchor="w")

        self.file_tree.column("Name", width=200)
        self.file_tree.column("Date Modified", width=150)
        self.file_tree.column("Date Created", width=150)
        self.file_tree.column("Type", width=100)
        self.file_tree.column("Size", width=100)

        self.file_scrollbar = Scrollbar(self.right_pane, orient='vertical', command=self.file_tree.yview)
        self.file_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_tree.config(yscrollcommand=self.file_scrollbar.set)

        # Create a status bar
        self.status_bar = Frame(self)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        self.status_label = Label(self.status_bar, text="Status: Ready")
        self.status_label.grid(row=0, column=0, padx=10, pady=5)

        # Populate the folder tree
        self.populate_folders()

        # Bind the folder tree selection event
        self.folder_tree.bind("<<TreeviewOpen>>", self.on_folder_expand)
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_select)
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_selection_change)
        self.file_tree.bind("<<TreeviewSelect>>", self.update_status_bar)

    def change_theme(self, theme_name):
        self.main_view.window.set_theme(theme_name)

    def populate_folders(self):
        # Create "This PC" node
        this_pc_node = self.folder_tree.insert("", "end", text="This PC", open=True)

        # Get all drives
        drives = [disk.device for disk in psutil.disk_partitions()]

        # Populate the folder tree with drives
        for drive in drives:
            drive_node = self.folder_tree.insert(this_pc_node, "end", iid=str(Path(drive)), text=drive, open=False)
            # Call `insert_subfolders` to add only subfolders
            self.insert_subfolders(drive_node, Path(drive))

    def insert_subfolders(self, parent, path):
        try:
            for folder in path.iterdir():
                if folder.is_dir():
                    # Use the full path as the iid
                    node = self.folder_tree.insert(parent, "end", iid=str(folder), text=folder.name, open=False)
                    self.folder_tree.insert(node, "end")  # Allows expansion
        except (PermissionError, FileNotFoundError):
            pass

    def on_folder_expand(self, _):
        # Get the selected folder
        selected_item = self.folder_tree.selection()[0]
        folder_path = self.get_full_path(selected_item)

        # Clear the dummy child first
        self.folder_tree.delete(*self.folder_tree.get_children(selected_item))

        # Check if the selected item is valid path and not "This PC"
        if selected_item and folder_path and folder_path.is_dir():
            # Populate the folder tree with subfolders
            self.insert_subfolders(selected_item, folder_path)

    def on_folder_select(self, _):
        # Get the selected folder
        selected_item = self.folder_tree.selection()[0]
        folder_path = self.get_full_path(selected_item)

        # Clear the file tree
        self.file_tree.delete(*self.file_tree.get_children())

        # Populate the file tree with files and folders in the selected folder
        try:
            for item in Path(folder_path).iterdir():
                item_type = "Folder" if item.is_dir() else item.suffix
                item_size = self.format_size(item.stat().st_size) if item.is_file() else ""
                date_modified = time.strftime("%d/%m/%Y %I:%M %p", time.localtime(item.stat().st_mtime))
                date_created = time.strftime("%d/%m/%Y %I:%M %p", time.localtime(item.stat().st_ctime))
                self.file_tree.insert("", "end", iid=str(item),
                                      values=(item.name, date_modified, date_created, item_type, item_size))
        except PermissionError:
            Messagebox.show_error("You do not have permission to access this folder.", "Permission Error")
        except FileNotFoundError:
            Messagebox.show_error("The specified folder was not found.", "File Not Found")

        # Update the status bar
        self.update_status_bar()

    def update_status_bar(self, _=None):
        # Get all items in the file tree
        all_items = self.file_tree.get_children()
        total_items = len(all_items)

        # Get selected items
        selected_items = self.file_tree.selection()
        selected_count = len(selected_items)

        # Calculate total size if only files are selected
        total_size = 0
        all_files = True
        for item in selected_items:
            item_values = self.file_tree.item(item, "values")
            item_path = Path(self.get_full_path(self.folder_tree.selection()[0])) / item_values[0]
            if item_path.is_file():
                total_size += item_path.stat().st_size
            else:
                all_files = False

        # Format total size
        size_str = self.format_size(total_size)

        # Update status label
        if selected_count == 0:
            status_text = f"{total_items} items"
        elif all_files:
            status_text = f"{total_items} items | {selected_count} items selected ({size_str})"
        else:
            status_text = f"{total_items} items | {selected_count} items selected"

        self.status_label.config(text=status_text)

    @staticmethod
    def format_size(size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 ** 3:
            return f"{size / 1024 ** 2:.2f} MB"
        else:
            return f"{size / 1024 ** 3:.2f} GB"

    def get_full_path(self, item):
        path = []
        while item:
            path.insert(0, self.folder_tree.item(item, "text"))
            item = self.folder_tree.parent(item)
        return Path("C:\\").joinpath(*path)

    def create_item(self):
        # Get selected folder from the left pane
        selected_item = self.folder_tree.selection()
        if not selected_item:
            Messagebox.show_error("Please select a valid folder in the left pane.", "Selection Error")
            return

        folder_path = self.get_full_path(selected_item[0])

        # Prompt user for the name of the file or directory
        name = Querybox.get_string("Enter the name for the new file or directory:", "Create Item")

        # Check if the user entered a name
        if not name:
            Messagebox.show_error("You must enter a name.", "Input Error")
            return

            # Determine if it's a file or directory
        item_path = Path(folder_path) / name
        try:
            if "." in name:  # Check for file extension
                item_path.touch()  # Create a new file
            else:
                item_path.mkdir()  # Create a new directory
        except FileExistsError:
            Messagebox.show_error("The item already exists.", "Creation Error")
        except PermissionError:
            Messagebox.show_error("You do not have permission to create this item.", "Permission Error")
        except Exception as e:
            Messagebox.show_error(f"An error occurred: {str(e)}", "Error")

            # Refresh the right pane to show the new item
        self.on_folder_select(None)

    def rename_item(self):
        # Get selected items from the right pane
        selected_items = self.file_tree.selection()
        if not selected_items:
            Messagebox.show_error("Please select at least one file or directory to rename.", "Selection Error")
            return

            # Prompt user for the new name
        new_name = Querybox.get_string("Enter the new name for the selected items:", "Rename Item")

        # Check if the user entered a name
        if not new_name:
            Messagebox.show_error("You must enter a new name.", "Input Error")
            return

            # Rename each selected item
        for index, item in enumerate(selected_items):
            item_values = self.file_tree.item(item, "values")
            item_path = Path(self.get_full_path(self.folder_tree.selection()[0])) / item_values[0]

            # Determine the new name with a number if multiple items are selected
            if len(selected_items) > 1:
                new_item_name = f"{new_name} ({index + 1})"
            else:
                new_item_name = new_name

            new_item_path = item_path.parent / new_item_name

            try:
                item_path.rename(new_item_path)  # Rename the item
            except FileExistsError:
                Messagebox.show_error(f"The item '{new_item_name}' already exists.", "Rename Error")
            except PermissionError:
                Messagebox.show_error(f"You do not have permission to rename '{item_values[0]}'.", "Permission Error")
            except Exception as e:
                Messagebox.show_error(f"An error occurred while renaming '{item_values[0]}': {str(e)}", "Error")

                # Refresh the right pane to show the renamed items
        self.on_folder_select(None)

    def delete_item(self):
        # Get selected items from the right pane
        selected_items = self.file_tree.selection()
        if not selected_items:
            Messagebox.show_error("Please select at least one file or directory to delete.", "Selection Error")
            return

            # Confirmation dialog
        confirm = Messagebox.yesno("Are you sure you want to delete the selected items?", "Confirm Deletion")
        if not confirm:
            return  # User chose not to delete

        # Delete each selected item
        for item in selected_items:
            item_values = self.file_tree.item(item, "values")
            item_path = Path(self.get_full_path(self.folder_tree.selection()[0])) / item_values[0]

            try:
                if item_path.is_dir():
                    item_path.rmdir()  # Remove directory (must be empty)
                else:
                    item_path.unlink()  # Remove file
            except FileNotFoundError:
                Messagebox.show_error(f"The item '{item_values[0]}' does not exist.", "Deletion Error")
            except PermissionError:
                Messagebox.show_error(f"You do not have permission to delete '{item_values[0]}'.", "Permission Error")
            except OSError as e:
                Messagebox.show_error(f"An error occurred while deleting '{item_values[0]}': {str(e)}", "Error")
            except Exception as e:
                Messagebox.show_error(f"An unexpected error occurred: {str(e)}", "Error")

                # Refresh the right pane to show the updated items
        self.on_folder_select(None)

    def on_folder_selection_change(self, _):
        # Clear search entry when selecting a new folder
        self.search_entry.delete(0, 'end')  # Clear the search entry
        self.on_folder_select(None)  # Show files in the newly selected folder

    def search(self, _):
        search_term = self.search_entry.get().strip()  # Get the search term and strip whitespace

        # Get selected folder from the left pane
        selected_item = self.folder_tree.selection()
        if not selected_item:
            self.clear_search_results()  # Clear results if no folder is selected
            return

        folder_path = self.get_full_path(selected_item[0])
        self.display_search_results(folder_path, search_term)

    def display_search_results(self, folder_path, search_term):
        # Clear previous results
        self.clear_search_results()

        # Convert folder_path to a Path object
        folder_path = Path(folder_path)

        if not search_term:  # If no search term, show all items
            self.on_folder_select(None)
            return

            # Determine if searching by extension or name
        search_by_extension = search_term.startswith("*")
        if search_by_extension:
            ext = search_term[1:].lower()  # Get the extension without the asterisk
        else:
            ext = None

            # Search through the directory and its subdirectories
        for item in folder_path.rglob('*'):
            name = item.name
            name_lower = name.lower()

            if search_by_extension:
                # If searching for a specific extension
                if name_lower.endswith(ext):
                    self.add_file_to_tree(item)
            else:
                # If searching by name only
                if search_term.lower() in name_lower:
                    self.add_file_to_tree(item)

    def add_file_to_tree(self, item):
        # Get file details
        modified_time = time.strftime("%d/%m/%Y %I:%M %p", time.localtime(item.stat().st_mtime))
        created_time = time.strftime("%d/%m/%Y %I:%M %p", time.localtime(item.stat().st_ctime))
        size = self.format_size(item.stat().st_size)
        file_type = item.suffix if item.is_file() else "Directory"

        # Insert file details into the tree
        self.file_tree.insert('', 'end', text=item.name,
                              values=(str(item), file_type, modified_time, created_time, size))

    def clear_search_results(self):
        # Clear the right pane or reset it to show the original structure
        self.file_tree.delete(*self.file_tree.get_children())  # Clear all items in the file tree

    def zip_files(self):
        # Get selected items from the tree view
        selected_items = [item for item in self.file_tree.selection()]

        if not selected_items:
            Messagebox.show_warning("Please select files or directories to zip.", "No Selection")
            return

        # Get the full path of the first selected item's parent directory
        parent_directory = Path(self.file_tree.selection()[0]).parent

        # Ask for the zip file name
        zip_name = Querybox.get_string("Enter a name for the zip file (without extension):", "Zip File Name")
        if not zip_name:
            return  # Cancel if no name is provided

        # Ask for the password (optional)
        password = Querybox.get_string("Enter a password for the zip file (leave empty for no password):", "Password")

        try:
            # Create the zip file in the same directory where the selected items are located
            zip_file_path = parent_directory / f"{zip_name}.zip"

            if password:
                with pyzipper.AESZipFile(zip_file_path, 'w', compression=pyzipper.ZIP_DEFLATED,
                                         encryption=pyzipper.WZ_AES) as zf:
                    zf.setpassword(password.encode('utf-8'))  # Set password if provided
                    for item in selected_items:
                        item_path = Path(item)
                        if item_path.is_dir():
                            for file_path in item_path.rglob('*'):
                                if file_path.is_file():
                                    zf.write(file_path, arcname=file_path.relative_to(parent_directory))
                        else:
                            zf.write(item_path, arcname=item_path.name)  # Write the files to the zip
            else:
                with pyzipper.AESZipFile(zip_file_path, 'w', compression=pyzipper.ZIP_DEFLATED) as zf:
                    for item in selected_items:
                        item_path = Path(item)
                        if item_path.is_dir():
                            for file_path in item_path.rglob('*'):
                                if file_path.is_file():
                                    zf.write(file_path, arcname=file_path.relative_to(parent_directory))
                        else:
                            zf.write(item_path, arcname=item_path.name)  # Write the files to the zip

            Messagebox.show_info(f"Files successfully zipped to {zip_file_path.name}", "Success")

        except Exception as e:
            Messagebox.show_error(f"An error occurred while creating the zip file: {str(e)}", "Error")

        # Refresh the right pane to show the updated items
        self.on_folder_select(None)

    def extract_zip(self):
        # Get selected zip file from the tree view
        selected_item = self.file_tree.selection()
        if not selected_item or not selected_item[0].endswith('.zip'):
            Messagebox.show_warning("Please select a zip file to extract.", "No Selection")
            return

        zip_file_path = selected_item[0]

        # Get the parent directory of the zip file
        parent_directory = Path(self.file_tree.selection()[0]).parent

        # Ask for the extraction directory name
        extract_dir_name = Querybox.get_string("Enter a name for the extraction folder:", "Extract Directory Name")
        if not extract_dir_name:
            return  # Cancel if no name is provided

        try:
            # Create the extraction directory within the parent directory
            extract_path = parent_directory / extract_dir_name
            extract_path.mkdir(exist_ok=True)  # Create directory

            with pyzipper.AESZipFile(zip_file_path) as zf:
                # Check if the zip file is encrypted
                if zf.is_encrypted:
                    password = Querybox.get_string("Enter the zip file password (if encrypted):", "Zip Password")
                    zf.extractall(path=extract_path, pwd=password.encode('utf-8'))  # Extract with the password
                else:
                    zf.extractall(path=extract_path)  # Extract without a password
            # with zipfile.ZipFile(zip_file_path, mode="r") as zf:
            #     # Check if the zip file is encrypted
            #     if zf.pwd:
            #         password = Querybox.get_string("Enter the zip file password (if encrypted):", "Zip Password")
            #         zf.extractall(path=extract_path, pwd=password.encode('utf-8'))  # Extract with the password
            #     else:
            #         zf.extractall(path=extract_path)  # Extract without a password

            Messagebox.show_info(f"Files successfully extracted to {extract_path}", "Success")

        except Exception as e:
            Messagebox.show_error(f"An error occurred while extracting the zip file: {str(e)}", "Error")

        # Refresh the right pane to show the updated items
        self.on_folder_select(None)
