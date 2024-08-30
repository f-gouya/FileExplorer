from ttkbootstrap import Frame, Menubutton, Menu, Treeview, Scrollbar, PanedWindow, Label
from pathlib import Path


class Home(Frame):
    def __init__(self, window, view):
        super().__init__(window)

        self.main_view = view

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.menu_bar = Frame(self)
        self.menu_bar.grid(row=0, column=0, sticky="ew")

        self.theme_button = Menubutton(self.menu_bar, text="Themes")
        self.theme_button.grid(row=0, column=0)

        self.theme_menu = Menu(self.theme_button, tearoff=0)
        self.theme_button["menu"] = self.theme_menu

        themes = ["flatly", "darkly", "cosmo"]
        for theme in themes:
            self.theme_menu.add_command(label=theme.capitalize(),
                                        command=lambda select=theme: self.change_theme(select))

        # Create a PanedWindow for the file explorer
        self.paned_window = PanedWindow(self, orient='horizontal')
        self.paned_window.grid(row=1, column=0, sticky="nsew")

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

        self.file_tree = Treeview(self.right_pane)
        self.file_tree.grid(row=0, column=0, sticky="nsew")

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
        # Populate the folder tree with directories
        root_node = self.folder_tree.insert("", "end", text="C:\\", open=True)
        self.insert_subfolders(root_node, Path("C:\\"))

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
                self.file_tree.insert("", "end", text=item.name)
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
            item_text = self.file_tree.item(item, "text")
            item_path = Path(self.get_full_path(self.folder_tree.selection()[0])) / item_text
            if item_path.is_file():
                total_size += item_path.stat().st_size
            else:
                all_files = False

        # Format total size
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 ** 2:
            size_str = f"{total_size / 1024:.2f} KB"
        elif total_size < 1024 ** 3:
            size_str = f"{total_size / 1024 ** 2:.2f} MB"
        else:
            size_str = f"{total_size / 1024 ** 3:.2f} GB"

        # Update status label
        if selected_count == 0:
            status_text = f"{total_items} items"
        elif all_files:
            status_text = f"{total_items} items | {selected_count} items selected ({size_str})"
        else:
            status_text = f"{total_items} items | {selected_count} items selected"

        self.status_label.config(text=status_text)

    def get_full_path(self, item):
        path = []
        while item:
            path.insert(0, self.folder_tree.item(item, "text"))
            item = self.folder_tree.parent(item)
        return Path("C:\\").joinpath(*path)
