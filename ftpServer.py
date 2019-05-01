import socket

port = 60000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', port))
s.listen(5)

print('Server listening...')

while True:
    conn, addr = s.accept()
    print('Got connection from' , addr)
    data = conn.recv(1024).decode()
    
    print('Server received', repr(data) )
    
    #open file
    filename = 'mytext.txt'
    f = open(filename, 'rb')
    l = f.read(1024)

    
    while(l):
        #send file
        conn.send(l)
        print('Sent', repr(l))
        l = f.read(1024)
    f.close()
    
    print('Done sending')
    conn.send(('Thank you for connecting').encode())
    conn.close()