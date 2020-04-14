from socket import *
import sys

COMMAND_PORT = int(sys.argv[1])

class Client:
    def __init__(self):
        self.comandSocket = socket(AF_INET, SOCK_STREAM)
        self.dataSocket = socket(AF_INET, SOCK_STREAM)
        
    def talk(self):
        self.dataSocket.bind(("", 0))
        self.dataSocket.listen(1)
        port = self.dataSocket.getsockname()[1]
        self.comandSocket.connect(("", COMMAND_PORT))
        while(True):
            cmd = input()
            if(cmd.split()[0] == "LIST" or cmd.split()[0] == "DL"):
                cmd += " " + str(port)

            self.comandSocket.send(cmd.encode())

            if(cmd.split()[0] == "LIST" and len(cmd.split())==2) or (cmd.split()[0] == "DL" and len(cmd.split())==3):
                c,a = self.dataSocket.accept()
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
            data = self.comandSocket.recv(100000)
            print(data.decode())    
        self.comandSocket.close()


if __name__ == "__main__":
    c = Client()
    c.talk()

