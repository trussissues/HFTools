# the data input interfaces

# external libraries
import socket # socket for UDP and TCP
import time


class Conn():
    """
    the connection class to create either TCP or UDP connection with external applications
    """

    def __init__(self, conn_type, conn_ip, conn_port, conn_buffer):

        self.conn_type = str(conn_type) # the type of the connection
        self.conn_ip = str(conn_ip) # the ip address of the connection
        self.conn_port = int(conn_port) # the port of the connection
        self.conn_buffer = int(conn_buffer) # the buffer of connection


    def conn_sock(self):

        # set the socket to the type of the connection
        if self.conn_type == "TCP":
            self.conn_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

        elif self.conn_type == "UDP":
            self.conn_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        else:
            print("Protocal not supported.")


        
    def conn_connect(self):

        # establish the connection
        self.conn_socket.bind((self.conn_ip, self.conn_port))


    def conn_recv(self):

        received_data = self.conn_sock.recvfrom(self.conn_buffer) # receive the information from ther connection
        
        if not received_data: # if the connection is not established
            return "Connection interrupted"
        else:
            return received_data


    def conn_recv_with_time(self):

        received_data = self.conn_socket.recvfrom(self.conn_buffer) # receive the information from ther connection
        time_received = time.time() # get the time when the UDP data is received

        if not received_data: # if the connection is not established
            return "Connection interrupted"
        else:
            return (received_data, time_received)