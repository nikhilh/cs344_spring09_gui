# modified from effbot.org/zone/socket-intro.htm

import socket, string

CRLF = "\r\n"

class BufferedSocket:
    "Client support class for simple Internet protocols."

    def __init__(self, argList):
        "Connect to an Internet server."
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if (len(argList) == 2):
            self.sock.connect((argList[0], argList[1]))
            self.file = self.sock.makefile("rb") # buffered
        
        else:
            self.sock = argList[0]
            self.file = self.sock.makefile("rb") # buffered


    def writeline(self, line):
        "Send a line to the server."
        self.sock.send(line + CRLF) # unbuffered write

    def read(self, maxbytes = None):
        "Read data from server."
        if maxbytes is None:
            return self.file.read()
        else:
            return self.file.read(maxbytes)

    def readline(self):
        "Read a line from the server.  Strip trailing CR and/or LF."
        s = self.file.readline()
        if not s:
            raise EOFError
        if s[-2:] == CRLF:
            s = s[:-2]
        elif s[-1:] in CRLF:
            s = s[:-1]
        return s
        
    def close(self):
        try: 
            self.sock.close()
            self.file.close()
        except:
            pass

    def settimeout(self, val):
        self.sock.settimeout(val)
