# internal libraries used
from matplotlib.pyplot import fill
from warning_display import *
from logger import * # info logging

# external libraries used
import tkinter as tk

# the main file of the program

class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.title("Warning Display System") # set the title of the frame
        self.geometry("720x480") # set the size of the frame
        self.configure(bg="black")


    def create_logger(self):

        self.logger_obj = Logger()
        self.logger_obj.create_timestamp()


    def create_conn(self):

        self.conn_object = Conn("UDP", "localhost", 20001, 1024)
        self.conn_object.conn_sock()
        self.conn_object.conn_connect()


    def create_visual_warning(self):

        self.visual_warning = WarningDisplay("Visual", self.conn_object)
        self.visual_warning.warning_init("icon.png", 0.160, 2.500)

    
    def refresh_visual_warning(self):
        self.visual_warning.warning()
        self.after(25, self.refresh_visual_warning)

    
    def create_auditory_warning(self):

        self.auditory_warning = WarningDisplay("Auditory", self.conn_object)
        self.auditory_warning.warning_init("warning.mp3", 0.160, 2.500)
    

    def refresh_auditory_warning(self):
        self.auditory_warning.warning()
        self.after(25, self.refresh_auditory_warning)

    
    def create_both_warning(self):

        self.visual_warning = WarningDisplay("Visual", self.conn_object)
        self.visual_warning.warning_init("icon.png", 0.160, 3.000, self.logger_obj)
        self.auditory_warning = WarningDisplay("Auditory", self.conn_object)
        self.auditory_warning.warning_init("warning.mp3", 0.160, 3.500, self.logger_obj)


    def refresh_both_warning(self):

        # establish the data stream
        data_stream = self.conn_object.conn_recv_with_time()

        # get the boolean data
        data = data_stream[0][0].decode("utf-8")[-6:-1].strip() # extract the data from the received UDP data
        # get the data receive time
        time_received = data_stream[1] # time when the data is received
        
        self.visual_warning.warning(data, time_received)
        self.auditory_warning.warning(data, time_received)
        self.after(5, self.refresh_both_warning)



if __name__ == "__main__":

    main = MainApplication()

    main.create_conn()
    main.create_logger()

    main.create_both_warning()

    main.after(5, main.refresh_both_warning)

    main.mainloop()