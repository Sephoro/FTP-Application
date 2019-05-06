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
        
        # ------------- Set up tree model for the local host --------------------
      
        self.clientDirectory = QtWidgets.QFileSystemModel()
        self.clientDirectory.setRootPath(QtCore.QDir.rootPath())
        self.localdir.setModel(self.clientDirectory)
        self.localdir.setRootIndex(self.clientDirectory.setRootPath(QtCore.QDir.rootPath()))
        self.pathSelectedItem = QtCore.QDir.rootPath()
        self.localdir.header().resizeSection(0, 300)
		
        # ----------------- End Tree View -----------------------------

    def loginButtonClicked(self):
        self.ftpLogic.initConnection(self.hostname.text(), int(self.port.text()))
        self.ftpLogic.login(self.username.text(), self.password.text())
        self.status.setText(st.getStatus())
        self.localdir.setEnabled(True)       
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.getList()
        
        self.remotedir.setRowCount(1)
        self.remotedir.setColumnCount(4)
        
        self.remotedir.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Filename"))
        self.remotedir.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Size"))
        self.remotedir.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem("Last Modified"))
        self.remotedir.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem("Permissions"))
        
    def treeViewClientDirectoryClicked(self, signal):
        self.pathSelectedItem = self.localdir.model().filePath(signal)
        print(self.pathSelectedItem)
 
 
class statusMessage:
     
    def __init__(self):
        self.statusMSG = ''
        
    def setStatus(self,msg):
        self.statusMSG  = msg
    
    def getStatus(self):
        return self.statusMSG
        
st = statusMessage()

class FTPclient:
    def __init__(self):

        self.IPsocket = None
        self.DTPsocket = None
        self.errorResp = False
        self.alive = False
        self.loggedIn = False
        self.user = None
        
    def initConnection(self, serverIPname, serverIPport):

        self.serverIPname = serverIPname
        self.serverIPport = serverIPport

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
            self.printServerReply(self.getServerReply())
            self.DTPsocket.close()
    
    def changeWD(self,dir):
        
        cmd = 'CWD ' + dir
        self.send(cmd)
        self.printServerReply(self.getServerReply())


            

def Main():
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
    client = FTPclient(serverName,serverIP)
    client.initConnection()
    client.login(userName, password)
    client.startPassiveDTPconnection()
    client.setMode('I')
    client.getList()
    time.sleep(1)
    client.changeWD('HOME')
    client.startPassiveDTPconnection()
    client.getList()
    client.startPassiveDTPconnection()
    client.downloadFile('EIE.png')
    client.login(userName, password) """
# client.startPassiveDTPconnection()
# client.getList()

#serverPort = 12000

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    
    status = statusMessage()
    client = FTPclient()    
    
    prog = cleintInterface(MainWindow, client, status)

    MainWindow.show()
    sys.exit(app.exec_())

Main()
