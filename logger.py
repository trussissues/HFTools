from datetime import datetime
import time

class Logger():
    
    def __init__(self):
        pass

    
    def create_timestamp(self):
        
        # set up the timestamp for the file
        time_year = datetime.now().strftime("%Y")
        time_month = datetime.now().strftime("%m")
        time_day = datetime.now().strftime("%d")
        time_hour = datetime.now().strftime("%H")
        time_minute = datetime.now().strftime("%M")
        time_second = datetime.now().strftime("%S")
        self.timestamp = f"{time_year}{time_month}{time_day} {time_hour}_{time_minute}_{time_second}"

    
    def log_data_received(self, data, time_received):
        unix_timestamp = ("%.3f" % round(time_received, 3)).replace(".", "")
        local_time = datetime.fromtimestamp(time.mktime(time.localtime(time_received)))
        
        # open the file with the current study timestamp
        with open(f"{self.timestamp}_log.txt", "a+") as log_file:
            log_file.write(f"{data} data received, {unix_timestamp}, {local_time}\n")



    def log_info(self, info, warning_type):

        self.warning_type = warning_type

        unix_time = time.time()
        local_time = datetime.fromtimestamp(time.mktime(time.localtime(unix_time)))
        unix_timestamp = ("%.3f" % round(unix_time, 3)).replace(".", "")

        # open the file with the current study timestamp
        with open(f"{self.timestamp}_log.txt", "a+") as log_file:
           
            log_file.write(f"{self.warning_type}, {info}, {unix_timestamp}, {local_time}\n")
