"""Defines the OpenFlow GUI-based OpenPipes protocol."""

import struct
import time

from twisted.internet import reactor

from OFGMessage import OFG_DEFAULT_PORT, OFG_MESSAGES
from OFGMessage import OFGMessage, LinksAdd, LinksDel, Link, LinkSpec, Node, NodesAdd, NodesDel, FlowHop, Flow, FlowsAdd, FlowsDel
from router_cli import *
from ltprotocol.ltprotocol import LTProtocol

MPFR_MESSAGES = []

class SetMP(OFGMessage):
    @staticmethod
    def get_type():
        return 0xF0

    def __init__(self, val_, xid=0):
        OFGMessage.__init__(self, xid)
	self.val = val_

    def length(self):
        return OFGMessage.SIZE + 2

    def pack(self):
        return OFGMessage.pack(self) + struct.pack('> H', self.val)

    @staticmethod
    def unpack(body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
	val = struct.unpack('> H', body[:2])[0]
        return SetMP(val, xid)

    def __str__(self):
        return 'Set MULTIPATH: ' + self.val + ' ' + OFGMessage.__str__(self)

MPFR_MESSAGES.append(SetMP)

class SetFR(OFGMessage):
    @staticmethod
    def get_type():
        return 0xF1

    def __init__(self, val_, xid=0):
        OFGMessage.__init__(self, xid)
	self.val = val_

    def length(self):
        return OFGMessage.SIZE + 2

    def pack(self):
        return OFGMessage.pack(self) + struct.pack('> H', self.val)

    @staticmethod
    def unpack(body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
	val = struct.unpack('> H', body[:2])[0]
        return SetMP(val, xid)

    def __str__(self):
        return 'Set FASTREROUTE: ' + self.val + ' ' + OFGMessage.__str__(self)

MPFR_MESSAGES.append(SetFR)

MPFR_PROTOCOL = LTProtocol(OFG_MESSAGES + MPFR_MESSAGES, 'H', 'B')
rtrs = list()
GIGABIT = 1000000000
POLL_INTERVAL = float(0.5)

def run_mpfr_server(port, recv_callback):
    """Starts a server which listens for Open Pipes clients on the specified port.

    @param port  the port to listen on
    @param recv_callback  the function to call with received message content
                         (takes two arguments: transport, msg)

    @return returns the new LTTwistedServer
    """
    from ltprotocol.ltprotocol import LTTwistedServer
    server = LTTwistedServer(MPFR_PROTOCOL, recv_callback)
    server.listen(port)
    reactor.run()

def test():
    def ip_to_dpid(ip):
	ip_re = re.compile("(\d+)\.(\d+)\.(\d+)\.(\d+)")
	ip_group = ip_re.search(ip)
	if ip_group is not None:
	    dpid = long(0)
	    for i in range(1,5):
		dpid = long(dpid)*256 + long(ip_group.group(i))
	    return dpid
	return 0

    def get_port(name):
	return int(name[-1:])

    def get_nbr_iface(nbr):
	for r in rtrs:
	    if(r.getRouterID() == nbr.getNeighborID()):
		for i in r.interfaces:
		    if((i.ip == nbr.getNeighborIP()) and i.isLinkUp()):
			return get_port(i.name)
	return (-1)


    # simply print out all received messages
    def print_ltm(xport, ltm):
        if ltm is not None:
            print 'recv: %s' % str(ltm)
            t = ltm.get_type()
            if t==LinksAdd.get_type() or t==LinksDel.get_type():
                # got request to add/del a link: tell the GUI we've done so
                xport.write(MPFR_PROTOCOL.pack_with_header(ltm))

    def receive_ltm(xport, ltm):
        if ltm is not None:
            print 'recv: %s' % str(ltm)
            t = ltm.get_type()
            if t==LinksAdd.get_type() or t==LinksDel.get_type():
                # got request to add/del a link: tell the GUI we've done so
                xport.write(MPFR_PROTOCOL.pack_with_header(ltm))
	    elif t == SetMP.get_type():
		for r in rtrs:
		    r.setMultipath(ltm.val)
	    elif t == SetFR.get_type():
		for r in rtrs:
		    r.setFastReroute(ltm.val)

    from ltprotocol.ltprotocol import LTTwistedServer

    def close_conn_callback(conn):
	print "close_conn_callback: Connection closed\n"
	for rtr in rtrs:
	    print "Deleting router " + rtr.routerID + " from the list"
	    del(rtr)

    # when the gui connects, tell it about the modules and nodes
    def new_conn_callback(conn):
	f = open('routers.txt', 'r')
	lines = f.readlines()
	f.close()
	rtr_re = re.compile("(\S+)\s+(\d+)")
	for line in lines:
	    res = rtr_re.search(line)
	    if res is not None:
		rtr = Router(res.group(1), res.group(2))
		print "Parsed router " + res.group(1) + ":" + res.group(2) + ", dpid " + str(ip_to_dpid(rtr.routerID))
		if rtr is not None:
		    rtrs.append(rtr)

	# Get updates the first time
	for r in rtrs:
	    r.checkLinkStatus()
	    r.updateNeighbors()
	    r.getStats()
	time.sleep(2)

	#draw the router nodes first
        nodes = []
	for r in rtrs:
	    nodes.append(Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(r.routerID)))
        server.send_msg_to_client(conn, NodesAdd(nodes))

	#draw the links
	for r in rtrs:
	    print "Drawing links for router " + r.routerID
	    linkspecs = []
	    src_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(r.routerID))
	    for i in r.interfaces:
		print "\tInterface : " + i.name
		if(i.isLinkUp() and (len(i.neighbors) > 0)):
		    print "\t\tLink is up : neighbor " + i.neighbors[0].getNeighborID()
		    src_port = get_port(i.name)
		    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(i.neighbors[0].getNeighborID()))
		    dst_port = get_nbr_iface(i.neighbors[0])
		    print "\t\tdst_port = " + str(dst_port)
		    if(dst_port >= 0):
			linkspecs.append(LinkSpec(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port, GIGABIT))
	    server.send_msg_to_client(conn, LinksAdd(linkspecs))

	while(True):
	    if(len(rtrs) == 0):
		print "No routers left in the list - I'm done with this session"
		return
	    for r in rtrs:
		r.checkLinkStatus()
		r.updateNeighbors()
		r.getStats()

	    for r in rtrs:
		src_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(r.routerID))
		del_links = []
		add_linkspecs = []
		del_flows = []
		add_flows = []
		for i in r.interfaces:
		    src_port = get_port(i.name)
		    old_nbrs = i.getOldNeighbors()
		    new_nbrs  = i.getNeighbors()

		    #if neighbors have changed or link status has changed
		    if(i.haveChangedNeighbors() or i.hasChangedLinkStatus()):
			#if there was an old nbr and active link, delete link and flow
			if((len(old_nbrs) > 0) and i.wasLinkUp()):
			    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(old_nbrs[0].getNeighborID()))
			    dst_port = get_nbr_iface(old_nbrs[0])
			    del_links.append(Link(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port))
			    # if there was a flow delete it
			    if(i.getOldStatsOUTChange()):
				del_flows.append(Flow(Flow.TYPE_UNKNOWN, 0, src_node, src_port, dst_node, dst_port, list()))

			# if there is a new nbr and the link is up, add link and flow
			if((len(new_nbrs) > 0) and i.isLinkUp()):
			    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(new_nbrs[0].getNeighborID()))
			    dst_port = get_nbr_iface(new_nbrs[0])
			    add_linkspecs.append(LinkSpec(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port, GIGABIT))
			    # if there is a flow add it
			    if(i.haveChangedStatsOUT()):
				add_flows.append(Flow(Flow.TYPE_UNKNOWN, 0, src_node, src_port, dst_node, dst_port, list()))

		    #else, if flow has changed
		    elif(i.hasChangedStatsOUTChange()):
			# if there was a flow delete it
			if((len(old_nbrs) > 0) and i.getOldStatsOUTChange()):
			    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(old_nbrs[0].getNeighborID()))
			    dst_port = get_nbr_iface(old_nbrs[0])
			    del_flows.append(Flow(Flow.TYPE_UNKNOWN, 0, src_node, src_port, dst_node, dst_port, list()))
			# if there is a flow add it
			if((len(new_nbrs) > 0) and i.haveChangedStatsOUT()):
			    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(new_nbrs[0].getNeighborID()))
			    dst_port = get_nbr_iface(new_nbrs[0])
			    add_flows.append(Flow(Flow.TYPE_UNKNOWN, 0, src_node, src_port, dst_node, dst_port, list()))

		if(len(del_links) > 0):
		    server.send_msg_to_client(conn, LinksDel(del_links))
		if(len(add_linkspecs) > 0):
		    server.send_msg_to_client(conn, LinksAdd(add_linkspecs))
		if(len(del_flows) > 0):
		    server.send_msg_to_client(conn, FlowsDel(del_flows))
		if(len(add_flows) > 0):
		    server.send_msg_to_client(conn, FlowsAdd(add_flows))

	    time.sleep(POLL_INTERVAL)

    #server = LTTwistedServer(MPFR_PROTOCOL, print_ltm)
    server = LTTwistedServer(MPFR_PROTOCOL, print_ltm, new_conn_callback, close_conn_callback)
    #server.new_conn_callback = new_conn_callback
    server.listen(OFG_DEFAULT_PORT)
    reactor.run()

if __name__ == "__main__":
    test()
