import socket 
import threading
import json
import sys

#  next step is to send the message shared from one client to the other clients // at later steps 
# also maybe dont close the connection right away after one message and wait for the client to send a dissconnect command 
# so rn the problem is that even though client doesnt send disconnect command, based on the code below, the server just 
# closes the connection and it waits for a new client to connect
# i want the previous clinet to be still connected plus new clinets also can connect 

# we dont close the connection anymore and still can send messages 
# give each client a username and password to connect to server 
# next is to try connect multiple clinets and send messages to everyone 

user_data_base = {} # dictionary to store username and password of the clients, it does not get reset unless the entire server code is reset

mutex = threading.Lock() # mutex lock 


all_clients = {} # dict of all the conn nd address that are connected. to be used in broadcast_messages -> {conn:address}, it gets updates with users connecting/disconnectin
data_dict = {} # dictionary to do private messages with -> {username:conn}, it gets updates with users connecting/disconnectin



# this function will broadcast the message of each client to the rest of them 
def broacast_message(conn, address, message): # the conn parameter is the one sending the message so we dont send the message back to it, conn not comprable since 
    # its an object, but rather use address which is a tuple 
    # any time we have a new client getting accepted we get this conn variable 
    # we can just use this conn variable and store them in a list 
    # once we want to broadcast the messages, we can just use conn.sendall()
    # and just go through that list and then all the clients will receive that message 
    # other thing i need to think about is the problem i might have with the clients
    # how do i code the clients to get the message 
    # since i need to write them and also read from them then how can i do both ????? is that even possible 
    # yeah so i am thinking prolly we will need to create 2 diff threads -> one is reading text from the user, other one is displaying newest messages
    for each_client in all_clients:
        if all_clients[each_client] != address:
            try: 
                print(f"sending to client {all_clients[each_client]}")
                #### !!!!! message is not complete you need to add who wrote the message and format it, but for now its fine 
                each_client.sendall(message.encode("utf-8"))
            except:
                print("not any live clients in the chat to broadcast the message")
                del all_clients[each_client] # this means we have a broken pipe with the client, so we delete the client ???? maybe remove it later?


    # here is another loop to write the message to every single live client for chat_history because it's a group message 
    message = message.replace("/$n", "")
    for each_user in data_dict:
        filename = each_user+".txt"
        try: 
            with open(filename, 'a') as file:
                file.write(message+"\n") # message already contains the sender name too 
        except KeyboardInterrupt:
            print("server will be closed due to keyboard interrupt")
            sys.exit()
        except Exception as e:
            print(f"writing to {filename} failed: {e}")     
            

            

def direct_message(sender, conn_recv, message):
    message = "<DM> " + sender + " : " + message # adding the sender to message and a DM sign
    conn_recv.sendall(message.encode("utf-8")) # send the direrct message

#filename is specific to each username.txt
def read_chat_history(filename):
    with open(filename, 'r') as file:
        for lines in file:
            print(lines.strip())


def handle_client(conn, address):
    print("address connected:", address)
    waiting = True  

    try:

        while waiting:
            user_data = conn.recv(1024).decode("utf-8")  # receive user data from the client
            user_data = json.loads(user_data)  # convert the received data from json to python object
            if user_data[0] == 'new':
                # mutex lock to ensure threads can safely access the database
                with mutex:
                    if user_data[1] not in user_data_base: # new user doesnt already exist and we can add it to the database 
                        user_data_base[user_data[1]] = user_data[2]
                        username = user_data[1]
                        conn.sendall("1".encode("utf-8"))  # send "1" to confirm it worked
                        waiting = False

                    else: # username alreay exists so user needs to choose a different username
                        conn.sendall("0".encode("utf-8"))  # send "0" to indicate failure

            elif user_data[0] == 'registered':
                # mutex lock to ensure threads can safely access the database
                with mutex:
                    if user_data[1] in user_data_base and user_data[2] == user_data_base[user_data[1]]:
                        conn.sendall("1".encode("utf-8"))
                        username = user_data[1]
                        waiting = False
                    else:
                        conn.sendall("0".encode("utf-8"))    
            else: # since 'new' or 'registerted' are both hardcoded into the list from client side, this case means a keyboard interrupt happened
                print("connection was closed by the client due to keyboard or other interrupts")
                conn.close()
                return 
    except KeyboardInterrupt: 
        print("\nserver was closed due to keyboard interrupt")
        sys.exit() # close the entire program 
    except Exception as e:
        print("\nclient disconnected....")  
        sys.exit() # close the entire program 

    # add the new data to dictionary 
    data_dict[username] = conn

    # add this new client to our dictionary of live connections 
    all_clients[conn] = address 

    client_name = user_data[1] # name of the client to be displayed for each message

    try: 
        
        while True:

            entire_message = ""
            while True:
                message = conn.recv(1024).decode("utf-8")

                entire_message += message
                entire_message = entire_message.strip()
                if message.endswith("/$n"):
                    check = False
                    break

            entire_message = entire_message.replace('/$n', '')
            entire_message = entire_message.strip() 
            
            if "/disconnect" == entire_message:
                print("client requested to disconnect from the server")
                # response = "you will be disconnected from the server based on your request"
                # conn.sendall(response.encode("utf-8"))      
                del all_clients[conn] # remove that client from our list of live connections 
                del data_dict[username] # remove the specific user from our live connections so private messages will fail to this user
                conn.close()
                return  # exit the function to stop handling this client
            
            # example message is /private <ali> this is a text message for me
            elif entire_message.startswith("/private"):
                try:
                    parts = entire_message.split(" ", 2)
                    command = parts[0]
                    person = parts[1].strip("<>")
                    acc_msg = parts[2].strip() 
                    acc_msg+='/$n' # adding the element to indicate end of the message to be used later when we wanna read it

                    
                    
                    if person in data_dict:

                        # we found the user so send a direct message 
                        # next, send the message to that specific person 
                        # first based on the username, we need to find the specific address and conn object to be able to send the message 
                        # and check if the username even exists, if not send a message back to user
                        print("person was found in the dataset")
                        direct_message(username, data_dict[person] , acc_msg) # direct_message(sender, conn object for receriver, message)
                        # send a message and let the client(sender) know it was successful 
                        conn.sendall("KERNEL_PRIVATE_MESSAGE_PASSED_OK".encode("utf-8"))

                        # create 2 filenames -> using username variable and person
                        log_message = acc_msg.replace('/$n', '')
                        log_message = log_message.strip()
                        log_message_recp = "<DM> " + username + " : " + log_message # add the sender of the message 
                        log_message_sendr = "<DM> " + person + " : " + log_message # add the recipient of the message 

                        logging_file_sender = username + ".txt" # sender file 
                        logging_file_recipient = person + ".txt"  # recipient file 
                        with open(logging_file_recipient, 'a') as recv_file:
                            recv_file.write(log_message_recp+'\n')

                        with open(logging_file_sender, 'a') as sendr_file:
                            sendr_file.write(log_message_sendr+'\n')    


                    else:
                        print("user was not found in the dataset for a private message")
                        conn.sendall("KERNEL_PRIVATE_MESSAGE_FAILED".encode("utf-8"))    
                    
                    # print("we see the message-> will use direct_message function")
                    
                    continue # this way we will skip broadcast_function since this is a private message 

                except Exception as e:    
                    print("private message does not have the proper format, so we ignore it") ## we need to send a message back to the client and let them know about this!!!!
                    continue # this way we will skip broadcast_function since this is a private message 

            elif entire_message.strip() == "/chat_history":
                continue # nothing needed to be done here printing the messages will be done from single_client_test.py
                
                        

            

            # here we call broadcast the message 
            print(client_name," : ", entire_message.strip()) # just for test, print each clients message in the server 

            entire_message+= '/$n'
            entire_message = client_name + " : " + entire_message # add the sender of the message  
            broacast_message(conn, address, entire_message) # this is always the last step in handnle client function 

    except KeyboardInterrupt: 
        print("\nserver was closed due to keyboard interrupt")
        sys.exit() # close the program 
    except Exception as e:
        print("\nclient disconnected")  
        sys.exit() # close the program     

def start_server():

    # SERVER = "" # this could be used if we just use a local host 
    SERVER = "10.0.0.35" # i got this IP address by getting the IP address of my mac with ifconfig | grep inet
    # any client(with the same wifi) trying to connect should use the same server i have here 
    PORT = 8080  # Port to listen on (non-privileged ports are > 1023)
    ADDRESS = (SERVER, PORT)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDRESS)
    server.listen()
    # !!!!!!!
    ##### this works with the special character but also add a preventive measure to avoid the server from crashing if the client sends a message that is not terminated with /$n
    try: 
        print("waiting for connection...")
        while True:
            

            
            conn, address = server.accept()

            # # add this new client to our dictionary of live connections 
            # all_clients[conn] = address it was moved up in handle_client function 
            
            thread = threading.Thread(target = handle_client, args = (conn, address)) # here we create another thread to handle receving the messages from the client
            thread.start() 
        
    except KeyboardInterrupt: 
        print("\nserver was closed due to keyboard interrupt")
        server.close()
        sys.exit()
    except Exception as e:
        print("\nclient disconnected")  
        server.close()
        sys.exit()

start_server()