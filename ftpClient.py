# client.py
""" import socket

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host = '10.196.51.12' # Or preferably 'localhost' # my IP address 10.196.6.30 
port = 60000

s.connect((host, port))

wm = 'Hello Server!' #Welcome Message
s.send(wm.encode())

with open('received_file.txt', 'wb') as f:
    print('file opened')
    while True:
        print('receiving data...')
        data = s.recv(1024)
        print(data)
        if not data:
            break
        f.write(data)

f.close()
print('succesfully get the file')
s.close()
print('connection closed') """

import socket
import os

def send(sock,msg):
    print('--> Sending: ' + msg)
    sock.send(msg + '\r\n')
    reply = sock.recv(1024)
    print('<-- Reply: ' + reply )
    return reply

serverPIname = 'localhost'#'127.0.1.1'# 'localhost' #'test.rebex.net'#'speedtest.tele2.net'#'ftp.swfwmd.state.fl.us' #'localhost'
serverPIport =  12000

clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
clientSocket.connect((serverPIname,serverPIport))

condition220 = True
message = clientSocket.recv(2048).decode()
print(message)

""" while condition220:
    message = clientSocket.recv(2048)
    print(message)
    condition220 = message[0:3] != '220' """
    

while True:   
    command = input('--> ')
    clientSocket.send((command+'\r\n').encode())
    reply = clientSocket.recv(1024).decode()
    print(reply)

clientSocket.close()