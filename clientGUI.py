from PyQt5 import QtCore, QtGui, QtWidgets
from clientInterface import Ui_MainWindow
from ftpClient import  FTPclient
import sys
import os
import socket

class cleintInterface(Ui_MainWindow):

    def __init__(self, ftpClientUI, ftpLogic):
        
        Ui_MainWindow.__init__(self)
        self.setupUi(ftpClientUI)
        self.ftpLogic = ftpLogic
        self.loginButton.clicked.connect(self.loginButtonClicked)
        self.numFiles = 0
        self.finerList = []
        self.r = 0
        self.passiveMode = True
        self.selectedDir = ' '
        
        # ------------- Set up tree model for the local host window--------------------
      
        self.clientDirectory = QtWidgets.QFileSystemModel()
        self.clientDirectory.setRootPath(QtCore.QDir.rootPath())
        self.localdir.setModel(self.clientDirectory)
        self.localdir.setRootIndex(self.clientDirectory.setRootPath(QtCore.QDir.rootPath()))
        self.pathSelectedItem = QtCore.QDir.rootPath()
        self.localdir.header().resizeSection(0, 150)
		
        # ----------------- End Tree View -----------------------------

    def loginButtonClicked(self):
        
        self.pasv.setStyleSheet("background-color: rgb(138, 226, 52);")
        self.ftpLogic.initConnection("127.0.1.1", int("21"))
        self.ftpLogic.login("Elias", "aswedeal")
        #self.ftpLogic.initConnection(self.hostname.text(), int(self.port.text()))
        #self.ftpLogic.login(self.username.text(), self.password.text())
        self.generateLogTable()
        self.statusMSG()
        self.ftpLogic.setMode('I')
        self.localdir.setEnabled(True)
        
        if self.passiveMode:       
            self.ftpLogic.startPassiveDTPconnection()
        else:
            self.ftpLogic.startActiveConnection()
            
        self.ftpLogic.getList()
        self.getRemoteDirList()
    
        # Set the number of rows according to the number of files
        self.numFiles = len(self.finerList)
        
        #--------------------Set the window for the remote directory----------------
        self.remoteWindow()
        self.logWindow()
        
        self.generateRemoteTable()
        # Check which file is selected on the remoted directory window
        self.selectedFile()
        # Check which file is selected on the local directory window
        self.selectedLocalFile()    
        # Events handlers when buttons are pressed
        self.noopButtonClicked()
        self.homeDirButtonClicked()
        self.logoutButtonClicked()
        self.activeButtonClicked()
        self.passiveButtonClicked()
        self.makeDirButtonClicked()
        # self.oneClickselectedFile()
        #self.removeDirButtonClicked()
        
    def remoteWindow(self):
        self.remotedir.setRowCount(self.numFiles)
        self.remotedir.setColumnCount(6)
        self.remotedir.setColumnWidth(0, 230)
        self.remotedir.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Filename"))
        self.remotedir.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Last Modified"))
        self.remotedir.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem("Size"))
        self.remotedir.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem("Group"))
        self.remotedir.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem("User"))
        self.remotedir.setHorizontalHeaderItem(5, QtWidgets.QTableWidgetItem("Permissions"))
          
    def logWindow(self):
        self.statusWindow.setColumnCount(1)
        self.statusWindow.setColumnWidth(0, 820)
        self.statusWindow.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Latest Session Log"))
    
    def passiveButtonClicked(self):
        self.pasv.clicked.connect(self.pasvMode)
    
    def pasvMode(self):
        self.passiveMode = True
        self.pasv.setStyleSheet("background-color: rgb(138, 226, 52);")
        self.active.setStyleSheet("")
    
    def activeButtonClicked(self):
        self.active.clicked.connect(self.actMode)
    
    def actMode(self):
        self.passiveMode = False
        self.active.setStyleSheet("background-color: rgb(138, 226, 52);")
        self.pasv.setStyleSheet("")
    
    def removeDirButtonClicked(self):
        self.remotedir.clicked.connect(self.removeDirectory)
        
    def removeDirectory(self):
        self.remotedir.cellClicked.connect(self.cellClickedOnce_)
        self.ftpLogic.remDir(self.selectedDir)
        self.statusMSG()
        self.generateLogTable()
    
    def makeDirButtonClicked(self):
        self.makeDir.clicked.connect(self.mkDir)
        
    def mkDir(self):
        
        self.ftpLogic.makeDir(self.dirName.text())
        self.statusMSG()
        self.generateLogTable()
        
                 
   
    def statusMSG(self):
        self.status.setText(self.ftpLogic.getStatus())
    
    def generateLogTable(self):
        
        self.statusWindow.setRowCount(len(self.ftpLogic.getComm()))
        
        for row in range(len(self.ftpLogic.getComm())):
                # Place files on the GUI              
                self.statusWindow.setItem(row,0, QtWidgets.QTableWidgetItem(self.ftpLogic.getComm()[len(self.ftpLogic.getComm())-row -1]))
                
        self.ftpLogic.clearComm()
                               
    def treeViewClientDirectoryClicked(self, signal):
        
        self.pathSelectedItem = self.localdir.model().filePath(signal)
        print(self.pathSelectedItem)
        self.statusMSG()
        self.generateLogTable()
        
        
    # Display the file and folders and its characteristic in the remote directory window
    def generateRemoteTable(self):
             
        self.numFiles = len(self.finerList)
        
        for row in range(self.numFiles):
            
            items = self.finerList[row]
            items = items.replace('\t\t', '\t')
            items = items.split("\t") 
                    
            for col in range(6):
                # Place files on the GUI              
                self.remotedir.setItem(row,col, QtWidgets.QTableWidgetItem(items[5-col]))
    
    """ Gets the files and folders on server side and decomposes the result
    so that it can be presented in a table format on the GUI """                     
    def getRemoteDirList(self):
        
        for row in range(len(self.finerList)):
            for col in range(6):              
                self.remotedir.setItem(row,col, QtWidgets.QTableWidgetItem(''))
        
        # Clear the List that stores files that are on the server everytime a directory is changed       
        self.finerList.clear()       
        self.dirList = self.ftpLogic.returnDirList()
        
        for element in self.dirList:
            
            temp = element.split("\n")
                   
            if(len(temp) == 2):
                # Avoid storing the null element at postion 1 or the arrray
                self.finerList.append(temp[0])
            elif(len(temp)> 2):
                s = len(temp) - 1
                
                for i in range(s):
                    # Store the new files that are in the new directory
                    self.finerList.append(temp[i])
               
    def selectedLocalFile(self):
        
        self.localdir.doubleClicked.connect(self.test)
        
        
    def test(self, signal):
        
        file_path= self.clientDirectory.filePath(signal)
        
        if file_path.find('.') > 0:
            
            self.uploadFile(file_path)
              
    
    def uploadFile(self, filePath):
        
        if self.passiveMode:       
            self.ftpLogic.startPassiveDTPconnection()
        else:
            self.ftpLogic.startActiveConnection()
            
        self.ftpLogic.uploadFile(filePath)
        self.statusMSG()
        self.generateLogTable() 
        
   # def oneClickselectedFile(self):
       # self.remotedir.cellClicked.connect(self.cellClickedOnce_)

        
    def cellClickedOnce_(self, row, column):
        
        self.selectedDir = self.remotedir.item(row,column).text().strip('\r')
        
        
    def selectedFile(self):   
            
        self.remotedir.cellDoubleClicked.connect(self.cellDoubleClicked_)
        self.statusMSG()
        self.generateLogTable()   
        
    def cellDoubleClicked_(self, row, column):
        
        item = self.remotedir.item(row,column).text()
        
        if column ==0:
            # Identify element with a . as a file else it is a folder
            if item.find('.') != -1:  
                b = str(item).strip('\r')
                self.downloadFile(b)
                
            else:
                b = str(item).strip('\r')
                self.openDir(b)
                
    def downloadFile(self, fileName):
        
        if self.passiveMode:       
            self.ftpLogic.startPassiveDTPconnection()
        else:
            self.ftpLogic.startActiveConnection()
            
        self.ftpLogic.downloadFile(fileName)
        self.statusMSG()
        self.generateLogTable()
        
    # open a folder and show its contents  on the GUI            
    def openDir(self,folderName):
        
        self.ftpLogic.changeWD(folderName)
        
        if self.passiveMode:       
            self.ftpLogic.startPassiveDTPconnection()
        else:
            self.ftpLogic.startActiveConnection()
            
        self.ftpLogic.getList()
        self.getRemoteDirList()
        self.generateRemoteTable()
        self.statusMSG()
        self.generateLogTable()
        
    def homeDirButtonClicked(self):
        
        self.homedir.clicked.connect(self.toHomeDir)
        self.statusMSG()
        self.generateLogTable()
    
    # Return to the home directory on remote host   
    def toHomeDir(self):
        
        self.ftpLogic.changeWD('/')
        
        if self.passiveMode:       
            self.ftpLogic.startPassiveDTPconnection()
        else:
            self.ftpLogic.startActiveConnection()
            
        self.ftpLogic.getList()
        self.getRemoteDirList()
        self.generateRemoteTable()
        self.statusMSG()
        self.generateLogTable()
    
    def logoutButtonClicked(self):

        self.logoutButton.clicked.connect(self.Logout)
               
    def Logout(self):
        
        self.ftpLogic.logout()
        self.ftpLogic.logout()
        self.statusMSG()
        self.generateLogTable()
    
    def noopButtonClicked(self):
        
        self.noop.clicked.connect(self.nooP)
               
    def nooP(self):
        
        self.ftpLogic.checkConnection()
        self.statusMSG()
        self.generateLogTable()


def Main():
    
    clientName = socket.gethostbyname(socket.gethostname())
   
    # Testing ftp servers
    
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    
    client = FTPclient(clientName)   
    
    application = cleintInterface(MainWindow, client)

    MainWindow.show()
    sys.exit(app.exec_())

Main()
