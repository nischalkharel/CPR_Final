'''
again, code from
https://docs.python.org/3/howto/sockets.html
https://www.geeksforgeeks.org/socket-programming-python/
'''

import socket
#import multiprocessing
import threading
import time

def authenticate(socket):

    length = socket.recv(1)
    code = socket.recv(int.from_bytes(length, byteorder="big"))
    message = code.decode("utf-8")

    print(message)

    value1 = 1
    value0 = 0

    match message:
        case "test_black":
            socket.send(value1.to_bytes(1, byteorder="big")) #length of message
            socket.send(value1.to_bytes(1, byteorder="big")) #message is also a one

            print("triggered black")

            return 'b'
        case "test_white":
            socket.send(value1.to_bytes(1, byteorder="big"))
            socket.send(value1.to_bytes(1, byteorder="big"))
            return 'w'
        case "test_both":
            socket.send(value1.to_bytes(1, byteorder="big"))
            socket.send(value1.to_bytes(1, byteorder="big"))
            return 'e'
        case "receive_black":
            socket.send(value1.to_bytes(1, byteorder="big"))
            socket.send(value1.to_bytes(1, byteorder="big"))
            return "b2"
        case "receive_white":
            socket.send(value1.to_bytes(1, byteorder="big"))
            socket.send(value1.to_bytes(1, byteorder="big"))
            return "w2"
        case default:
            socket.send(value1.to_bytes(1, byteorder="big"))
            socket.send(value0.to_bytes(1, byteorder="big"))

            print("triggered default")

            return 'x'
        
def receive_move(socket):
    length = socket.recv(1)
    encoded_message = socket.recv(int.from_bytes(length, byteorder = "big"))
    message = encoded_message.decode("utf-8")

    print(message)

    return message

def get_moves_thread(clientsocket, lock):
    global move_buffer

    go = 'x'
    while go == 'x':
        go = authenticate(clientsocket)

    connected = True
    while connected:
        match go:
            case 'b':
                moves = receive_move(clientsocket)

                if moves == "":
                    connected = False
                    continue

                #multiprocessing.lock.acquire()
                lock.acquire()
                move_buffer[0] = moves
                #multiprocessing.lock.release()
                lock.release()

                print(move_buffer)
                time.sleep(1) #no need for continuous data transfer
            case 'w':
                moves = receive_move(clientsocket)

                if moves == "":
                    connected = False
                    continue

                #multiprocessing.lock.acquire()
                lock.acquire()
                move_buffer[1] = moves
                #multiprocessing.lock.release()
                lock.release()

                print(move_buffer)
                time.sleep(1) #no need for continuous data transfer
            case 'e':
                moves = receive_move(clientsocket)

                if moves == "":
                    connected = False
                    continue

                #multiprocessing.lock.acquire()
                lock.acquire()
                move_buffer[0] = moves
                move_buffer[1] = moves
                #multiprocessing.lock.release()
                lock.release()

                print(move_buffer)
                time.sleep(1) #no need for continuous data transfer
            case 'b2':
                message = move_buffer[0]
                message_length = len(message)
                clientsocket.send(message_length.to_bytes(1, byteorder="big")) #length of message
                clientsocket.send(message.encode("utf-8")) #message

                clientsocket.recv(1) #closing exchange
            case 'w2':
                message = move_buffer[1]
                message_length = len(message)
                clientsocket.send(message_length.to_bytes(1, byteorder="big")) #length of message
                clientsocket.send(message.encode("utf-8")) #message

                clientsocket.recv(1) #closing exchange

'''
main program
'''  

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#serversocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port = 7777 #just a random port I make for this
serversocket.bind((socket.gethostname(), port)) #use "0.0.0.0" to accept any IP address #lies . . .


#socket.gethostname() returns 'DESKTOP-GO1JE2E' on my device . . .
my_IP = socket.gethostbyname(socket.gethostname())
print(f"Your IP address is {my_IP}")
#print(f"your IP is of data type {type(my_IP)}") #ip addresses are just strings

serversocket.listen(5) #well, both tutorials used a max of 5 connections, so why not?

move_buffer = ["",""]
while True:
    (clientsocket, address) = serversocket.accept()
    print(f"socket 1 connected to device at {address}")

    my_lock = threading.Lock() #with multithreading locks exist separately from the threads

    my_thread = threading.Thread(target = get_moves_thread, args = (clientsocket, my_lock))

    my_thread.start()

