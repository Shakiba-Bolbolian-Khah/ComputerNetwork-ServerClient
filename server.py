from socket import *
import json
import _thread
import os
import shutil
# import pathlib

CONFIG_ADD = "./config.json"
NORMAL = "normal"
ADMIN = "admin"
MAX_LENGTH = 2048

class Accountant:
    def __init__(self, size, alert, threshold):
        self.size = size
        self.alert = alert
        self.threshold = threshold

    def updateRemainedSize(self, decreasedSize):
        # ToDo: size must check and if it gets lower than threshold send email
        self.size -= decreasedSize


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
        self.accountant.updateRemainedSize(decreasedSize)

    def __str__(self):
        print (self.userName, self.password, self.role, self.email, self.accountant.size, self.accountant.alert, self.accountant.threshold)
        return self.userName



class Logger:
    def __init__(self, fileName):
        self.logFile = open(fileName,"a")



class DownloadManager:
    def __init__(self, dataPort):
        self.dataPort = dataPort
        # self.s = socket(AF_INET, SOCK_STREAM)
        # self.s.bind(("", dataPort))

    def uploadList(self, data, portNum, user):
        if True:
            self.s = socket(AF_INET, SOCK_STREAM)
            self.s.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1)
            self.s.bind(("", self.dataPort))
            self.s.connect(('127.0.0.1',portNum))
            sendBytes = self.s.sendall(data.encode())
            self.s.close()
            # user.updateRemainedSize(len(data))
            return True
        else:
            return False


class Server:
    def __init__(self, users, dataPort):
        self.users = users
        self.loggedInUser = {}
        self.dm = DownloadManager(dataPort)

    def isUserNameValid( self, userName):
        print(userName)
        if userName in self.users:
            return True
        return False

    def isUserLoggedIn( self, portNum):
        if portNum in self.loggedInUser:
            return True
        return False

    def addLoggedInUser( self, portNum, userName, password):
        # print(self.users)
        if userName not in self.users or  self.users[userName].password != password :
            return "430 Invalid username or password."
        self.loggedInUser[portNum] = self.users[userName]
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
                return "250 "+dirName+" deleted." 
        else:
            return self.sendLoginError()

    def handleDeleteFile(self, portNum, fileName):
        if(self.isUserLoggedIn(portNum)):
            if os.path.exists(fileName) and os.path.isfile(fileName):
                os.remove(fileName)
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
                # os.path.isfile(os.path.join(somedir, f))
            uploadStatus = self.dm.uploadList(fileList.rstrip(), int(dataPort), self.loggedInUser[portNum])
            if uploadStatus:
                return '226 List transfer done.'
            else:
                return self.send500Error('List cound not uploas')
        else:
            return self.sendLoginError()





class CommandParser:

    def __init__(self, users, dataPort):
        self.requestedUsers = {}
        self.server = Server(users, dataPort)

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
            return self.server.addLoggedInUser(portNum, self.requestedUsers[portNum], password)


    def parseCmd(self, client, portNum, cmd):
        print(cmd)
        splitedCmd = cmd.decode().split()
        print(splitedCmd)

        if splitedCmd[0] == "USER" and len(splitedCmd) == 2:
            client.send(self.handleUsername(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "PASS" and len(splitedCmd) == 2:
            client.send(self.handlePassword(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "PWD" and len(splitedCmd) == 1:
            client.send(self.server.handlePWD(portNum).encode())

        elif splitedCmd[0] == "MKD" and splitedCmd[1] == "-i" and len(splitedCmd) == 3:
            client.send(self.server.handleMKFile(portNum, splitedCmd[2]).encode())

        elif splitedCmd[0] == "MKD" and len(splitedCmd) == 2:
            client.send(self.server.handleMKDir(portNum, splitedCmd[1]))

        elif splitedCmd[0] == "RMD" and splitedCmd[1] == "-f" and len(splitedCmd) == 3:
            client.send(self.server.handleDeleteDir(portNum, splitedCmd[2]).encode())

        elif splitedCmd[0] == "RMD" and len(splitedCmd) == 2:
            client.send(self.server.handleDeleteFile(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "LIST" and len(splitedCmd) == 2:
            client.send(self.server.handleGetList(portNum, splitedCmd[1]).encode())

        elif splitedCmd[0] == "CWD" and len(splitedCmd) == 2:
            pass
        elif splitedCmd[0] == "DL" and len(splitedCmd) == 2:
            pass
        elif splitedCmd[0] == "HELP" and len(splitedCmd) == 1:
            pass
        elif splitedCmd[0] == "QUIT" and len(splitedCmd) == 1:
            pass
        else:
            client.send("501 Syntax error in parameters or arguments.".encode())
    

    





class API :

    def __init__(self):
        self.logger = None
        self.jsonParser()
        self.cmdParser = CommandParser(self.users, self.dataPort)
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.bind(("",self.cmdPort))
        self.s.listen(10)
        # self.s.setblocking(False)
        # self.s.settimeout(100.0)
        self.listen()

    def handleRequest(self,  client, address):
        # client.send(cmd +" "+str(address[1]))
        # self.cmdParser.parseCmd(client, address[1], cmd)
        # try:
        while(True):
            cmd = client.recv(MAX_LENGTH)
            self.cmdParser.parseCmd(client, address[1], cmd)
        # except:
        #     client.close()
        #     print("done")

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
            self.logger = Logger(configs["logging"]["path"])

        if(configs["authorization"]["enable"]):
            for admin in configs["authorization"]["admins"]:
                self.users[admin].setRole()
            self.adminFiles = configs["authorization"]["files"]

api = API()