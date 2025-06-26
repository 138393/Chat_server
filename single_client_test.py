import socket 
import json 
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
import threading 
from prompt_toolkit import prompt, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from getpass import getpass


kb = KeyBindings()
@kb.add('c-d')
def _(event):
    event.app.exit(result=event.app.current_buffer.text)


def group_messages(socket_conn): # this will be another thread to indicate messages to the user # but how???
    # cuz when terminal is open, and user is typing, how do we wanna update the user and show new messages to them ???
    # this group should also be able to read message that are private ??!! i think so 
    entire_message = ''
    while True:
        message = socket_conn.recv(1024).decode("utf-8")
        entire_message+= message
        entire_message = entire_message.strip()
        if entire_message.startswith("KERNEL_PRIVATE_MESSAGE_PASSED_OK"):
            print_formatted_text(FormattedText([("fg:plum", "your private message was sent successfully")]))
            
            entire_message = "" # reset for next round 
            #somehow let the client know it was successful
        elif entire_message.startswith("KERNEL_PRIVATE_MESSAGE_FAILED"):
            print_formatted_text(FormattedText([("fg:plum", "the person you tried to contact does not exist in the system")]))
            entire_message = ''    
        
        elif entire_message.endswith("/$n"): 
            entire_message = entire_message.replace('/$n', '').strip()
            print_formatted_text(FormattedText([("fg:gray", entire_message)]))
            entire_message = ''
            
    

def register_user(): 
    username = input("Enter a username: ")
    password = getpass("Enter a password: ")
    
    # Here you would typically send this data to the server for registration
    # For now, we will just print it
    print(f"User registered with username: {username} and password: {password}")
    return ['new',username,password]

def sign_in_user():
    username = input("Enter your username: ")
    password = getpass("Enter your password: ")
    
    # Here you would typically send this data to the server for authentication
    # For now, we will just print it
    print(f"User signed in with username: {username} and password: {password}")
    return ['registered',username,password]

def start_client():


    # HOST = 'raspberrypi.local'  # OR replace with your Pi’s IP address
    # HOST = 'localhost'
    HOST = "10.0.0.35" # IP address I got to connect to my server
    PORT = 8080
    check = True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        try :
            while check: # new user or registered user
                new_or_registered = input("choose 'new' to register or 'registered' to connect to the server: ").strip().lower()
                if new_or_registered == 'new':
                    user_data = register_user()
                    username = user_data[1] 
                    s.sendall(json.dumps(user_data).encode('utf-8'))  # send user data to the server
                    success_or_not = s.recv(1024).decode('utf-8')  # wait for server response to confirm registration
                    if success_or_not == '0':
                        print("Username already exists, please choose a different username.")
                        continue
                    # i need more cases here to handle what happens in the server if user exists or not 
                    check = False
                elif new_or_registered == 'registered':
                    user_data = sign_in_user()
                    username = user_data[1] 
                    s.sendall(json.dumps(user_data).encode('utf-8')) # send user data to the server
                    success_or_not = s.recv(1024).decode('utf-8')  # wait for server response to confirm registration
                    if success_or_not == '0':
                        print("Username or password is incorrect, please try again.")
                        continue
                    check = False
                else:
                    print("invalid input, please try again")    
        
        except KeyboardInterrupt: # process was interrupted so we end this communication 
            print("\nkeyboard interrupt happened, and connection was closed")
            user_data = ["stop"] 
            s.sendall(json.dumps(user_data).encode('utf-8')) # send user data to the server
            return 

    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #     s.connect((HOST, PORT))

        
        print("connection established, type your message...")

        # start a new thread here to broadcast messages to each client 
        # but would this cause a trouble in the terminal while user is typing sth, and at the same time display sth else 
        # it will cause problems so in order to avoid problems, prompt_toolkit will help us 
        thread = threading.Thread(target=group_messages, args=(s,), daemon=True)
        thread.start()
            
        # loop here to make sure the clinent can send multiple messages
        while True: 

            try:
                entire_message = prompt("Enter your message (press Ctrl+D to send):\n", multiline=True, key_bindings=kb)
                # entire_message = ""    
                # while True:
                #     message = input()
                    
                #     entire_message += message + "\n"
                #     if '/$n' in message: # we will read everything as a single message until we see \$n 
                #         print("END OF MESSAGE")
                #         break


                entire_message+= '/$n'
                print("MESSAGE SENT")
                s.sendall(entire_message.encode('utf-8')) # send the message to the server
                
            except KeyboardInterrupt: 
                print("\nkeyboard interrupt detected, Informing server and closing connection")
                entire_message = "/disconnect/$n"
                s.sendall(entire_message.encode('utf-8'))    
            except Exception as e:
                print("exception occured due to your input")
                return    


            entire_message = entire_message.replace('/$n', '')
            entire_message = entire_message.strip()
            if '/disconnect' == entire_message:
                # response = s.recv(1024)
                # print(response.decode('utf-8'))
                print("you will be disconnected from the server based on your request")
                return  # exit the function to stop handling this client
            
            # example message is /private <ali> this is a text message for me
            elif entire_message.startswith("/private"):
                try:
                    parts = entire_message.split(" ", 2)
                    command = parts[0]
                    person = parts[1].strip("<>")
                    acc_msg = parts[2]
                    
                    # we wait for a response from the server in group_messages thread to hear a response from server to see if message was sent
                    # successfully or not, and based on that user gets a message back
                    
                
                except Exception as e:
                    # uncompleted message 
                    # think of what to do here 
                    print("your message does not have the proper format, refer to manual to learn about the format")

            elif entire_message.strip() == "/chat_history":
                print("your chat history including group messages and DMs will be displayed soon") 
                file_to_read = username + ".txt" # file to read for the client 
                with open(file_to_read, 'r') as myfile:
                    for lines in myfile:
                        print(lines)       


start_client()