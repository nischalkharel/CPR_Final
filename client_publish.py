'''
Put intro here

Credits to
https://realpython.com/playing-and-recording-sound-python/
https://github.com/openai/whisper?tab=readme-ov-file
https://ffmpeg.org/ffmpeg.html#Trancoding

and Bing Chat AI for answering some syntax queries and member function explanations
'''

import sounddevice
from scipy.io.wavfile import write

import subprocess
import os

import whisper

import unicodedata

import socket
import time

def record_audio(duration, filename = "sound.wav"):
    sample_rate = 44100 #standard value in Hz

    my_recording = sounddevice.rec(int(duration * sample_rate), samplerate = sample_rate, channels = 2) #a numpy array of recorded values
    sounddevice.wait() #waits for recording to finish

    #filename2 = "\"" + os.curdir + "/" + filename + "\""
    #like whisper, sounddevice isn't liking quotation marks and os.curdir
    filename2 = os.curdir + "/" + filename

    write(filename2, sample_rate, my_recording)

def transcode_audio(input = "sound.wav", output = "sound.mp3"):
    my_cmd = "ffmpeg -i \"" + os.curdir + "/" + input + "\" \"" + os.curdir + "/" + output + "\" -y"
    #-y is to overwrite any existing file with os.curdir + /sound.mp3 name

    subprocess.check_call(
        my_cmd, shell=True
    )

def transcribe_audio(input = "sound.mp3"):
    model = whisper.load_model("tiny.en")

    #filepath = "\"" + os.curdir + "/" + input + "\""
    #so, for some reason whisper doesn't like "./sound.mp3" . . . it doesn't want the quotation marks when you use "."
    filepath = os.curdir + "/" + input

    result = model.transcribe(filepath)
    #print(result["text"])

    return result["text"]

def detect_audio():
    sample_rate = 44100
    duration = 2
    threshold = 0.5

    print("Please Make Noise")

    my_recording = sounddevice.rec(int(duration * sample_rate), samplerate = sample_rate, channels = 2) #a numpy array of recorded values
    sounddevice.wait() #waits for recording to finish

    #print(my_recording.max())
    #print(my_recording.min())
    #print(my_recording.mean())

    if my_recording.max() > threshold:
        return True
    else:
        return False

def str_to_move(my_str):
    my_str = my_str.lower() #convert all letters to lowercase
    sentence = my_str.split() #separates a string by whitespaces into an array of shorter strings

    #print(sentence)
    #print(len(sentence))

    move_count = 0 #keeps track of number of detected board positions in the input string
    move = [] #keeps track of the detected moves

    for word in range(0, len(sentence)): #cycles through the array of strings
        #print(word)
        #print(sentence[word])
        #print(len(sentence[word]))

        for letter in range(1, len(sentence[word])): #cycles through the letters after the first letter of each short string
            #skip the first letter b/c search algorithm begins by looking for numbers; if the first letter is a number it cannot stand for a move

            type = unicodedata.category(sentence[word][letter]) #finds letter type
            #print(type)

            if type == "Nd": #if the letter is a number
                value = int(sentence[word][letter])
                if (value < 9) and (value > 0):
                    #print(sentence[word][letter])
                    #print(unicodedata.category(sentence[word][letter-1]))

                    if unicodedata.category(sentence[word][letter-1]) == "Ll": #if the number is preceeded by a letter
                        #print(sentence[word][letter-1] + sentence[word][letter])

                        if (sentence[word][letter - 1] >= "a") and (sentence[word][letter - 1] < "i"): #if the letter can be for a move
                            move.append(sentence[word][letter-1] + sentence[word][letter])
                            move_count = move_count + 1

                            #print(move_count)
                            #print(sentence[word][letter-1] + sentence[word][letter])

    if move_count == 2:
        return move
    else:
        return "error, please try again"

'''main program here'''

#collect connection information host and port
#collect authentication code (also encodes black/white/either)
unlocked = False
authorized = False
auth_code_max_length = 255 #should fit within 1 byte

while not unlocked:
    host_ip = input("Enter CPR IP Address:\n")
    port = input("Enter CPR Port:\n")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((host_ip, int(port)))
    except:
        print("Connection failed. Please check the IP address, port, and server firewall.")
        continue #shouldn't crash when the connection fails
    #s.connect((host_ip, int(port)))

    unlocked = True

while not authorized:
    auth_code = input("Enter Player Code:\n") #not restricted to numbers, but do restrict length

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
            print("Incorrect Player Code")

#gets audio and sends move
playing = True
while playing:
    while True: #allow ending the loop without pressing start and for the user to trigger the audio recording's start time
        keep_going = input("Please enter 1 to record audio or 0 to exit:\n")
        if keep_going == "1":
            break
        elif keep_going == "0":
            playing = False
            break
        else:
            print("Please enter 1 or 0")

    if not playing:
        break

    print("speak move")
    record_audio(7)
    transcode_audio()
    output = transcribe_audio()

    move = str_to_move(output)

    print(move)

    if move != ["00", "00"]:
        message = move[0] + move[1]
        encoded_message = message.encode("utf-8")
        s.send(len(encoded_message).to_bytes(1, byteorder="big"))
        s.send(encoded_message)
1
print("program complete")








