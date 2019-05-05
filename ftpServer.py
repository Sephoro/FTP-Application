import socket
import os
import time
import threading
import math


serverPort = 12000
serverIP = 'localhost' #socket.gethostbyname(socket.gethostname())

allow_delete = False

class serverThread(threading.Thread):
    def __init__(self, conn, addr,usersDB, currDir):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.baseWD = currDir
        self.cwd = self.baseWD
        self.rest = False
        self.PASVmode = False
        self.isLoggedIn = False
        self.users = usersDB
        self.validUser = False
        self.isConnected = True
    
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
        #TODO
        resp = '200 F.'
        self.sendReply(resp)
       
    def NOOP(self,cmd):
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
            print(tempDir)
            cwd = os.path.relpath(tempDir,'/')
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
            self.serverSocket.bind((serverIP,0))
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
        
            # Acknowledge
            resp = '200 Got it.'
            self.sendReply(resp)

        else:
            self.notLoggedInMSG()

    def startDTPsocket(self):
        
        try:
            if self.PASVmode:
                self.DTPsocket, addr = self.serverSocket.accept()
                print('connect: ', addr)
            else:
                self.DTPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.DTPsocket.connect((self.DTPaddr,self.DTPport))
            resp = ' 225 Data Connection open'
            self.sendReply(resp)
        except socket.error:
            resp = '425 Cannot open Data Connection'
            self.sendReply(resp)

    def stopDTPsocket(self):
        self.DTPsocket.close()
        if self.PASVmode:
            self.serverSocket.close()
    
    def sendData(self, data):
        self.DTPsocket.send((data+'\r\n').encode())

    def LIST(self,cmd):
        resp = '150 File status okay; about to open data connection.'
        self.sendReply(resp)
        print('list: ', self.cwd)
        self.startDTPsocket()
        for l in os.listdir(self.cwd):
            ll = self.toList(os.path.join(self.cwd,l))
            self.sendData(ll)
        self.stopDTPsocket()
    
    def toList(self,l):
        st = os.stat(l)
        fullmode ='rwxrwxrwx'
        mode = ''
        for i in range(9):
            mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
        
        d = (os.path.isdir(l)) and 'd' or '-'
        fhist = time.strftime(' %b %d %H:%M ',time.gmtime(st.st_mtime))
        return d + mode + '1 user group ' + str(st.st_size) + fhist + os.path.basename(l)
    
    def MKD(self,cmd):
        dirName = os.path.join(self.cwd,cmd[4:-2])
        os.mkdir(dirName)
        resp = '257 Directory created.'
        self.sendReply(resp)

    def RMD(self,cmd):
        dirName = os.path.join(self.cwd,cmd[4:-2])
        if allow_delete:
            os.rmdir(dirName)
            resp = '250 Directory deleted.'
            self.sendReply(resp)
        else:
            resp = '450 Not allowed.'
            self.sendReply(resp)
    
    def REST(self,cmd):
        self.pos = int(cmd[5:-2])
        self.rest = True
        resp = '250 File position reseted.'
        self.sendReply(resp)
        
    def STOR(self,cmd):
        
        fileName = os.path.join(self.cwd,cmd[5:-2])
        print('Uploading: ', fileName)

        if self.mode == 'I':
            oFile = open(fileName,'wb')
        else:
            oFile = open(fileName, 'w')
        
        resp = '150 Opening data connection.'
        self.sendReply(resp)
        self.startDTPsocket()

        while True:
            data = self.DTPsocket.recv(1024).decode()
            if not data: break
            
            oFile.write(data)

        oFile.close()
        self.stopDTPsocket()
        resp = '226 Transfer complete.'
        self.sendReply(resp)

    def RETR(self,cmd):
        fileName = os.path.join(self.cwd, cmd[5:-2])
        print('Downloading :', fileName)

        if self.mode == 'I':
            rFile = open(fileName, 'rb')
        else:
            rFile = open(fileName, 'r')
        
        resp = '150 Opening data connection.'
        self.sendReply(resp)
        if self.rest:
            rFile.seek(self.pos)
            self.rest = False
        
        data = rFile.read(1024)
        self.startDTPsocket()
        while data:
            self.sendData(data)
            data = rFile.read(1024)
        rFile.close()
        self.stopDTPsocket()
        resp = '226 Transfer complete.'
        self.sendReply(resp)
        
class FTPserver(threading.Thread):
    def __init__(self,usersDB,homeDir):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind((serverIP, serverPort))
        self.usersDB = usersDB
        self.homeDir = homeDir
        threading.Thread.__init__(self)
    
    def run(self):
        self.sock.listen(5)
        while True:
            connectionSocket, addr = self.sock.accept()
            thread = serverThread(connectionSocket, addr,self.usersDB, self.homeDir)
            thread.daemon = True
            thread.start()
    
    def stop(self):
        self.sock.close()

#if __name__ == '__main___':'
users = './users.txt'
homeDir = 'HOME'
cThread = FTPserver(users,homeDir)
cThread.daemon = True
cThread.start()
print('On', serverIP, ':', serverPort)
input('Enter to end...\n')
cThread.stop()