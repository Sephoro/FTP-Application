#client.py

import socket
import math
import sys
import time
import os

class FTPclient:
    def __init__(self, serverIPname, serverIPport,clientName):

        self.IPsocket = None
        self.DTPsocket = None
        self.errorResp = False
        self.alive = False
        self.loggedIn = False
        self.user = None
        self.serverIPname = serverIPname
        self.serverIPport = serverIPport
        self.clientName = clientName
        
    def initConnection(self):

        self.IPsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        try:

            self.IPsocket.connect((self.serverIPname,self.serverIPport))
            print(self.IPsocket.recv(1024).decode())
            
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
        self.printServerReply(self.getServerReply())
        
        if not self.errorResp:
            # enter password
            cmd = 'PASS ' + password
            self.send(cmd)
            self.printServerReply(self.getServerReply())

            if not self.errorResp:
                self.loggedIn = True
                self.user = userName
                print('Login Success\n')

                
    def send(self, cmd):

        self.IPsocket.send((cmd + '\r\n').encode())
        print('Client: ', cmd)

    def getServerReply(self):
        
        resp = self.IPsocket.recv(1024).decode()
        
        # Notify if this an error
        if resp[0] != '5' and resp[0] != '4':
            self.errorResp = False
        else:
            self.errorResp = True
        return resp
    
    def printServerReply(self,resp):
        print('Server :', resp)
    
    def setMode(self, mode):

        if mode.upper() == 'I' or mode.upper() == 'A':
            self.mode = mode
            cmd = 'TYPE '  + mode
            self.send(cmd)
            self.printServerReply(self.getServerReply())

        else:
            print('Client : Error unknown mode')


    def startPassiveDTPconnection(self):
        
        #Ask for a passive connection
        cmd = 'PASV'
        self.send(cmd)
        resp = self.getServerReply()
        self.printServerReply(resp)

        if not self.errorResp:
            
            firstIndex = resp.find('(')
            endIndex  = resp.find(')')
            
            # Obtain the server DTP address and Port
            addr = resp[firstIndex+1:endIndex].split(',')
            self.serverDTPname = '.'.join(addr[:-2])
            self.serverDTPport = (int(addr[4])<<8) + int(addr[5])
            print(self.serverDTPname,self.serverDTPport)

            try:
                #Connect to the server DTP
                self.DTPsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.DTPsocket.connect((self.serverDTPname,self.serverDTPport))
                print('Passive Connection Success, Ready to receive\n')
                self.dataConnectionAlive = True

            except:

                print('Failed to connect to ', self.serverDTPname)
                self.dataConnectionAlive = False
                time.sleep(3)
                return

    def startActiveConnection(self):

        # Request for an active connection
        self.clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.clientSocket.bind((self.clientName,0))
        self.clientSocket.listen(1)

        ip, port = self.clientSocket.getsockname()
         
        # Ready the ip with respect to the RFC959 standard
        ip = ip.split('.')
        ip = ','.join(ip)

        # Ready the Port with respect to the TFC959 standard
        p1 = math.floor(port/256)
        p2 = port%256
    
        print('Requested...\n IP: ' + ip + '\nPort: ' + str(port))
        
        cmd = 'PORT ' + ip + ',' + str(p1) + ',' + str(p2)
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        
        # Start Connection
        self.DTPsocket, addr = self.clientSocket.accept()
        print('Connected to :' , addr)
        self.dataConnectionAlive = True


    def getList(self):
         
        # Cant't get list if disconnected
        if self.dataConnectionAlive and self.alive:

            cmd = 'LIST'
            self.send(cmd)
            self.printServerReply(self.getServerReply())

            print('\nReceiving Data\n')

            while True:
                # Get the directory list
                data = self.DTPsocket.recv(1024)
                print(data.decode())

                if not data:
                    break
           
            print('Downloading done\n')
            self.DTPsocket.close()
            self.printServerReply(self.getServerReply())
    
    def downloadFile(self,fileName):

        downloadFolder = 'Downloads'
        cmd = 'RETR ' +  fileName
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        
        # Dont continue if there is an error 
        if not self.errorResp:

            # Create Downloads folder
            if not os.path.exists(downloadFolder):
                os.makedirs(downloadFolder)
            
            if self.mode == 'I':
                outfile = open(downloadFolder + '/' + fileName, 'wb')
            else:
                outfile = open(downloadFolder + '/' + fileName, 'w')
            
            print('Receiving data...')
            while True:
                data = self.DTPsocket.recv(1024)
                if not data:
                    break
                outfile.write(data)
            outfile.close()
            print('Transfer Succesfull')
            self.DTPsocket.close()
            self.printServerReply(self.getServerReply())
            
    
    def uploadFile(self,filePath):

        #Check if file path is valid
        if os.path.exists(filePath):
            # Get the file name
            if '/' in filePath:
                f_index = filePath.rindex('/')
                fileName = filePath[f_index+1:]
            else:
                fileName = filePath

            # Send Command
            cmd = 'STOR ' + fileName
            self.send(cmd)
            self.printServerReply(self.getServerReply())
        
            # Continue if there are no errors reported
            if not self.errorResp:
                print('Uploading ' + fileName + ' to server...')

                if self.mode == 'I':
                    uFile = open(filePath, 'rb')
                else:
                    uFile = open(filePath, 'r')
                
                # Send packets of the file
                data =  uFile.read(1024)

                while data:

                    if self.mode == 'I':
                        self.DTPsocket.send(data)
                    else:
                        self.DTPsocket.send(data.encode())
                    data = uFile.read(1024)

                uFile.close()
                print('Upload success')
                self.DTPsocket.close()
                self.printServerReply(self.getServerReply())
                
        else:
            print('Error: invalid path!')
            self.DTPsocket.close()

    
    def changeWD(self,dir):
        
        cmd = 'CWD ' + dir
        self.send(cmd)
        self.printServerReply(self.getServerReply())


            

def Main():
    
    clientName = 'localhost'
    # Testing ftp servers
    Po = [21,12000,21,21,12005]
    S  = ['speedtest.tele2.net', 'localhost','test.rebex.net','dlptest.com','localhost']
    U  = ['anonymous','Elias','demo','dlpuser@dlptest.com','tokelo']
    Pa = ['anonymous','aswedeal', 'password','5p2tvn92R0di8FdiLCfzeeT0b','1234']

    server = 1
    serverIP = Po[server]
    serverName = S[server]
    userName =  U[server]
    password = Pa[server]
    client = FTPclient(serverName,serverIP,clientName)
    client.initConnection()
    client.login(userName, password)
    client.setMode('I')
    client.startActiveConnection()
    client.getList()
    time.sleep(1)
    client.changeWD('HOME')
    client.startActiveConnection()
    client.getList()
    """ time.sleep(1)
    client.startPassiveDTPconnection()
    client.uploadFile('Downloads/bw.jpg')
    time.sleep(1)
    client.startPassiveDTPconnection()
    client.getList() """
    
    
Main()