from socket import *

class Client:
    def __init__(self):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.dataS = socket(AF_INET, SOCK_STREAM)
        self.talk()
        
    def talk(self):
        self.s.connect(("", 8300))
        self.dataS.bind(("", 8200))
        print(self.dataS.getsockname()[1])
        while(True):
            cmd = raw_input()
            print(cmd)
            if(cmd == "LIST"):
                cmd += " 8200"
            self.s.send(cmd)
            if(cmd == "LIST 8200"):
                self.dataS.listen(2)
                c,a = self.dataS.accept()
                listData = self.dataS.recv(100000)
                print(listData)
            data = self.s.recv(100000)
            print(data)    
        self.s.close()


c = Client()