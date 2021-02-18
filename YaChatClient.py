import sys
import socket
import threading
import urllib.request

class ChatterClient:

    MAX_SCREEN_NAME_LENGTH = 50
    MAX_MESSAGE_LENGTH = 50

    ###################################
    ###Constructor for ChatterClient###
    ###################################
    def __init__(self, Name, Ip, Port):

        #Variables of the client
        self.__exit_server = False
        self.__connection_established = False
        self.__debug_mode = False

        self.client_name = Name
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

        #Insert Error Checking Here

        #Create UDP Port To Receive
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(3)
        try:
            self.client_socket.bind(("127.0.0.1", 0))                               #Python asigns an empty port
        except socket.error:
            self.__print_to_chat_console_log("Unable to bind to UDP socket")
            exit()
        self.client_port = self.client_socket.getsockname()[1]                      #Store the port assigned

        #Create TCP Port To Server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.settimeout(3)
        try:
            self.server_socket.connect((self.server_ip, self.server_port))
        except socket.error:
            self.__print_to_chat_console_log("Unable to connect to Server TCP socket")
            exit()

    ###########################################################
    ##Private functions to communicate to TCP and UDP sockets##
    ###########################################################
    def __send_string_to_server(self, Input_string):
        if self.__debug_mode:
            self.__print_to_chat_console_log("TCP Send: " + repr(Input_string))
        self.server_socket.send(Input_string.encode())

    def __get_string_from_server(self):
        server_character_response = ""
        server_response = ""
        while server_character_response != '\n':
            server_character_response = self.server_socket.recv(1).decode()
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
        bytes_sent = self.client_socket.sendto(Input_string.encode(), (Ip, int(Port)))

    #############################################################
    ##Begin and End connect to YaChat Server before client loop##
    #############################################################
    def connect_to_server(self, Count):
        self.__print_to_chat_console_log("Attempted to connect to Server")
        connect_string = "HELO " + self.client_name + " " + self.server_ip + " " + str(self.client_port) + '\n'

        self.__send_string_to_server(connect_string)
        server_response = self.__get_string_from_server()

        if server_response.startswith("RJCT"):
            sys.exit()
        elif server_response.startswith("ACPT"):
            self.__parse_acceptance(server_response[5:-1])
        else:
            #Is there even a possible condition here?
            self.__print_to_chat_console_log("WTF Happened? First response not ACPT or EJCT")
        
        self.__print_to_chat_console_log("Connected to Server and membership list parsed")

    def request_exit_from_server(self):
        self.__print_to_chat_console_log("Requesting to leaving the session")
        self.__send_string_to_server("EXIT\n")

    #########################
    ##Thread for UDP socket##
    #########################
    def __client_udp_thread_func(self):

        while self.__exit_server == False:
            udp_string = self.__get_string_from_udp()
            if udp_string == None:
                continue

            if udp_string.endswith('\n'):
                if udp_string.startswith("MESG"):
                    self.__parse_message(udp_string[5:-1])
                elif udp_string.startswith("JOIN"):
                    self.__parse_join(udp_string[5:-1])
                elif udp_string.startswith("EXIT"):
                    self.__parse_exit(udp_string[5:-1])
                else:
                    print("WTF Happened? Not MESG JOIN or EXIT")
            else:
                print("WTF Happened? Udp string doesn't end in newline")

    ###############################
    ##Parsing UDP inbound packets##
    ###############################
    def __parse_acceptance(self, Accept_string):
        chatter_string_list = Accept_string.split(':')
        for chatter_string in chatter_string_list:
            chatter_string_items = chatter_string.split(' ')
            self.chatter_list.append((chatter_string_items[0], chatter_string_items[1], chatter_string_items[2]))

    def __parse_message(self, Message_string):
        self.__print_to_chat_console(Message_string)
       
    def __parse_join(self, Join_string):
        join_string_list = Join_string.split(' ')
        new_member = True
        for chatter in self.chatter_list:
            if chatter == (join_string_list[0], join_string_list[1], join_string_list[2]):
                new_member = False

        if (join_string_list[0], join_string_list[1], join_string_list[2]) == (self.client_name, "127.0.0.1", str(self.client_port)):
            self.__print_to_chat_console("Join for myself")
            self.__connection_established = True
        elif new_member:
            self.__print_to_chat_console("Join for new member: " + join_string_list[0])
            self.chatter_list.append((join_string_list[0], join_string_list[1], join_string_list[2]))
        else:
            self.__print_to_chat_console("Join for old member: " + join_string_list[0])
            print(self.client_name + ": ", end='', flush=True)
        
    def __parse_exit(self, Exit_string):
        exit_string_name = Exit_string

        if(exit_string_name == self.client_name):
            self.__print_to_chat_console_log("Leaving the session")
            self.client_socket.close()
            self.server_socket.close()
            self.__exit_server = True
            exit()

        for member in self.chatter_list:
            if member[0] == exit_string_name:
                self.__print_to_chat_console("\rRemoved member " + exit_string_name)
                self.chatter_list.remove(member)
                return

        self.__print_to_chat_console_log("WTF Happened? No member to remove")
        return

    ############################
    ##Thread for console Input##
    ############################

    def __client_console_thread_func(self):
        while self.__exit_server == False:
            if self.__connection_established:
                self.__print_client_name_to_chat_console()
                #Make sure special characers don't come through and break the printing on receiver side
                try:
                    console_input_string = repr(input())[1:-1]
                except EOFError:
                    self.request_exit_from_server()
                    break
                if(console_input_string == "exit()"):
                    self.request_exit_from_server()
                    break
                elif(console_input_string == "chatter_list()"):
                    print(self.chatter_list)
                    continue
                elif(console_input_string == "debug_mode_on()"):
                    self.__debug_mode = True
                    continue
                elif(console_input_string == "debug_mode_off()"):
                    self.__debug_mode = False
                    continue

                self.__send_message_to_all_chatters(console_input_string)

    def __send_message_to_all_chatters(self, Input_string):
        string_to_send = "MESG " + self.client_name + ": " + Input_string
        if not string_to_send.endswith('\n'):
            string_to_send += '\n'

        for chatter in self.chatter_list:
            ##Don't send MESG to yourself
            if chatter == (self.client_name, "127.0.0.1", str(self.client_port)):
                continue
            else:
                self.__send_string_to_udp(string_to_send, chatter[1], chatter[2])

    #################################################
    ##Generic Helper Functions for console writting##
    #################################################

    def __print_to_chat_console_log(self, Input_string):
        print(Input_string)

    def __print_to_chat_console(self, Input_string):
        self.__clear_console_line()
        print('\r' + Input_string, end='\n', flush=True)
        self.__print_client_name_to_chat_console()

    def __print_client_name_to_chat_console(self):
        print('\r' + self.client_name + ": ", end='', flush=True)

    def __clear_console_line(self):
        print("\r",end='')
        for i in range(self.MAX_SCREEN_NAME_LENGTH):
            print(" ",end='')

    #####################################################################################
    ##Start function for client. Must be run after initial connection to server is made##
    #####################################################################################
    def run(self):
        #Declare threads
        self.udp_input_thread = threading.Thread(target=self.__client_udp_thread_func)
        self.console_input_thread = threading.Thread(target=self.__client_console_thread_func)
        self.console_input_thread.daemon = True
        #Starts threads
        self.udp_input_thread.start()
        self.console_input_thread.start()

        #Waits for threads to finish (shouldn't happen)
        self.udp_input_thread.join()
        self.console_input_thread.join()

def main():
    #print("Number of arguments:", len(sys.argv), "arguments.")
    #print("Argument List:", str(sys.argv))
    #print("Hello World")

    # external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    # print(external_ip)

    if len(sys.argv) != 4:
        print("Incorrect number of arguments for calling YaChatClient.py")
        exit()

    client = ChatterClient(sys.argv[1], sys.argv[2], sys.argv[3])

    client.connect_to_server(0)
    try:
        client.run()
    except: 
        client.request_exit_from_server()

main()