import sys
import socket
import threading
import urllib.request

class ChatterServer:

    MAX_SCREEN_NAME_LENGTH = 50
    MAX_MESSAGE_LENGTH = 50

    ###################################
    ###Constructor for ChatterServer###
    ###################################
    def __init__(self, Ip, Port):

        #Variables of the server
        self.__exit_server = False
        self.__connection_established = False
        self.__debug_mode = True

        #Parsing input arguments
        if Ip == "localhost":
            self.server_ip = "127.0.0.1"
        else:
            self.server_ip = Ip
        try:
            self.server_port = int(Port)
        except ValueError:
            print("Invalid Port provided")
            exit()

        #Membership list
        #Contains tuples with the structure (Name, Ip, Port)
        self.chatter_list = []

        #Create UDP Port To Send to client UDP
        self.server_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_udp_socket.settimeout(3)
        try:
            self.server_udp_socket.bind(("127.0.0.1", 0))                               #Python asigns an empty port
        except socket.error:
            self.__print_to_chat_console_log("Unable to bind to UDP socket")
            exit()
        self.client_port = self.server_udp_socket.getsockname()[1]                      #Store the port assigned

        #Create TCP Port To Server
        self.server_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_tcp_socket.bind((self.server_ip, self.server_port))

    ###########################################################
    ##Private functions to communicate to TCP and UDP sockets##
    ###########################################################
    def __send_string_to_tcp(self, Input_string, Socket=None):
        if Socket is None:
            Socket = self.server_tcp_socket

        if self.__debug_mode:
            self.__print_to_chat_console_log("TCP Send: " + repr(Input_string))
        Socket.send(Input_string.encode())

    def __get_string_from_tcp(self, Socket=None):
        if Socket is None:
            Socket = self.server_tcp_socket

        server_character_response = ""
        server_response = ""
        while server_character_response != '\n':
            server_character_response = Socket.recv(1).decode()
            server_response += server_character_response
        if self.__debug_mode:
            self.__print_to_chat_console_log("TCP Received: " + repr(server_response))
        return server_response

    def __get_string_from_udp(self):
        try:
            udp_character_response, server = self.client_socket.recvfrom(2048)
            if self.__debug_mode:
                self.__print_to_chat_console_log("UDP Received: " + repr(udp_character_response.decode()))
            return udp_character_response.decode()
        except socket.timeout:
            return None
        
    def __send_string_to_udp(self, Input_string, Ip, Port):
        if self.__debug_mode:
            self.__print_to_chat_console_log("UDP Send: " + repr(Input_string))
        bytes_sent = self.server_udp_socket.sendto(Input_string.encode(), (Ip, int(Port)))

    #########################
    ##Thread for TCP socket##
    #########################
    def __server_main_tcp_thread_func(self):
        self.server_tcp_socket.listen(5)
        thread_number = 0
        while True:
            (client_socket, address) = self.server_tcp_socket.accept()
            client_thread = threading.Thread(target=self.__server_client_tcp_thread_func, args=(thread_number,client_socket))
            client_thread.daemon = True
            client_thread.start()
            thread_number += 1
        
    def __server_client_tcp_thread_func(self, Thread_number, Client_socket):
        while True:
            client_string = self.__get_string_from_tcp(Client_socket)[:-1]
            if self.__is_hello_valid(client_string, Client_socket):
                chatter_name = self.__parse_service_hello(client_string, Client_socket)
                print(chatter_name + " says hello")
            elif client_string == "EXIT":
                print(chatter_name + " wants to exit")
                for chatter in self.chatter_list:
                    if chatter[0] == chatter_name:
                        #Mutex lock this?
                        self.__send_exit_to_all_chatters(chatter_name)
                        self.chatter_list.remove(chatter)
                        break
                
    ###############################
    ##Parsing TCP inbound packets##
    ###############################
    def __is_hello_valid(self, Hello_string, Client_socket):
        hello_string_list = Hello_string.split(' ')
        #Correct number of arguments and HELO start
        if hello_string_list[0] != "HELO" or len(hello_string_list) != 4:
            return False
        #Check if username is taken
        for chatter in self.chatter_list:
            if chatter[0] == hello_string_list[1]:
                self.__send_string_to_tcp("RJCT " + hello_string_list[1] + "\n", Client_socket)
                return False
        
        return True

    def __parse_service_hello(self, Hello_string, Client_socket):
        hello_string_list = Hello_string.split(' ')
        #Add to member list
        self.chatter_list.append((hello_string_list[1], hello_string_list[2], hello_string_list[3]))
        #Send Acceptance message
        self.__send_accept_to_new_chatter(Client_socket)

        #Send Join to all chatters
        self.__send_join_to_all_chatters(hello_string_list[1], hello_string_list[2], hello_string_list[3])
    
        return hello_string_list[1]

    def __send_accept_to_new_chatter(self, Client_socket):
        accept_string = "ACPT "
        for chatter in self.chatter_list:
            accept_string = accept_string + chatter[0] + " " + chatter[1] + " " + chatter[2] + ":"
        accept_string = accept_string[:-1] + "\n"
        self.__send_string_to_tcp(accept_string, Client_socket)

    def __send_join_to_all_chatters(self, Name, Ip, Port):
        join_string = "JOIN " + Name + " " + Ip + " " + Port + "\n"

        for chatter in self.chatter_list:
            self.__send_string_to_udp(join_string, chatter[1], chatter[2])
        
    def __send_exit_to_all_chatters(self, Name):
        exit_string = "EXIT " + Name + "\n"

        for chatter in self.chatter_list:
            self.__send_string_to_udp(exit_string, chatter[1], chatter[2])

    def __parse_service_exit(self, Chatter_name):
        pass

    #####################################################################################
    ##Start function for client. Must be run after initial connection to server is made##
    #####################################################################################
    def run(self):
        #Declare threads
        self.tcp_input_thread = threading.Thread(target=self.__server_main_tcp_thread_func)
        self.tcp_input_thread.daemon = True
        #Starts threads
        self.tcp_input_thread.start()

        #Waits for threads to finish (shouldn't happen)
        self.tcp_input_thread.join()

def main():
    #print("Number of arguments:", len(sys.argv), "arguments.")
    #print("Argument List:", str(sys.argv))
    #print("Hello World")

    # external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    # print(external_ip)

    if len(sys.argv) != 3:
        print("Incorrect number of arguments for calling YaChatClient.py")
        exit()

    client = ChatterServer(sys.argv[1], sys.argv[2])
    try:
        client.run()
    except: 
        exit()

main()