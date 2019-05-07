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
        #self.statusMessage = statusMessage
        self.loginButton.clicked.connect(self.loginButtonClicked)
        self.numFiles = 0
        self.finerList = []
        self.r = 0
        
        # ------------- Set up tree model for the local host window--------------------
      
        self.clientDirectory = QtWidgets.QFileSystemModel()
        self.clientDirectory.setRootPath(QtCore.QDir.rootPath())
        self.localdir.setModel(self.clientDirectory)
        self.localdir.setRootIndex(self.clientDirectory.setRootPath(QtCore.QDir.rootPath()))
        self.pathSelectedItem = QtCore.QDir.rootPath()
        self.localdir.header().resizeSection(0, 150)
		
        # ----------------- End Tree View -----------------------------

    def loginButtonClicked(self):
        
        self.ftpLogic.initConnection("127.0.1.1", int("21"))
        self.ftpLogic.login("Elias", "aswedeal")
        #self.ftpLogic.initConnection(self.hostname.text(), int(self.port.text()))
        #self.ftpLogic.login(self.username.text(), self.password.text())
        self.statusMSG()
        self.ftpLogic.setMode('I')
        self.localdir.setEnabled(True)       
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.getList()
        self.getRemoteDirList()
    
        # Set the number of rows according to the number of files
        self.numFiles = len(self.finerList)
        
        #--------------------Set the window for the remote directory----------------
        self.remotedir.setRowCount(self.numFiles)
        self.remotedir.setColumnCount(6)
        self.remotedir.setColumnWidth(0, 230)
        self.remotedir.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Filename"))
        self.remotedir.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Last Modified"))
        self.remotedir.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem("Size"))
        self.remotedir.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem("Group"))
        self.remotedir.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem("User"))
        self.remotedir.setHorizontalHeaderItem(5, QtWidgets.QTableWidgetItem("Permissions"))
        
        self.generateRemoteTable()
        # Check which file is selected on the remoted directory window
        self.selectedFile()
        # Check which file is selected on the local directory window
        self.selectedLocalFile()    
        # Events handlers when buttons are pressed
        self.noopButtonClicked()
        self.homeDirButtonClicked()
        self.logoutButtonClicked()
    
    def statusMSG(self):
        self.status.setText(self.ftpLogic.getStatus())
                               
    def treeViewClientDirectoryClicked(self, signal):
        
        self.pathSelectedItem = self.localdir.model().filePath(signal)
        print(self.pathSelectedItem)
        self.statusMSG()
        
        
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
        
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.uploadFile(filePath)
        self.statusMSG() 
        
           
    def selectedFile(self):   
            
        self.remotedir.cellDoubleClicked.connect(self.cell_was_clicked)
        self.statusMSG()   
        
    def cell_was_clicked(self, row, column):
        
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
        
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.downloadFile(fileName)
        self.statusMSG()
        
    # open a folder and show its contents  on the GUI            
    def openDir(self,folderName):
        
        self.ftpLogic.changeWD(folderName)
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.getList()
        self.getRemoteDirList()
        self.generateRemoteTable()
        self.statusMSG()
        
    def homeDirButtonClicked(self):
        
        self.homedir.clicked.connect(self.toHomeDir)
        self.statusMSG()
    
    # Return to the home directory on remote host   
    def toHomeDir(self):
        
        self.ftpLogic.changeWD('/')
        self.ftpLogic.startPassiveDTPconnection()
        self.ftpLogic.getList()
        self.getRemoteDirList()
        self.generateRemoteTable()
    
    def logoutButtonClicked(self):

        self.logoutButton.clicked.connect(self.Logout)
               
    def Logout(self):
        
        self.ftpLogic.logout()
        self.ftpLogic.logout()
        self.statusMSG()
    
    def noopButtonClicked(self):
        
        self.noop.clicked.connect(self.nooP)
               
    def nooP(self):
        
        self.ftpLogic.checkConnection()
        self.statusMSG()


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
