from ttkbootstrap import Window


class Windows(Window):
    def __init__(self):
        super().__init__(themename="flatly")

        # self.geometry("800x500")
        self.title("Task Manager Application")
        # self.resizable(False, False)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def show_form(self):
        self.mainloop()
