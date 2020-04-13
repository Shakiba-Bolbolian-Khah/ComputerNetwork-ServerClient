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
            if(cmd.split()[0] == "LIST" or cmd.split()[0] == "DL"):
                cmd += " " + str(port)
            self.s.send(cmd.encode())
            if(cmd.split()[0] == "LIST" or cmd.split()[0] == "DL"):
                c,a = self.dataS.accept()
                total_data=[]
                while True:
                    data = c.recv(8192).decode()
                    if not data: break
                    total_data.append(data)
                
                if cmd.split()[0] == "DL":
                    fileName = cmd.split()[1]
                    open(fileName, 'w').write(''.join(total_data))
                elif cmd.split()[0] == "LIST":
                    print(''.join(total_data))
                c.close()
            data = self.s.recv(100000)
            print(data.decode())    
        self.s.close()


c = Client()