from socket import *

class Client:
    def __init__(self):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.dataS = socket(AF_INET, SOCK_STREAM)
        self.talk()
        
    def talk(self):
        self.dataS.bind(("", 0))
        self.dataS.listen(1)
        self.s.connect(("", 8100))
        port = self.dataS.getsockname()[1]
        while(True):
            cmd = input()
            print(cmd.encode())
            if(cmd.split()[0] == "LIST" or cmd.split()[0] == "DL"):
                cmd += " " + str(port)
            self.s.send(cmd.encode())
            if(cmd.split()[0] == "LIST" and len(cmd.split())==2) or (cmd.split()[0] == "DL" and len(cmd.split())==3):
                c,a = self.dataS.accept()
                total_data=bytearray()
                while True:
                    data = c.recv(8192)
                    if not data: break
                    total_data.extend(data)

                total_data = total_data.decode("ISO-8859-1").split('\n',1)
                if(total_data[0]!="0"):
                    if cmd.split()[0] == "DL":
                        fileName = cmd.split()[1]
                        open(fileName, 'wb').write(total_data[1].encode("ISO-8859-1"))
                    elif cmd.split()[0] == "LIST":
                        print(total_data[1])
                c.close()
            data = self.s.recv(100000)
            print(data.decode())    
        self.s.close()


c = Client()