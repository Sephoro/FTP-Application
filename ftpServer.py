#***********************#
#      Elias Sepuru     #
#   Boikanyo Radiokana  #
#        FTP Server     #
#       07-May-2019     #
#***********************#

import socket
import os
import time
import threading
import math

class serverThread(threading.Thread):
    
    def __init__(self, conn, addr,usersDB, currDir,IP, port):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.serverIP = IP
        self.serverPort = port
        self.baseWD = currDir
        self.cwd = self.baseWD
        self.rest = False
        self.PASVmode = False
        self.isLoggedIn = False
        self.users = usersDB
        self.validUser = False
        self.isConnected = True
        self.islist = False
        self.mode = 'I' #Default Mode
        self.allowDelete = True
    
    def run(self):

        self.isConnected = True
        # Welcome Message
        resp = '220 Welcome!'
        self.sendReply(resp)
        # Await for connection from clients
        while True:
            
            cmd = self.conn.recv(256).decode()
            
            if not cmd or not self.isConnected : break
            else:
                print('Recieved: ', cmd)
                try:
                    func = getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception as err:
                    print('Error: ', err)
                    resp = '500 Syntax error, command unrecognized.'
                    self.sendReply(resp)
        
        self.conn.close()
   
    def sendReply(self,reply):
        self.conn.send((reply + '\r\n').encode())
    
    def notLoggedInMSG(self):
        res = '530 Please login with USER and PASS.'
        self.sendReply(res)

    def paramError(self,cmd):
        res = '501 \'' + cmd[:-2] + '\': parameter not understood.' 
        self.sendReply(res)
    
    def resetState(self):
         
        # RESET STATE of affairs
        self.isLoggedIn = False
        self.validUser = False
        self.user = None


    def SYST(self,cmd):
        resp = '215 UNIX Type: L8.'
        self.sendReply(resp)
    
    def USER(self,cmd):
        
        #RESET STATE, Incase someone logs in while the other is still logged in
        self.resetState()

        # Extract username in the command
        self.user = cmd[5:-2]
        
        # Read users file
        users = open(self.users, 'r').read()
        
        # Check if user exists on the database
        for u in users.split('\n'):
            if self.user == u.split(' ')[0] and len(u.split(' ')[0]) != 0:
                self.validUser = True
                resp = '331 User name okay, need password.'
                self.sendReply(resp)
                break
                
        if not self.validUser:    
            resp = '530 Invalid User.'
            self.sendReply(resp)
            self.validUser = False
    
    def PASS(self,cmd):
        
        # Check if user name is entered
        if self.validUser:
            password = cmd[5:-2]
            pws = open(self.users, 'r').read()

            # Check if password matches user
            for p in pws.split('\n'):

                if len(p.split(' ')[0]) != 0:
                    if password == p.split(' ')[1] and self.user == p.split(' ')[0]:
                        self.isLoggedIn = True
                        resp = '230 User logged in, proceed.'
                        self.sendReply(resp)
                        break

            if not self.isLoggedIn:
                resp = '530 Invalid password for '  + self.user
                self.sendReply(resp)
        else:
            self.notLoggedInMSG()
    
    def QUIT(self,cmd):

        # If the user is logged in, they are logged out
        if self.isLoggedIn:

            self.resetState()
            resp = '221 Logged out'
            self.sendReply(resp)
    
        else:

            resp = '221 Service closing control connection'
            self.sendReply(resp)
            self.isConnected = False
        

    def STRU(self,cmd):
         # Obsolete command
        stru = cmd[5]

        if stru == 'F':
            resp = '200 F.'
        else:
            resp = '504 Command obsolete'

        self.sendReply(resp)

    def MODE(self,cmd):
        
        # Obsolete command
        mode = cmd[5]

        if mode == 'S':
            resp = '200 MODE set to stream.'
        else:
            resp = '504 Command obsolete'

        self.sendReply(resp)

       
    def NOOP(self,cmd):

        # To check if the connection is alive
        resp = '200 OK.'
        self.sendReply(resp)
    
    def TYPE(self,cmd):

        # ASCII or Binary Mode
        mode = cmd[5]
        
        # Confirm I or A
        if mode.upper() == 'I':
            self.mode = mode
            resp = '200 Binary mode.'
            self.sendReply(resp)
        elif mode.upper() == 'A':
            self.mode = mode
            resp = '200 ASCII mode.'
            self.sendReply(resp)
        else:
            # Unknown parameter
            self.paramError(cmd)

    def PWD(self,cmd):
        
        # Cant't print working directory if not looged in
        if self.isLoggedIn:
            
            # The path relative to the root
            tempDir = '/' + self.cwd
            cwd = os.path.relpath(tempDir,'/')
            
            if cwd == '.':
                cwd = '/'
            else:
                cwd = '/' + cwd 
            resp = '257' + ' "' + cwd + '" is the current dir.'
            self.sendReply(resp)

        else:
            self.notLoggedInMSG()

    def CWD(self,cmd):

        if self.isLoggedIn: 
            # Get the directory
            chwd = cmd[4:-2]
         
            # Base directory?
            if chwd == '.' or chwd == '/':
                self.cwd = self.baseWD
                resp = '250 OK.'
                self.sendReply(resp)
            else:
            
                # Consider /dir or dir
                if chwd[0] == '/':
                    chwd = chwd[1:]

                tempCwd = os.path.join(self.cwd, chwd)
            
                # Does the path exist?
                if os.path.exists(tempCwd):
                    self.cwd = tempCwd
                    resp = '250 OK.'
                    self.sendReply(resp)
                else:
                    resp = '550 The system cannot find the file specified.'
                    self.sendReply(resp)
           
        else:
            self.notLoggedInMSG()

    def PASV(self,cmd):
        # Cant't try to establish connection without logging in
        if self.isLoggedIn:
            self.PASVmode = True

            self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.serverSocket.bind((self.serverIP,0))
            self.serverSocket.listen(1)

            ip, port = self.serverSocket.getsockname()
        
            # Condition IP with the RFC959 standard
            ip = ip.split('.')
            ip = ','.join(ip)
        
            # Condition the port with the RFC959 standard
            p1 = math.floor(port/256)
            p2 = port%256
            print('open...\nIP: ' + str(ip) +'\nPORT: '+ str(port))
        
            # Prepare the connection settings for take-off
            resp = '227 Entering Passive Mode (' + str(ip) + ',' + str(p1) + ',' +str(p2) + ').'
            self.sendReply(resp)

        else:
            self.notLoggedInMSG()

    def PORT(self,cmd):
        
        # Cant't try to establish connection without logging in
        if self.isLoggedIn:
    
            # check if Passive Mode
            if self.PASVmode:
                self.serverSocket.close()
                self.PASVmode = False

            # Split the connection settings
            conSettings = cmd[5:].split(',')
        
            # Generate the IP address from the connection settings 
            self.DTPaddr = '.'.join(conSettings[:4])

            # Generate the PORT from the connection settings
            # This is with respect to RFC959
            self.DTPport = ((int(conSettings[4])<<8)) + int(conSettings[5])
            
            print('Connected to :', self.DTPaddr, self.DTPport)
            # Acknowledge
            resp = '200 Got it.'
            self.sendReply(resp)

            self.DTPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.DTPsocket.connect((self.DTPaddr,self.DTPport))

        else:
            self.notLoggedInMSG()

    def startDTPsocket(self):
        
        try:
            if self.PASVmode:
                self.DTPsocket, addr = self.serverSocket.accept()
                print('connect: ', addr)
                
        except socket.error:
            resp = '425 Cannot open Data Connection'
            self.sendReply(resp)

    def stopDTPsocket(self):

        self.DTPsocket.close()
        if self.PASVmode:
            self.serverSocket.close()
    
    def sendData(self, data):

        # Mode of sending?
        if not self.islist and self.mode == 'I':
            self.DTPsocket.send((data))   
        else:
            self.DTPsocket.send((data+'\r\n').encode())

    def LIST(self,cmd):
        
        # Can't list if not logged in
        if self.isLoggedIn:

            resp = '150 File status okay; about to open data connection.'
            self.sendReply(resp)
            print('list: ', self.cwd)
            
            # Ready the socket for data transfer
            self.startDTPsocket()

            # Get each file in the directory
            for l in os.listdir(self.cwd):

                ll = self.toList(os.path.join(self.cwd,l))
                # Send as str/ASCII
                self.islist = True
                self.sendData(ll)
                self.islist = False
            # Done
            self.stopDTPsocket()

            resp = '200 Listing completed.'
            self.sendReply(resp)

        else:
            self.notLoggedInMSG()
    
    def toList(self,l):

        st = os.stat(l)
        fullmode ='rwxrwxrwx'
        mode = ''
        
        # Prep the directory listing with regards to RFC959
        for i in range(9):
            mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
        
        d = (os.path.isdir(l)) and 'd' or '-'
        fhist = time.strftime(' %b %d %H:%M ',time.gmtime(st.st_mtime))
        return d + mode+ '\t1 user'+'\t group \t\t' + str(st.st_size) + '\t' + fhist + '\t' + os.path.basename(l)
    
    def MKD(self,cmd):

        #Can't make new directory if not logged in
        if self.isLoggedIn:
            dirName = os.path.join(self.cwd,cmd[4:-2])
            os.mkdir(dirName)
            resp = '257 Directory created.'
            self.sendReply(resp)
        else:
            self.notLoggedInMSG()

    def RMD(self,cmd):
        
        # Can't delete directory if not logged in
        if self.isLoggedIn:
            
            dirName = os.path.join(self.cwd,cmd[4:-2])

            # Check if specified path exists

            if os.path.exists(dirName):

                # Allow deletion if only deletion is allowed
                if self.allowDelete:
                    os.rmdir(dirName)
                    resp = '250 Directory deleted.'
                    self.sendReply(resp)
                else:
                    resp = '450 Not allowed.'
                    self.sendReply(resp)
            else:
                resp = '550 The system cannot find the file specified.'
                self.sendReply(resp)
        else:
            self.notLoggedInMSG()

      
    def STOR(self,cmd):

        # Cant store files if not logged in
        if self.isLoggedIn:

            # Create file path
            fileName = os.path.join(self.cwd,cmd[5:-2])
            print('Uploading: ', fileName)

            # Upload mode?
            if self.mode == 'I':
                oFile = open(fileName,'wb')
            else:
                oFile = open(fileName, 'w')
        
            resp = '150 Opening data connection.'
            self.sendReply(resp)

            # Ready the socket for upload
            self.startDTPsocket()
            
            # Get the file
            while True:
                data = self.DTPsocket.recv(8192)
                #print(data)
                if not data: 
                    break
                oFile.write(data)
            
            # Done
            self.stopDTPsocket()
            resp = '226 Transfer complete.'
            self.sendReply(resp)
            print('Upload success')
            oFile.close()
            
            
        else:
            self.notLoggedInMSG()

    def RETR(self,cmd):

        # Cant retrieve files if not logged in
        if self.isLoggedIn:
         
            fileName = os.path.join(self.cwd, cmd[5:-2])
            
            # For Filezilla
            if fileName[0] == '/':
                fileName = fileName[1:]
            
            # Check if file exist
            if os.path.exists(fileName):
                print('Downloading :', fileName)
             
                 # Mode?
                if self.mode == 'I':
                    rFile = open(fileName, 'rb')
                else:
                    rFile = open(fileName, 'r')
                    
             
                # Open data connection
                resp = '150 Opening file data connection.'
                self.sendReply(resp)

                data = rFile.read(8192)
                self.startDTPsocket()
                # Send the file
                while data:
                    self.sendData(data)
                    data = rFile.read(8192)
                rFile.close()
                self.stopDTPsocket()
                resp = '226 Transfer complete.'
                self.sendReply(resp)
            else:
                # File does not exist
                resp = '550 The system cannot find the file specified.'
                self.sendReply(resp)
        else:
            self.notLoggedInMSG()

        
class FTPserver(threading.Thread):

    # The lookout class, waits for contact from client

    def __init__(self,usersDB,homeDir,IP,Port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.serverIP = IP
        self.serverPort = Port
        self.sock.bind((self.serverIP, self.serverPort))
        self.usersDB = usersDB
        self.homeDir = homeDir
        threading.Thread.__init__(self)
    
    def run(self):
        self.sock.listen(5)
        while True:
            connectionSocket, addr = self.sock.accept()
            thread = serverThread(connectionSocket, addr,self.usersDB, self.homeDir,self.serverIP,self.serverPort)
            thread.daemon = True
            thread.start()
    
    def stop(self):
        self.sock.close()

def Main():
    
    serverPort = 21

    #! For some reason this now gives localhost only
    #! serverIP =  socket.gethostbyname(socket.gethostname())

    #* New method

    server =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.connect(("8.8.8.8", 80))

    serverIP = server.getsockname()[0]

    # Database for users
    users = './users.txt'

    # Default directory
    homeDir = '../'

    # Make new thread for each new connection

    cThread = FTPserver(users,homeDir,serverIP,serverPort)
    cThread.daemon = True
    cThread.start()

    # Wait for contact
    print('FTP-Application running on', serverIP, ':', serverPort)
    input('Enter to end...\n')
    cThread.stop()
    
    
Main()