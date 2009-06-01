"""Defines the OpenFlow GUI-based OpenPipes protocol."""

import struct
import time

from twisted.internet import reactor

from OFGMessage import OFG_DEFAULT_PORT, OFG_MESSAGES
from OFGMessage import OFGMessage, LinksAdd, LinksDel, Link, LinkSpec, Node, NodesAdd, NodesDel, FlowHop, Flow, FlowsAdd, FlowsDel
from router_cli import *
from ltprotocol.ltprotocol import LTProtocol

class GUIRouter:
    def __init__(self, rtr_):
	self.rtr = rtr_

MPFR_PROTOCOL = LTProtocol(OFG_MESSAGES, 'H', 'B')
rtrs = list()

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

    from ltprotocol.ltprotocol import LTTwistedServer

    def close_conn_callback(conn):
	print "close_conn_callback: Connection closed\n"
	for rtr in rtrs:
	    print "Deleting router " + rtr.routerID + " from the list"
	    del(rtr)

    # when the gui connects, tell it about the modules and nodes
    def new_conn_callback(conn):
	'''
        nodes = [
            Node(Node.TYPE_HOST, 0),
            Node(Node.TYPE_HOST, 10),
            Node(Node.TYPE_OPENFLOW_SWITCH, 1),
            Node(Node.TYPE_OPENFLOW_SWITCH, 14),
            Node(Node.TYPE_OPENFLOW_SWITCH, 2),
            Node(Node.TYPE_OPENFLOW_SWITCH, 12),
            Node(Node.TYPE_OPENFLOW_SWITCH, 3),
            Node(Node.TYPE_OPENFLOW_SWITCH, 13),
            ]
        server.send_msg_to_client(conn, NodesAdd(nodes))

	linkspecs = [
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_HOST, 0), 0, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 0, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 0, Node(Node.TYPE_HOST, 0), 0, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_HOST, 10), 0, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 0, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 0, Node(Node.TYPE_HOST, 10), 0, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 2, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 1, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 2, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 1, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 2, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 1, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 2, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 1, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 2, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 1, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 3, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 3, 1000000000),

		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 3, 1000000000),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 3, 1000000000),
		]
	server.send_msg_to_client(conn, LinksAdd(linkspecs))

	path = [
		FlowHop(2, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2),
		FlowHop(3, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 2),
		]
	flows = [Flow(Flow.TYPE_UNKNOWN, 1, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 1, path),]
	server.send_msg_to_client(conn, FlowsAdd(flows))
	'''
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

	#draw the router nodes first
        nodes = []
	for r in rtrs:
	    nodes.append(Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(r.routerID)))
        server.send_msg_to_client(conn, NodesAdd(nodes))

	for r in rtrs:
	    r.checkLinkStatus()
	    r.updateNeighbors()
	    r.getStats()
	time.sleep(2)
	#draw the links
	for r in rtrs:
	    print "Drawing links for router " + r.routerID
	    linkspecs = []
	    for i in r.interfaces:
		print "\tInterface : " + i.name
		if(i.isLinkUp() and (len(i.neighbors) > 0)):
		    print "\t\tLink is up : neighbor " + i.neighbors[0].getNeighborID()
		    src_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(r.routerID))
		    src_port = get_port(i.name)
		    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(i.neighbors[0].getNeighborID()))
		    dst_port = get_nbr_iface(i.neighbors[0])
		    print "\t\tdst_port = " + str(dst_port)
		    if(dst_port >= 0):
			linkspecs.append(LinkSpec(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port, 1000000000))
	    server.send_msg_to_client(conn, LinksAdd(linkspecs))
	while(False):
	    if(len(rtrs) == 0):
		print "No routers left in the list - I'm done with this session"
		return
	    for r in rtrs:
		r.checkLinkStatus()
		r.updateNeighbors()
		r.getStats()
	    #for r in rtrs:
		#for i in r.interfaces:
		    #if link status has changed
		    #if neighbors have changed
		    #if flow has changed
	    time.sleep(0.1)

    #server = LTTwistedServer(MPFR_PROTOCOL, print_ltm)
    server = LTTwistedServer(MPFR_PROTOCOL, print_ltm, new_conn_callback, close_conn_callback)
    #server.new_conn_callback = new_conn_callback
    server.listen(OFG_DEFAULT_PORT)
    reactor.run()

if __name__ == "__main__":
    test()
