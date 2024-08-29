from PresentationLayer.windows import Windows
from PresentationLayer.home import Home


class MainView:
    def __init__(self):
        self.window = Windows()

        self.home_frame = Home(self.window, self)
        self.home_frame.grid(row=0, column=0, sticky="nsew")

        self.window.show_form()
