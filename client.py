from socket import *

class Client:
    def __init__(self):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.dataS = socket(AF_INET, SOCK_STREAM)
        self.talk()
        
    def talk(self):
        self.dataS.bind(("", 0))
        self.dataS.listen(1)
        self.s.connect(("", 8000))
        port = self.dataS.getsockname()[1]
        while(True):
            cmd = input()
            print(cmd.encode())
            if(cmd == "LIST"):
                cmd += " " + str(port)
            self.s.send(cmd.encode())
            if(cmd == "LIST " + str(port)):
                c,a = self.dataS.accept()
                listData = c.recv(100000)
                print(listData.decode())
                c.close()
            data = self.s.recv(100000)
            print(data.decode())    
        self.s.close()


c = Client()