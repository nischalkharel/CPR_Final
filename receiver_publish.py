import socket
import time

#collect connection information host and port
#collect authentication code (also encodes black/white/either)
def get_move(ip, the_port, black_white):
    unlocked = False
    authorized = False
    auth_code_max_length = 255 #should fit within 1 byte

    while not unlocked:
        host_ip = ip
        port = the_port #7777

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((host_ip, int(port)))
        except:
            print("Connection failed. Please check the IP address, port, and server firewall.")
            continue #shouldn't crash when the connection fails
        #s.connect((host_ip, int(port)))

        unlocked = True

    while not authorized:
        match black_white:
            case "black":
                auth_code = "receive_black"
            case "white":
                auth_code = "receive_white"

        auth_sequence = auth_code.encode("utf-8")

        x = len(auth_sequence)
        if x < auth_code_max_length:
            s.send(x.to_bytes(1, byteorder="big"))
            s.send(auth_sequence)

            time.sleep(1) #maybe server needs to process

            y = s.recv(1) #receive return message length

            print(y)

            success = s.recv(int.from_bytes(y, byteorder="big")) #receive return message

            print(success)

            if int.from_bytes(success, byteorder="big") == 1:
                authorized = True
            else:
                print("Incorrect Auth Code, please try redownloading the program")

    message_length = s.recv(1)
    message = s.recv(int.from_bytes(message_length, byteorder="big"))
    EOF = 1
    s.send(EOF.to_bytes(1, byteorder="big")) #end connection signal

    s.close() #properly close the connection

    return message.decode("utf-8")

'''main program'''
""" 
ip = "123.456.7.8"
port = 7777

while True:
    print(get_move(ip, port, "white"))
    time.sleep(1)
    print(get_move(ip, port, "black"))
    time.sleep(1)
 """








