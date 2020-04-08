from socket import *
import json
import thread

CONFIG_ADD = "./config.json"
NORMAL = "normal"
ADMIN = "admin"
MAX_LENGTH = 2048

class Accountant:
    def __init__(self, size, alert, threshold):
        self.size = size
        self.alert = alert
        self.threshold = threshold


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

    def __str__(self):
        print (self.userName, self.password, self.role, self.email, self.accountant.size, self.accountant.alert, self.accountant.threshold)
        return self.userName



class Logger:
    def __init__(self, fileName):
        self.logFile = open(fileName,"a")


class Server:
    def __init__(self):
        pass

class CommandParser:
    def __init__(self):
        self.server = Server()
    def parseCmd(self,cmd):
        pass





class API :

    def __init__(self):
        self.logger = None
        self.jsonParser()
        self.cmdParser = CommandParser()
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.bind(("",self.cmdPort))
        self.s.listen(10)
        # self.s.setblocking(False)
        # self.s.settimeout(100.0)
        self.listen()

    def handleRequest(self, cmd, client,address):
        client.send(cmd +" "+str(a[1]))
        try:
            while(True):
                cmd = client.recv(MAX_LENGTH)
                print("here1")
                client.send(cmd +" "+str(a[1]))
        except:
            client.close()
            print("done")

    def listen(self):
        while(True):
            c,a = self.s.accept()
            cmd = c.recv(MAX_LENGTH)
            print("here")
            t = thread.start_new_thread(self.handleRequest,(cmd,c,a))


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
                size = user["size"]
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