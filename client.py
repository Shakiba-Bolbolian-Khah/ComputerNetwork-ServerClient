from socket import *

class Client:
    def __init__(self):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.talk()
        
    def talk(self):
        self.s.connect(("", 8200))
        while(True):
            cmd = raw_input()
            print(cmd)
            self.s.send(cmd)
            data = self.s.recv(100000)
            print(data)    
        self.s.close()


c = Client()