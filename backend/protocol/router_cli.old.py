# CS344 Spring 09
# Mario Flajslik
# Stanford University

import socket, string, BufferedSocket, re, sys

class Router:
    
    def __init__(self, host, port):
        self.routerID = 0
        self.interfaces = list()
        self.multipath = 0
        self.fastReroute = 0

        self.sockEnd = "TheEnd!"
        self.sockTimeout = 3 # blocking read timeout
        try:
            self.sock =  BufferedSocket.BufferedSocket([host,int(port)])
            self.sock.settimeout(self.sockTimeout)
        except:
            print "Socket error"
            return
        
        if(not self.setBot("on")):
            print "Failed to set CLI to bot mode"
            return
        self.initInterfaces()

    def __del__(self):
	self.setBot("off")
	self.sock.close()
        
    def getRouterID(self):
        return self.routerID
    
    def getMultipath(self):
        return (self.multipath == 1)

    def getFastReroute(self):
        return (self.fastReroute == 1)

    # returns interface reference, give interface name
    def getInterface(self, name):
        for intf in self.interfaces:
            if(intf.isMe(name)):
                return intf
        return None

    # sets CLI in bot mode, i.e. makes the CLI end every message with TheEnd!
    def setBot(self, val):
        routerID_re = re.compile('RouterID:\s*(\d+\.\d+\.\d+\.\d+)')
        running_re = re.compile('Bot\s+is\s+(\w+)')
        self.sock.writeline("adv bot " + val);
        is_on = False
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return False
            if(line == self.sockEnd):
                break
            res = routerID_re.search(line)
            if res is not None:
                self.routerID = res.group(1)
            res = running_re.search(line)
            if res is not None:
                if (res.group(1) == 'ON'):
                    is_on = True
        
        if(is_on):
            return True
        else:
            return False

    # initializes interfaces
    def initInterfaces(self):
        ifline_re = re.compile('(\w+)\s+IP:\s*(\d+\.\d+\.\d+\.\d+)\s+netmask:\s*(\d+\.\d+\.\d+\.\d+)\s+MAC:\s*(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)\s+enabled:\s*(\d+)')
        self.sock.writeline("show ip interface")
        self.interfaces = list()
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return
            if(line == self.sockEnd):
                break
            res = ifline_re.search(line)
            if ( (res is not None) and (int(res.group(5)) == 1) ):
                self.interfaces.append( RouterInterface(res.group(1), res.group(2), res.group(3), res.group(4)) )

    # sets multipath, returns True if mulipath is on, False if it is off
    def setMultipath(self, val):
        multi_re = re.compile('Multipath\s+is\s+(\w+)')
        if(val == 1):
            val = 'on'
        elif(val == 0):
            val = 'off'

        self.sock.writeline("adv mode multi " + val)
        is_on = (self.multipath == 1)
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return is_on
            if(line == self.sockEnd):
                break
            res = multi_re.search(line)
            if res is not None:
                if (res.group(1) == 'ON'):
                    is_on = True
                elif (res.group(1) == 'OFF'):
                    is_on = False
        
        if(is_on):
            self.multipath = 1
            return True
        else:
            self.multipath = 0
            return False

    # sets fast reroute, returns True if fast reroute is on, False if it is off
    def setFastReroute(self, val):
        fast_re = re.compile('Fast\s+Reroute\s+is\s+(\w+)')
        if(val == 1):
            val = 'on'
        elif(val == 0):
            val = 'off'

        self.sock.writeline("adv mode fast " + val)
        is_on = (self.fastReroute == 1)
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return is_on
            if(line == self.sockEnd):
                break
            res = fast_re.search(line)
            if res is not None:
                if (res.group(1) == 'ON'):
                    is_on = True
                elif (res.group(1) == 'OFF'):
                    is_on = False
        
        if(is_on):
            self.fastReroute = 1
            return True
        else:
            self.fastReroute = 0
            return False

    # checks for router mode and updates local variables (ideally, this doesn't need to be called)
    def updateMode(self):
        multi_re = re.compile('Multipath\s+is\s+(\w+)')
        fast_re = re.compile('Fast\s+Reroute\s+is\s+(\w+)')

        self.sock.writeline("adv mode")
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return
            if(line == self.sockEnd):
                break
            res = multi_re.search(line)
            if res is not None:
                if (res.group(1) == 'ON'):
                    self.multipath = 1
                elif (res.group(1) == 'OFF'):
                    self.multipath = 0
            res = fast_re.search(line)
            if res is not None:
                if (res.group(1) == 'ON'):
                    self.fastReroute = 1
                elif (res.group(1) == 'OFF'):
                    self.fastReroute = 0


    # updates link status for every interface (this should be called often)
    def checkLinkStatus(self):
        link_re = re.compile('If\s+name:\s+(\w+)\s+link:\s(\d)')
        self.sock.writeline("show hw about")
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return
            if(line == self.sockEnd):
                break
            res = link_re.search(line)
            if res is not None:
                self.getInterface(res.group(1)).setLinkStatus(int(res.group(2)))

    # updates neighbors
    def updateNeighbors(self):
        ifline_re = re.compile('(\w+):\s+neighbors:')
        neighline_re = re.compile('\s+RouterID:\s*(\d+\.\d+\.\d+\.\d+)\s+IP:\s*(\d+\.\d+\.\d+\.\d+)')
        self.sock.writeline("show ospf neigh")
        last_intf = None
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return
            if(line == self.sockEnd):
                break
            res = ifline_re.search(line)
            if res is not None:
                last_intf = self.getInterface(res.group(1))
                last_intf.emptyNeighbors()
            res = neighline_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.addNeighbor( RouterNeighbor(last_intf.getName(), res.group(1), res.group(2)) )

    # gets statistics
    def getStats(self):
        ifline_re = re.compile('Interface:\s+(\w+)')
        packetIN_re = re.compile('Num\s+pkts\s+received:\s+(\d+)')
        packetOUT_re = re.compile('Num\s+bytes\s+received:\s+(\d+)')
        bytesIN_re = re.compile('Num\s+pkts\s+sent:\s+(\d+)')
        bytesOUT_re = re.compile('Num\s+bytes\s+sent:\s+(\d+)')
        self.sock.writeline("adv stats")
        last_intf = None
        while( True ):
            try:
                line = self.sock.readline()
            except:
                print "Socket Timeout"
                return
            if(line == self.sockEnd):
                break
            res = ifline_re.search(line)
            if res is not None:
                last_intf = self.getInterface(res.group(1))
                print last_intf.getName()
            res = packetIN_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.setPacketsIN( int(res.group(1)) )
            res = packetOUT_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.setPacketsOUT( int(res.group(1)) )
                    print last_intf.getPacketsOUT()
            res = bytesIN_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.setBytesIN( int(res.group(1)) )
            res = bytesOUT_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.setBytesOUT( int(res.group(1)) )

class RouterInterface:
 
    def __init__(self, name_, ip_, netmask_, mac_):
        self.name = name_
        self.ip = ip_
        self.netmask = netmask_
        self.mac = mac_
        self.linkStatus = 0
        self.neighbors = list()

        self.packetsIN = 0
        self.packetsOUT = 0
        self.bytesIN = 0
        self.bytesOUT = 0

    def getName(self):
        return self.name

    def addNeighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def emptyNeighbors(self):
        self.neighbors = list()

    def getNeighbors(self):
        return self.neighbors

    def isMe(self, name):
        if(self.name == name):
            return True
        else:
            return False
        
    def setLinkStatus(self, status):
        self.linkStatus = status

    def isLinkUp(self):
        if(self.linkStatus == 1):
            return True
        else:
            return False

    def getPacketsIN(self):
        return self.packetsIN
    def getPacketsOUT(self):
        return self.packetsOUT
    def getBytesIN(self):
        return self.bytesIN
    def getBytesOUT(self):
        return self.bytesOUT

    def setPacketsIN(self, val):
        self.packetsIN = val
    def setPacketsOUT(self, val):
        self.packetsOUT = val
    def setBytesIN(self, val):
        self.bytesIN = val
    def setBytesOUT(self, val):
        self.bytesOUT = val


class RouterNeighbor:

    def __init__(self, interface_, neighborID_, ip_):
        self.interface = interface_
        self.neighborID = neighborID_
        self.ip = ip_

    def getNeighborID(self):
        return self.neighborID

    def getNeighborIP(self):
        return self.ip
