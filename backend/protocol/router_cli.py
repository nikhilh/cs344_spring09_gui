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
                elif (res.group(1) == 'OFF'):
                    return False
        
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
                self.getInterface(res.group(1)).setLinkStatusUpdateOld(int(res.group(2)))

    # updates neighbors
    def updateNeighbors(self):
        ifline_re = re.compile('(\w+):\s+neighbors:')
        neighline_re = re.compile('\s+RouterID:\s*(\d+\.\d+\.\d+\.\d+)\s+IP:\s*(\d+\.\d+\.\d+\.\d+)')
        self.sock.writeline("show ospf neigh")
        retVal = False
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
                last_intf.backupNeighbors()
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
                last_intf.backupStats()
            res = packetIN_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.stats.setPacketsIN( int(res.group(1)) )
            res = packetOUT_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.stats.setPacketsOUT( int(res.group(1)) )
            res = bytesIN_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.stats.setBytesIN( int(res.group(1)) )
            res = bytesOUT_re.search(line)
            if res is not None:
                if(last_intf is not None):
                    last_intf.stats.setBytesOUT( int(res.group(1)) )

class RouterInterface:
 
    def __init__(self, name_, ip_, netmask_, mac_):
        self.name = name_
        self.ip = ip_
        self.netmask = netmask_
        self.mac = mac_
        self.linkStatus = 0
        self.old_linkStatus = 0
        self.neighbors = list()
        self.old_neighbors = list()
        self.stats = RouterInterfaceStats()
        self.old_stats = RouterInterfaceStats()
        self.old_statsIN_change = False
        self.old_statsOUT_change = False

    def getName(self):
        return self.name

    def addNeighbor(self, neighbor): 
        self.neighbors.append(neighbor)

    # checks if neighbors have changed, and returns True if they have
    def haveChangedNeighbors(self):
        if( len(self.neighbors) != len(self.old_neighbors) ):
            return True
        self.neighbors.sort()
        self.old_neighbors.sort()
        for i in range(0, len(self.neighbors)):
            if( self.neighbors[i] != self.old_neighbors[i] ):
                return True
        return False

    # save neighbors in old_neighbors
    def backupNeighbors(self):
        self.emptyOldNeighbors()
        self.old_neighbors.extend(self.neighbors)

    def emptyNeighbors(self):
        self.neighbors = list()

    def emptyOldNeighbors(self):
        self.old_neighbors = list()

    def getNeighbors(self):
        return self.neighbors

    def getOldNeighbors(self):
        return self.old_neighbors

    def isMe(self, name):
        if(self.name == name):
            return True
        else:
            return False
        
    def setLinkStatus(self, status):
        self.linkStatus = status

    def setLinkStatusUpdateOld(self, status):
        self.old_linkStatus = self.linkStatus
        self.linkStatus = status

    def isLinkUp(self):
        if(self.linkStatus == 1):
            return True
        else:
            return False

    def wasLinkUp(self):
        if(self.old_linkStatus == 1):
            return True
        else:
            return False

    # checks for link status change, returns True if changed
    def hasChangedLinkStatus(self):
        return ( self.isLinkUp() != self.wasLinkUp() )

    def getStats(self):
        return self.stats

    def getOldStats(self):
        return self.old_stats

    def backupStats(self):
        self.old_statsIN_change = self.haveChangedStatsIN() 
        self.old_statsOUT_change = self.haveChangedStatsOUT() 
        self.getOldStats().copyFrom(self.getStats())

    # checks for stats change, returns True if changed
    def haveChangedStats(self):
        return ( self.getStats() != self.getOldStats() )

    # checks for IN stats change, returns True if changed
    def haveChangedStatsIN(self):
        return not self.getStats().eqIN( self.getOldStats() )

    # checks for OUT stats change, returns True if changed
    def haveChangedStatsOUT(self):
        return not self.getStats().eqOUT( self.getOldStats() )

    def getOldStatsINChange(self):
        return self.old_statsIN_change

    def getOldStatsOUTChange(self):
        return self.old_statsOUT_change

    # checks for change in "IN stats change", returns True if changed
    def hasChangedStatsINChange(self):
        return ( self.haveChangedStatsIN() != self.getOldStatsINChange() )

    # checks for change in "OUT stats change", returns True if changed
    def hasChangedStatsOUTChange(self):
        return ( self.haveChangedStatsOUT() != self.getOldStatsOUTChange() )

class RouterNeighbor:

    def __init__(self, interface_, neighborID_, ip_):
        self.interface = interface_
        self.neighborID = neighborID_
        self.ip = ip_

    def getNeighborID(self):
        return self.neighborID

    def getNeighborIP(self):
        return self.ip

    def getInterface(self):
        return self.interface

    def __eq__(self, neighbor):
        if(neighbor.getNeighborID() != self.getNeighborID()):
            return False
        elif(neighbor.getNeighborIP() != self.getNeighborIP()):
            return False
        elif(neighbor.getInterface() != self.getInterface()):
            return False
        return True

    def __ne__(self, other):
        return not (self == other)

class RouterInterfaceStats:
    def __init__(self, packetsIN = 0, packetsOUT = 0, bytesIN = 0, bytesOUT = 0):    
        self.packetsIN = packetsIN
        self.packetsOUT = packetsOUT
        self.bytesIN = bytesIN
        self.bytesOUT = bytesOUT

    def copyFrom(self, other):
        self.packetsIN = other.getPacketsIN()
        self.packetsOUT = other.getPacketsOUT()
        self.bytesIN = other.getBytesIN()
        self.bytesOUT = other.getBytesOUT()
        
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

    def eqIN(self, other):
        if(other.getPacketsIN() != self.getPacketsIN()):
            return False
        if(other.getBytesIN() != self.getBytesIN()):
            return False
        return True

    def eqOUT(self, other):
        if(other.getPacketsOUT() != self.getPacketsOUT()):
            return False
        if(other.getBytesOUT() != self.getBytesOUT()):
            return False
        return True

    def __eq__(self, other):
        if(other.getPacketsIN() != self.getPacketsIN()):
            return False
        if(other.getPacketsOUT() != self.getPacketsOUT()):
            return False
        if(other.getBytesIN() != self.getBytesIN()):
            return False
        if(other.getBytesOUT() != self.getBytesOUT()):
            return False
        return True

    def __ne__(self, other):
        return not (self == other)
