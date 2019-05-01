# client.py
import socket

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
print('connection closed')
