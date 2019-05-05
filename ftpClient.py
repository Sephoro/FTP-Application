#client.py

import socket
import math
import sys
import time

class FTPclient:
    def __init__(self, serverIPname, serverIPport):

        self.IPsocket = None
        self.DTPsocket = None
        self.errorResp = False
        self.alive = False
        self.loggedIn = False
        self.user = None
        self.serverIPname = serverIPname
        self.serverIPport = serverIPport
        
    def initConnection(self):

        self.IPsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        try:

            self.IPsocket.connect((self.serverIPname,self.serverIPport))
            self.getServerReply()
            
        except:

            errMSG = 'Failed to connect ' + self.serverIPname
            print(errMSG)
            self.errorResp = True
            time.sleep(3)
            return

        self.alive = True
        print('Connected to server :)')
    
    def login(self, userName, password):
        
        # enter username
        cmd = 'USER ' + userName
        self.send(cmd)
        
        if not self.errorResp:
            # enter password
            cmd = 'PASS ' + password
            self.send(cmd)

            if not self.errorResp:
                self.loggedIn = True
                self.user = userName
                print('Login Success')

                
    def send(self, cmd):
        
        self.IPsocket.send((cmd + '\r\n').encode())
        self.getServerReply()

    def getServerReply(self):

        resp = self.IPsocket.recv(1024).decode()
        
        # Notify if this an error
        if resp[0] != '5' and resp[0] != '4':
            self.errorResp = False
            print(resp[0])
        else:
            self.errorResp = True
        print('Server: ', resp)

            
def Main():
    
    serverIP = 12000
    serverName = 'localhost'
    userName = 'Elias'
    password = 'aswedeal'
    client = FTPclient(serverName,serverIP)
    client.initConnection()
    client.login(userName, password)
    
Main()