import tkinter as tk
from PIL import ImageTk, Image # use of image, "Pillow"
import os

class WarningDisplay(tk.Frame):
    def __init__(self):
        super(WarningDisplay, self).__init__()
        self.state = False


    def logger_init(self, logger_obj):
        self.logger = logger_obj
        


    def visual_warning_init(self, warning_icon_path):

        self.warning_icon = ImageTk.PhotoImage(Image.open(os.path.expanduser(warning_icon_path))) # load the image with the icon in file system

        # initialization of the warning icon
        self.warning_display = tk.Label(image = self.warning_icon, borderwidth=0, background="black") # use as the icon of the warning
        self.warning_display.pack(fill="both", expand=1) # display the warning
        self.warning_display.pack_forget() # hide the warning


    def start_visual_warning(self):
        self.warning_display.pack(fill="both", expand=1) # display the warning icon
        self.state = True


    def stop_visual_warning(self):
        self.warning_display.pack_forget() # stop displaying the warning
        self.state = False


    def key_pressed(self, event):
        if self.state == False:
            self.start_visual_warning()
        else:
            self.stop_visual_warning()

    

class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.title("Warning Display System") # set the title of the frame
        self.geometry("720x480") # set the size of the frame
        self.configure(bg="black")
        self.warnings = []

    def create_warning(self, icon):
        warning = WarningDisplay()
        warning.visual_warning_init(icon)
        self.warnings.append(warning)

    

if __name__ == "__main__":

    main = MainApplication()

    main.create_warning("icon.png")
    main.create_warning("icon_2.png")

    main.bind("<s>", main.warnings[0].key_pressed)
    main.bind("<d>", main.warnings[1].key_pressed)

    main.mainloop()
