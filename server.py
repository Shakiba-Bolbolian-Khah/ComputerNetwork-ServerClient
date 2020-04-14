from socket import *
import json
import _thread
import os
import shutil
import datetime

CONFIG_ADD = "./config.json"
NORMAL = "normal"
ADMIN = "admin"
MAX_LENGTH = 2048

logger = None

class Accountant:
    def __init__(self, size, alert, threshold):
        self.size = size
        self.alert = alert
        self.threshold = threshold
        self.hasEmailSent = False

    def checkStatus(self, response, expectedStatus):
        status = int(response.decode().split()[0])
        if status != expectedStatus:
            return False
        else:
            return True

    def addLog(self, msg):
        global logger
        if logger:
            logger.log(msg)

    def sendEmail(self, email):
        commands = [('HELO 127.0.0.1\n', 250), ('MAIL FROM:<hsazarmsa@ut.ac.ir>\n', 250), ('AUTH LOGIN\n', 334),
                    ('aHNhemFybXNhCg==\n', 334), ('SGVuYTc4KzgxMDE5NjQwOA==\n', 235),('RCPT TO:<' + email + '>\n', 250) ,
                    ('DATA\n', 354), ('Subject:traffic alarm\nyour traffic is lower than threshold\n.\n', 250), 
                    ('QUIT\n', 221)]
        emailSocket = socket(AF_INET, SOCK_STREAM)
        emailSocket.connect(('mail.ut.ac.ir', 25))
        response = emailSocket.recv(500)
        if not self.checkStatus(response, 220):
            return
        for command,expectedStatus in commands:
            emailSocket.send(command.encode())
            response = emailSocket.recv(500)
            if not self.checkStatus(response, expectedStatus):
                return
        emailSocket.close()
        self.addLog('Email to ' + email + ' has sent.')
        self.hasEmailSent = True

    def updateRemainedSize(self, decreasedSize, email):
        self.size -= decreasedSize
        if self.size < self.threshold and not self.hasEmailSent:
            self.sendEmail(email)


    def hasEnoughTraffic(self, size):
        if self.size < size:
            return False
        return True

class User:
    def __init__(self, userName, password):
        self.userName = userName
        self.password = password
        self.accountant = None
        self.email = ""
        self.role = NORMAL

    def setAccountant(self, accountant):
        self.accountant = accountant

    def setEmail(self, email):
        self.email = email

    def setRole(self, role = ADMIN):
        self.role = role

    def updateRemainedSize(self, decreasedSize):
        if self.accountant:
            self.accountant.updateRemainedSize(decreasedSize, self.email)

    def hasEnoughTraffic(self, size):
        if self.accountant:
            return self.accountant.hasEnoughTraffic(size)
        else:
            return True

    def __str__(self):
        print (self.userName, self.password, self.role, self.email, self.accountant.size, self.accountant.alert, self.accountant.threshold)
        return self.userName



class Logger:
    def __init__(self, fileName):
        if fileName[:2] == './':
            fileName = fileName[2:]
        self.fileName = str(os.path.dirname(os.path.realpath(__file__))) + '/' + fileName
    def log(self, msg):
        newLogging = str(datetime.datetime.now()) + " : " + msg + "\n"
        with open(self.fileName, "a") as f:
            f.write(newLogging)



class DownloadManager:
    def __init__(self, dataPort, adminFiles):
        self.adminFiles = adminFiles
        self.dataPort = dataPort
        
    def uploadError(self, portNum):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1)
        self.s.bind(("", self.dataPort))
        self.s.connect(('127.0.0.1', portNum))
        errorData = "0\n"
        self.s.sendall(errorData.encode())
        self.s.close()

    def uploadList(self, data, portNum, user):
        if not data:
            data = '\n'
        if user.hasEnoughTraffic(len(data.encode('utf-8'))):
            self.s = socket(AF_INET, SOCK_STREAM)
            self.s.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1)
            self.s.bind(("", self.dataPort))
            self.s.connect(('127.0.0.1',portNum))
            sendBytes = self.s.sendall(data.encode())
            self.s.close()
            user.updateRemainedSize(len(data.encode('utf-8')))
            return 'ok'
        else:
            self.uploadError(portNum)
            return "425 Can't open data connection."

    def uploadFile(self, fileName, portNum, user):
        fileData = open(fileName, 'rb').read()
        fileData = (str(len(fileData)) + "\n").encode() + fileData
        if user.hasEnoughTraffic(len(fileData)):
            if fileName in self.adminFiles and user.role != ADMIN:
                self.uploadError(portNum)
                return "550 File unavailable."
            self.s = socket(AF_INET, SOCK_STREAM)
            self.s.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1)
            self.s.bind(("", self.dataPort))
            self.s.connect(('127.0.0.1', portNum))
            self.s.sendall(fileData)
            self.s.close()
            user.updateRemainedSize(len(fileData))
            return "ok"
        else:
            self.uploadError(portNum)
            return "425 Can't open data connection."


class Server:
    def __init__(self, users, dataPort, adminFiles):
        self.users = users
        self.loggedInUser = {}
        self.dm = DownloadManager(dataPort, adminFiles)

    def addLog(self, msg):
        global logger
        if logger:
            logger.log(msg)

    def isUserNameValid( self, userName):
        if userName in self.users:
            return True
        return False

    def isUserLoggedIn( self, portNum):
        if portNum in self.loggedInUser:
            return True
        return False

    def addLoggedInUser( self, portNum, userName, password):
        if userName not in self.users or  self.users[userName].password != password :
            return "430 Invalid username or password."
        self.loggedInUser[portNum] = self.users[userName]
        self.addLog(userName + " logged in!")
        return "230 User logged in, proceed."

    def sendLoginError(self):
        return "332 Need account for login."

    def send500Error(self, msg):
        return "500 Error: "+msg

    def handlePWD(self, portNum):
        if(self.isUserLoggedIn(portNum)):
            res = "257 " + os.path.abspath(os.getcwd())
            return res
        else:
            return self.sendLoginError()
    
    def handleMKFile(self, portNum, fileName):
        if(self.isUserLoggedIn(portNum)):
            if not os.path.exists(fileName):
                os.mknod(fileName)
                self.addLog(self.loggedInUser[portNum].userName + " created file with name: " + fileName + "!")
                return "257 "+fileName+" created."
            else:
                return self.send500Error("File "+fileName+" already exists!")
        else:
            return self.sendLoginError()

    def handleMKDir(self, portNum, dirName):
        if(self.isUserLoggedIn(portNum)):
            try:
                os.mkdir(dirName)
            except OSError:
                return self.send500Error("Creation of the directory "+dirName+" failed!")
            else:
                self.addLog(self.loggedInUser[portNum].userName + " created directory with name: " + dirName + "!")
                return "257 "+dirName+" created." 
        else:
            return self.sendLoginError()

    def handleDeleteDir(self, portNum, dirName):
        if(self.isUserLoggedIn(portNum)):
            try:
                shutil.rmtree(dirName)
            except OSError:
                return self.send500Error("Deletion of the directory "+dirName+" failed!")
            else:
                self.addLog(self.loggedInUser[portNum].userName + " deleted directory with name: " + dirName + "!")
                return "250 "+dirName+" deleted." 
        else:
            return self.sendLoginError()

    def handleDeleteFile(self, portNum, fileName):
        if(self.isUserLoggedIn(portNum)):
            if os.path.exists(fileName) and os.path.isfile(fileName):
                os.remove(fileName)
                self.addLog(self.loggedInUser[portNum].userName + " deleted file with name: " + fileName + "!")
                return "250 "+fileName+" deleted."
            else:
                return self.send500Error("File "+fileName+" does not exist!")
        else:
            return self.sendLoginError()

    def handleGetList(self, portNum, dataPort):
        if(self.isUserLoggedIn(portNum)):
            fileList = ""
            files = [f for f in os.listdir('.') if os.path.isfile(f)]
            for f in files:
                fileList += f + "\n"
            uploadStatus = self.dm.uploadList(fileList.rstrip(), int(dataPort), self.loggedInUser[portNum])
            if uploadStatus == 'ok':
                return '226 List transfer done.'
            else:
                return uploadStatus
        else:
            self.dm.uploadError(int(dataPort))
            return self.sendLoginError()

    def handleCWD(self, portNum, path):
        if(self.isUserLoggedIn(portNum)):
            try:
                os.chdir(path)
                return '250 Successful Change.'
            except OSError as e:
                return self.send500Error(str(e))
        else:
            return self.sendLoginError()

    def handleDL(self, portNum, dataPort, fileName):
        if(self.isUserLoggedIn(portNum)):
            if os.path.exists(fileName) and os.path.isfile(fileName):
                uploadStatus = self.dm.uploadFile(fileName, int(dataPort), self.loggedInUser[portNum])
                if uploadStatus == "ok":
                    self.addLog(self.loggedInUser[portNum].userName + " downloaded file with name: " + fileName + "!")
                    return '226 Successful Download.'
                else:
                    return uploadStatus
            else:
                self.dm.uploadError(int(dataPort))
                return self.send500Error("File "+fileName+" does not exist!")
        else:
            self.dm.uploadError(int(dataPort))
            return self.sendLoginError()

    def handleHelp(self, portNum):
        if(self.isUserLoggedIn(portNum)):
            helpData = "421\n" + open("help.txt", 'r').read()
            return(helpData)
        else:
            return self.sendLoginError()

    def handleQuit(self, portNum):
        if(self.isUserLoggedIn(portNum)):
            self.addLog(self.loggedInUser[portNum].userName + " logged out!")
            del self.loggedInUser[portNum]
            return "221 Successful Quit."
        else:
            return self.sendLoginError()








class CommandParser:

    def __init__(self, users, dataPort, adminFiles):
        self.requestedUsers = {}
        self.server = Server(users, dataPort, adminFiles)
        self.initialDir = os.path.dirname(os.path.realpath(__file__))

    def handleUsername(self, portNum, userName):
        if(self.server.isUserNameValid(userName)):
            self.requestedUsers[portNum] = userName
            return "331 User name okay, need password."
        else:
            return "430 Invalid username or password."

    def handlePassword(self, portNum, password):
        if portNum not in self.requestedUsers:
            return "503 Bad sequence of commands."
        else:
            username = self.requestedUsers[portNum]
            del self.requestedUsers[portNum]
            return self.server.addLoggedInUser(portNum, username, password)


    def parseCmd(self, client, portNum, cmd):
        splitedCmd = cmd.decode().split()

        if splitedCmd[0] == "USER" and len(splitedCmd) == 2:
            client.send(self.handleUsername(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "PASS" and len(splitedCmd) == 2:
            client.send(self.handlePassword(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "PWD" and len(splitedCmd) == 1:
            client.send(self.server.handlePWD(portNum).encode())

        elif splitedCmd[0] == "MKD" and splitedCmd[1] == "-i" and len(splitedCmd) == 3:
            client.send(self.server.handleMKFile(portNum, splitedCmd[2]).encode())

        elif splitedCmd[0] == "MKD" and len(splitedCmd) == 2:
            client.send(self.server.handleMKDir(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "RMD" and splitedCmd[1] == "-f" and len(splitedCmd) == 3:
            client.send(self.server.handleDeleteDir(portNum, splitedCmd[2]).encode())

        elif splitedCmd[0] == "RMD" and len(splitedCmd) == 2:
            client.send(self.server.handleDeleteFile(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "LIST" and len(splitedCmd) == 2:
            client.send(self.server.handleGetList(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "CWD" and 1 <= len(splitedCmd) <= 2:
            path = splitedCmd[1] if len(splitedCmd) == 2 else self.initialDir
            client.send(self.server.handleCWD(portNum, path).encode())

        elif splitedCmd[0] == "DL" and len(splitedCmd) == 3:
            client.send(self.server.handleDL(portNum, splitedCmd[2], splitedCmd[1]).encode())

        elif splitedCmd[0] == "HELP" and len(splitedCmd) == 1:
            client.send(self.server.handleHelp(portNum).encode())

        elif splitedCmd[0] == "QUIT" and len(splitedCmd) == 1:
            client.send(self.server.handleQuit(portNum).encode())

        else:
            client.send("501 Syntax error in parameters or arguments.".encode())
    

    





class API :

    def __init__(self):
        self.adminFiles = []
        self.jsonParser()
        self.cmdParser = CommandParser(self.users, self.dataPort, self.adminFiles)
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.bind(("",self.cmdPort))
        self.s.listen(10)
        print('listeninig...')
        self.listen()

    def handleRequest(self,  client, address):
        try:
            while(True):
                cmd = client.recv(MAX_LENGTH)
                self.cmdParser.parseCmd(client, address[1], cmd)
        except Exception as e:
            client.close()
            print(e)

    def listen(self):
        while(True):
            c,a = self.s.accept()
            t = _thread.start_new_thread(self.handleRequest,(c,a))


    def jsonParser(self):
        configs = json.load(open(CONFIG_ADD))
        self.cmdPort = configs["commandChannelPort"]
        self.dataPort = configs["dataChannelPort"]
        self.users = {}
        for user in configs["users"]:
            self.users[user["user"]] = User(user["user"], user["password"])
        if(configs["accounting"]["enable"]):
            threshold = configs["accounting"]["threshold"]
            for user in configs["accounting"]["users"]:
                size = int(user["size"])
                email = user["email"]
                alert = user["alert"]
                self.users[user["user"]].setAccountant(Accountant(size, alert, threshold))
                self.users[user["user"]].setEmail(email)

        if(configs["logging"]["enable"]):
            global logger 
            logger = Logger(configs["logging"]["path"])

        if(configs["authorization"]["enable"]):
            for admin in configs["authorization"]["admins"]:
                self.users[admin].setRole()
            self.adminFiles = configs["authorization"]["files"]

api = API()