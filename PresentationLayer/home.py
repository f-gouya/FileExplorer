from ttkbootstrap import Frame, Menubutton, Menu, Treeview, Scrollbar, PanedWindow, Label, Button
from pathlib import Path
import time
import psutil


class Home(Frame):
    def __init__(self, window, view):
        super().__init__(window)

        self.main_view = view

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.menu_bar = Frame(self)
        self.menu_bar.grid(row=0, column=0, pady=(1, 0), sticky="ew")

        self.theme_button = Menubutton(self.menu_bar, text="Themes")
        self.theme_button.grid(row=0, column=0)

        self.theme_menu = Menu(self.theme_button, tearoff=0)
        self.theme_button["menu"] = self.theme_menu

        themes = ["flatly", "darkly", "cosmo"]
        for theme in themes:
            self.theme_menu.add_command(label=theme.capitalize(),
                                        command=lambda select=theme: self.change_theme(select))

        self.create_folder_button = Button(self.menu_bar, text="Create", width=10)
        self.create_folder_button.grid(row=0, column=1, padx=(1, 0))

        self.rename_items_button = Button(self.menu_bar, text="Rename", width=10)
        self.rename_items_button.grid(row=0, column=3, padx=(1, 0))

        self.delete_items_button = Button(self.menu_bar, text="Delete", width=10)
        self.delete_items_button.grid(row=0, column=4, padx=(1, 0))

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
            drive_node = self.folder_tree.insert(this_pc_node, "end", text=drive, open=False)
            self.insert_subfolders(drive_node, Path(drive))

    def insert_subfolders(self, parent, path):
        try:
            for folder in path.iterdir():
                if folder.is_dir():
                    node = self.folder_tree.insert(parent, "end", text=folder.name, open=False)
                    # Insert a dummy child to make the node expandable
                    self.folder_tree.insert(node, "end")
        except PermissionError:
            pass

    def on_folder_expand(self, _):
        # Get the selected folder
        selected_item = self.folder_tree.selection()[0]
        folder_path = self.get_full_path(selected_item)

        # Clear the dummy child
        self.folder_tree.delete(*self.folder_tree.get_children(selected_item))

        # Populate the folder tree with subfolders
        self.insert_subfolders(selected_item, Path(folder_path))

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
                self.file_tree.insert("", "end", values=(item.name, date_modified, date_created, item_type, item_size))
        except PermissionError:
            pass

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
