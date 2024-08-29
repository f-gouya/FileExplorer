from ttkbootstrap import Frame, Menubutton, Menu


class Home(Frame):
    def __init__(self, window, view):
        super().__init__(window)

        self.main_view = view

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.menu_button = Menubutton(self, text="Themes")
        self.menu_button.grid(row=0, column=0)

        self.menu = Menu(self.menu_button, tearoff=0)
        self.menu_button["menu"] = self.menu

        themes = ["flatly", "darkly", "cosmo"]
        for theme in themes:
            self.menu.add_command(label=theme.capitalize(), command=lambda select=theme: self.change_theme(select))

    def change_theme(self, theme_name):
        self.main_view.window.set_theme(theme_name)
