# integrated warning display system with UDP listner, time-based approach

# internal libraries used
from input import * # data stream

# external libraries used
import tkinter as tk
from PIL import ImageTk, Image # use of image, "Pillow"
import pygame # warning sound
import os # filepath
import time # UNIX time



class WarningDisplay(tk.Frame):

    def __init__(self, warning_type, conn_obj):
        super(WarningDisplay, self).__init__()
        self.warning_type = warning_type
        self.conn = conn_obj

    
    def logger_init(self, logger_obj):
        self.logger = logger_obj
        

    def sound_warning_init(self, warning_sound_path):

        pygame.mixer.init() # initialize the mixer module from pygame
        pygame.mixer.music.load(os.path.expanduser(warning_sound_path))

    
    def start_sound_warning(self):
        pygame.mixer.music.play() # start to play the warning sound

    
    def stop_sound_warning(self):
        pygame.mixer.music.stop() # stop playing the warning sound
    

    def visual_warning_init(self, warning_icon_path):

        self.warning_icon = ImageTk.PhotoImage(Image.open(os.path.expanduser(warning_icon_path))) # load the image with the icon in file system

        # initialization of the warning icon
        self.warning_display = tk.Label(image = self.warning_icon, borderwidth=0, background="black") # use as the icon of the warning
        self.warning_display.pack(fill="both", expand=1) # display the warning
        self.warning_display.pack_forget() # hide the warning


    def start_visual_warning(self):
        self.warning_display.pack(fill="both", expand=1) # display the warning icon


    def stop_visual_warning(self):
        self.warning_display.pack_forget() # stop displaying the warning
   
   
    def param_init(self, glance, warning):

        # variable initialization
        self.current_state = False # a flag to mark the current state of the system, True = warning triggered
        self.warning_detection = False # a flag to mark if the warning detection has started, True = started
        self.glance_detection = False # a flag to mark if the glance detection has started, True = started
        self.warning_detection_start_time = time.time() # warning detection period start time
        self.glance_detection_strart_time = time.time() # glance detection period start time

        # period definition
        self.glance_period = glance # set the glance interval
        self.warning_period = warning # set time interval for warning

    
    def warning_init(self, filename, glance, warning, logger_obj): # initialize the warning depending on the type
        if self.warning_type == "Visual":

            self.visual_warning_init(os.path.expanduser(os.getcwd() + "/" + filename)) # initialize visual warning
            self.param_init(glance, warning) # initialize parameters
            self.logger_init(logger_obj) # initialize the logger

        elif self.warning_type == "Auditory":

            self.sound_warning_init(os.path.expanduser(os.getcwd() + "/" + filename)) # initialize visual warning
            self.param_init(glance, warning) # initialize parameters
            self.logger_init(logger_obj) # initialize the logger

    def start_warning(self): # general warning method depending on the type
        if self.warning_type == "Visual":
            self.start_visual_warning()

        elif self.warning_type == "Auditory":
            self.start_sound_warning()

    def stop_warning(self): # general warning method depending on the type
        if self.warning_type == "Visual":
            self.stop_visual_warning()

        elif self.warning_type == "Auditory":
            self.stop_sound_warning()



    def warning(self, data, time_received):

        self.logger.log_data_received(data, time_received)


        if self.current_state == False and self.warning_detection == False and self.glance_detection == False:

            if data == "false": # if the data is outside AOI

                self.warning_detection = True # start the warning detection
                self.warning_detection_start_time = time.time() # set the start of the warning detection period

                self.logger.log_info("warning detection started", self.warning_type)

        elif self.current_state == False and self.warning_detection == True and self.glance_detection == False:

            if time_received - self.warning_detection_start_time < self.warning_period: # if the warning period has not exceeded the minimum trigger time

                if data == "true": # if the data is inside AOI

                    self.glance_detection = True # start the glance detection
                    self.glance_detection_strart_time = time.time() # set the start of the glance detection period

                    self.logger.log_info("glance detection started", self.warning_type)

            if time_received - self.warning_detection_start_time >= self.warning_period: # if the warning period has exceeded the minimum trigger time

                self.current_state = True
                self.warning_detection = False # end the warning detection

                self.start_warning()

                self.logger.log_info("warning triggered", self.warning_type)

        elif self.current_state == False and self.warning_detection == True and self.glance_detection == True:

            if time_received - self.glance_detection_strart_time < self.glance_period: # if it is not a glance

                if data == "false":

                    self.glance_detection = False # end the glance detection

                    self.logger.log_info("glance detection ended", self.warning_type)

            else:

                self.warning_detection = False # end the warning detection
                self.glance_detection = False # end the glance detection

                self.logger.log_info("warning detection and glance detection ended", self.warning_type)

        elif self.current_state == True and self.warning_detection == False and self.glance_detection == False:

            if data == "true": # if the data is inside AOI        
                
                self.glance_detection = True # start the glance detection
                self.glance_detection_strart_time = time.time() # set the start of the glance detection period

                self.logger.log_info("glance detection started", self.warning_type)


        elif self.current_state == True and self.warning_detection == False and self.glance_detection == True:

            if time_received - self.glance_detection_strart_time < self.glance_period: # if it is not a glance

                if data == "false":

                    self.glance_detection = False # end the glance detection

                    self.logger.log_info("glance detection ended", self.warning_type)

            else:

                self.current_state = False
                self.glance_detection = False # end the glance detection

                self.stop_warning()

                self.logger.log_info("warning disabled", self.warning_type)

        else:
            self.logger.log_info("exception", self.warning_type)