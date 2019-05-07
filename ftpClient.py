# client.py

import socket
import math
import sys
import time
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from clientInterface import Ui_MainWindow


class cleintInterface(Ui_MainWindow):

    def __init__(self, ftpClientUI, ftpLogic, statusMessage):
        Ui_MainWindow.__init__(self)
        self.setupUi(ftpClientUI)
        self.ftpLogic = ftpLogic
        self.statusMessage = statusMessage
        self.loginButton.clicked.connect(self.loginButtonClicked)
        self.numFiles = 0
        self.finerList = []
        
        # ------------- Set up tree model for the local host --------------------
      
        self.clientDirectory = QtWidgets.QFileSystemModel()
        self.clientDirectory.setRootPath(QtCore.QDir.rootPath())
        self.localdir.setModel(self.clientDirectory)
        self.localdir.setRootIndex(self.clientDirectory.setRootPath(QtCore.QDir.rootPath()))
        self.pathSelectedItem = QtCore.QDir.rootPath()
        self.localdir.header().resizeSection(0, 150)
		
        # ----------------- End Tree View -----------------------------

    def loginButtonClicked(self):
        self.ftpLogic.initConnection("localhost", int("12000"))
        self.ftpLogic.login("Elias", "aswedeal")
        """ self.ftpLogic.initConnection(self.hostname.text(), int(self.port.text()))
        self.ftpLogic.login(self.username.text(), self.password.text()) """
        self.ftpLogic.setMode('I')
        self.status.setText(st.getStatus())
        self.localdir.setEnabled(True)       
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.getList()
        
        self.getRemoteDirList()
        self.sWindow()
       
        
        #set the number of rows according to the number of files
        self.numFiles = len(self.finerList)
        self.remotedir.setRowCount(self.numFiles)
        self.remotedir.setColumnCount(6)
        self.remotedir.setColumnWidth(0, 230)
        
        #set the headings of the remoted directory view
        self.remotedir.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Filename"))
        self.remotedir.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Last Modified"))
        self.remotedir.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem("Size"))
        self.remotedir.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem("Group"))
        self.remotedir.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem("User"))
        self.remotedir.setHorizontalHeaderItem(5, QtWidgets.QTableWidgetItem("Permissions"))
        
       
         
        #display the file and its characteristic in the remote directory view
        self.generateRemoteTable()
        #check which file is selected
        self.selectedFile()
        self.homeDirButtonClicked()
                
        
    def treeViewClientDirectoryClicked(self, signal):
        self.pathSelectedItem = self.localdir.model().filePath(signal)
        print(self.pathSelectedItem)
    
    def generateRemoteTable(self):
        
        
        self.numFiles = len(self.finerList)
        print(self.numFiles)
        
        for row in range(self.numFiles):
            
            items = self.finerList[row]
            items = items.replace('\t\t', '\t')
            items = items.split("\t") 
                    
            for col in range(6):              
                self.remotedir.setItem(row,col, QtWidgets.QTableWidgetItem(items[5-col]))
        
              
    def getRemoteDirList(self):
        
        for row in range(len(self.finerList)):
            for col in range(6):              
                self.remotedir.setItem(row,col, QtWidgets.QTableWidgetItem(''))
                
        self.finerList.clear()
        
        
        self.dirList = self.ftpLogic.returnDirList()
        
        for element in self.dirList:
            
            temp = element.split("\n")
                   
            if(len(temp) == 2):
                self.finerList.append(temp[0])
            elif(len(temp)> 2):
                s = len(temp) - 1
                
                for i in range(s):
                    self.finerList.append(temp[i])
        
    def sWindow(self):
        
        self.statusWindow.setRowCount(3)
        self.statusWindow.setColumnCount(2)
        self.statusWindow.setColumnWidth(0, 180)
        self.statusWindow.setColumnWidth(1, 630)
        self.statusWindow.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Code"))
        self.statusWindow.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Message"))
    
    def selectedFile(self):
        
        self.remotedir.cellDoubleClicked.connect(self.cell_was_clicked)      
        
    
    def cell_was_clicked(self, row, column):
        item = self.remotedir.item(row,column).text()
        
        if column ==0:
            if item.find('.') != -1:  #If a full stop is found then it is a file
                b = str(item).strip('\r')
                self.downloadFile(b)
                
            else:
                b = str(item).strip('\r')
                self.openDir(b)
                
    def downloadFile(self, fileName):
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.downloadFile(fileName)
        
                
    def openDir(self,folderName):
        self.ftpLogic.changeWD(folderName)
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.getList()
        self.getRemoteDirList()
        self.generateRemoteTable()
        
    def homeDirButtonClicked(self):
        
        self.homedir.clicked.connect(self.toHomeDir)
    
        
    def toHomeDir(self):
        self.ftpLogic.changeWD('/')
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.getList()
        self.getRemoteDirList()
        self.generateRemoteTable()
        
    
class statusMessage:
     
    def __init__(self):
        self.statusMSG = ''
        
    def setStatus(self,msg):
        self.statusMSG  = msg
    
    def getStatus(self):
        return self.statusMSG
        
st = statusMessage()

class FTPclient:
    def __init__(self, clientName):

        self.IPsocket = None
        self.DTPsocket = None
        self.errorResp = False
        self.alive = False
        self.loggedIn = False
        self.user = None
        self.remotedirList = []
        self.clientName = clientName
        
    def initConnection(self, serverIPname, serverIPport):

        self.serverIPname = serverIPname
        self.serverIPport = serverIPport
        #self.clientName = clientName

        self.IPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            self.IPsocket.connect((self.serverIPname, self.serverIPport))
            print(self.IPsocket.recv(1024).decode())

        except:

            errMSG = 'Failed to connect ' + self.serverIPname
            print(errMSG)
            self.errorResp = True
            time.sleep(3)
            return

        self.alive = True
        
        st.setStatus('Connected to Server ;)')
        print(st.getStatus())

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
                st.setStatus('Login Success')
                

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

    def printServerReply(self, resp):
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
        
        self.remotedirList = []
        # Cant't get list if disconnected
        if self.dataConnectionAlive and self.alive:

            cmd = 'LIST'
            self.send(cmd)
            self.printServerReply(self.getServerReply())

            print('\nReceiving Data\n')

            while True:
                # Get the directory list
                data = self.DTPsocket.recv(1024)
                
                self.remotedirList.append(data.decode())

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
    def returnDirList(self):
        return self.remotedirList
    
    def changeWD(self,dir):
        
        cmd = 'CWD ' + dir
        self.send(cmd)
        self.printServerReply(self.getServerReply())


            

def Main():
    clientName = 'localhost'
    import sys
    # Testing ftp servers
    """ Po = [21,12000,21,21,12005]
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
    """ 
    """ time.sleep(1)
    client.startPassiveDTPconnection()
    client.uploadFile('Downloads/bw.jpg')
    time.sleep(1)
    client.startPassiveDTPconnection()
    client.getList() """
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    
    clientName = 'localhost'
    status = statusMessage()
    client = FTPclient(clientName)    
    
    prog = cleintInterface(MainWindow, client, status)

    MainWindow.show()
    sys.exit(app.exec_())

Main()
