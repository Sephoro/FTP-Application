# client.py
# Authors - Boikanyo Radiokana (1386807)
# Authors - Elias Sepuru (1427726) 

import socket
import math
import sys
import time
import os
        
class FTPclient:
    def __init__(self, clientName):

        self.IPsocket = None
        self.DTPsocket = None
        self.errorResp = False
        self.alive = False
        self.loggedIn = False
        self.user = None
        self.remotedirList = []
        self.collectMSG = []
        self.statusMSG = ' '
        self.clientName = clientName
        
    def initConnection(self, serverIPname, serverIPport):

        self.serverIPname = serverIPname
        self.serverIPport = serverIPport
       
        self.IPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Try to connect to server
        try:

            self.IPsocket.connect((self.serverIPname, self.serverIPport))
            print(self.IPsocket.recv(8192).decode())

        except:

            errMSG = 'Failed to connect ' + self.serverIPname
            self.statusMSG = errMSG
            print(errMSG)
            self.errorResp = True
            time.sleep(3)
            return

        self.alive = True
        
        print('Connected to Server ;)')
    
    def getStatus(self):
        
        return self.statusMSG

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
                msg =('Login Success\n')
                print(msg)
                self.statusMSG = msg
                

    def send(self, cmd):
        # Sending commands to server
        self.IPsocket.send((cmd + '\r\n').encode())
        # Dont print or log the password
        if cmd[:4] != 'PASS':
            print('Client: ', cmd)
            self.collectMSG.append('Client: ' + cmd)

    def getServerReply(self):

        resp = self.IPsocket.recv(8192).decode()
        self.collectMSG.append('Server: ' + resp)

        # Notify if this an error
        if resp[0] != '5' and resp[0] != '4':
            self.errorResp = False
        else:
            self.errorResp = True
        return resp

    def printServerReply(self, resp):
        
        print('Server :', resp)
    
    def setMode(self, mode):
        
        # Set mode of data transfer
        if mode.upper() == 'I' or mode.upper() == 'A':
            self.mode = mode
            cmd = 'TYPE '  + mode
            self.send(cmd)
            self.printServerReply(self.getServerReply())

        else:
            msg = ('Client : Error unknown mode')
            self.statusMSG = msg
            print(msg)
    
    def getComm(self):
        return self.collectMSG
    
    def clearComm(self):
        self.collectMSG.clear()


    def startPassiveDTPconnection(self):

        # Ask for a passive connection
        cmd = 'PASV'
        self.send(cmd)
        resp = self.getServerReply()
        self.printServerReply(resp)

        if not self.errorResp:

            firstIndex = resp.find('(')
            endIndex = resp.find(')')

            # Obtain the server DTP address and Port
            addr = resp[firstIndex+1:endIndex].split(',')
            self.serverDTPname = '.'.join(addr[:-2])
            self.serverDTPport = (int(addr[4]) << 8) + int(addr[5])
            print(self.serverDTPname, self.serverDTPport)

            try:
                # Connect to the server DTP
                self.DTPsocket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                self.DTPsocket.connect(
                    (self.serverDTPname, self.serverDTPport))
                self.statusMSG = 'Passive Connection Success, Ready to receive'
                print('Passive Connection Success, Ready to receive\n')
                
                self.dataConnectionAlive = True

            except:

                print('Failed to connect to ', self.serverDTPname)
                self.statusMSG = 'Failed to connect to '+ self.serverDTPname
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
        self.statusMSG = 'Requested... IP: ' + ip + 'Port: ' + str(port)
        
        cmd = 'PORT ' + ip + ',' + str(p1) + ',' + str(p2)
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        
        # Start Connection
        self.DTPsocket, addr = self.clientSocket.accept()
        print('Connected to :' , addr)
        self.statusMSG  = 'Connected to :' +  str(addr)
        self.dataConnectionAlive = True


    def getList(self):
        
        self.remotedirList = []
        # Cant't get list if disconnected
        if self.dataConnectionAlive and self.alive:

            cmd = 'LIST'
            self.send(cmd)
            self.printServerReply(self.getServerReply())
            
            print('\nReceiving Data...\n')
            self.statusMSG = 'Receiving Data...'

            while True:
                # Get the directory list
                data = self.DTPsocket.recv(8192)
                self.remotedirList.append(data.decode())

                if not data:
                    break

            print('Directory Listing Done!\n')
            self.statusMSG ='Directory Listing Done!'
            self.DTPsocket.close()
            self.printServerReply(self.getServerReply())
    
    def downloadFile(self,fileName):
        
        # Send download command
        cmd = 'RETR ' +  fileName
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        
        # Dont continue if there is an error 
        if not self.errorResp:
            
            # Create Downloads folder if not exist

            downloadFolder = 'Downloads'
            if not os.path.exists(downloadFolder):
                os.makedirs(downloadFolder)
            
            # Mode of data transfer
            if self.mode == 'I':
                outfile = open(downloadFolder + '/' + fileName, 'wb')
            else:
                outfile = open(downloadFolder + '/' + fileName, 'w')
            
            # Get them packets :D
            print('Receiving data...')
            self.statusMSG = 'Recieving data...'
            
            while True:
                data = self.DTPsocket.recv(8192)
                if not data:
                    break
                outfile.write(data)
            outfile.close()
            # Done
            print('Transfer Succesfull')
            self.statusMSG = 'Transfer Successfull'
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
                self.statusMSG = 'Uploading ' + fileName + ' to server...'

                if self.mode == 'I':
                    uFile = open(filePath, 'rb')
                else:
                    uFile = open(filePath, 'r')
                
                # Send packets of the file
                data =  uFile.read(8192)

                while data:

                    if self.mode == 'I':
                        self.DTPsocket.send(data)
                    else:
                        self.DTPsocket.send(data.encode())
                    data = uFile.read(8192)

                uFile.close()
                print('Upload success')
                self.statusMSG = ' Upload Success'
                self.DTPsocket.close()
                self.printServerReply(self.getServerReply())
                
        else:
            print('Error: invalid path!')
            self.statusMSG = 'Error: invalid path!'
            self.DTPsocket.close()
            
    def returnDirList(self):

        return self.remotedirList
    
    def changeWD(self,dir_):

        # Change working directory
        cmd = 'CWD ' + dir_
        self.send(cmd)
        self.printServerReply(self.getServerReply())
    
    def makeDir(self,folderName):
        
        # Create a new directory on server
        cmd = 'MKD ' + folderName
        self.send(cmd)
        self.printServerReply(self.getServerReply())
    
    def remDir(self,folderName):

        # Delete directory on server
        cmd = 'RMD ' + folderName
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        
    def logout(self):
        
        #Close connection
        cmd = 'QUIT'
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        self.statusMSG = 'Logged out, Connection Closed'
        
    def checkConnection(self):
        
        cmd = 'NOOP'
        self.send(cmd)
        self.printServerReply(self.getServerReply())
