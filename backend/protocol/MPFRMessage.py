"""Defines the OpenFlow GUI-based MPFR protocol."""

import struct
import time

from twisted.internet import reactor

from OFGMessage import OFG_DEFAULT_PORT, OFG_MESSAGES
from OFGMessage import OFGMessage, LinksAdd, LinksDel, Link, LinkSpec, Node, NodesAdd, NodesDel, FlowHop, Flow, FlowsAdd, FlowsDel
from router_cli import *
from ltprotocol.ltprotocol import LTProtocol

MPFR_MESSAGES = []

class SetMPFR(OFGMessage):
    #subtypes
    TYPE_MP = 0
    TYPE_FR = 1

    @staticmethod
    def get_type():
        return 0xF0

    def __init__(self, type_, val_, xid=0):
        OFGMessage.__init__(self, xid)
	self.type = int(type_)
	self.val = int(val_)

    def get_subtype(self):
	return self.type

    def length(self):
        return OFGMessage.SIZE + 4

    def pack(self):
        return OFGMessage.pack(self) + struct.pack('> HH', self.type, self.val)

    @staticmethod
    def unpack(body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
	type = struct.unpack('> H', body[:2])[0]
        body = body[2:]
	val = struct.unpack('> H', body[:2])[0]
        return SetMPFR(type, val, xid)

    def __str__(self):
	if(self.type == self.TYPE_MP):
	    return 'Set MULTIPATH : ' + str(self.val) + ' ' + OFGMessage.__str__(self)
	elif(self.type == self.TYPE_FR):
	    return 'Set FAST REROUTE : ' + str(self.val) + ' ' + OFGMessage.__str__(self)
	else:
	    return "Unknown subtype"

MPFR_MESSAGES.append(SetMPFR)


MPFR_PROTOCOL = LTProtocol(OFG_MESSAGES + MPFR_MESSAGES, 'H', 'B')
rtrs = list()
GIGABIT = 1000000000

def run_mpfr_server(port, recv_callback):
    """Starts a server which listens for MPFR clients on the specified port.

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

    def get_nbr_iface(nbr, check_disabled=True):
	for r in rtrs:
	    if(r.getRouterID() == nbr.getNeighborID()):
		for i in r.interfaces:
		    if((i.ip == nbr.getNeighborIP())):
			if((not check_disabled) or i.isLinkUp()):
			    return get_port(i.name)
	return (-1)

    def get_host_nbr(rtr_ip):
	for r in rtrs:
	    for i in r.interfaces:
		if(i.ip == rtr_ip):
		    return (ip_to_dpid(r.routerID), get_port(i.name),)
	return (-1, -1,)


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
	    elif t == SetMPFR.get_type():
		if(ltm.get_subtype() == SetMPFR.TYPE_MP): 
		    for r in rtrs:
			r.setMultipath(ltm.val)
		elif(ltm.get_subtype() == SetMPFR.TYPE_FR): 
		    for r in rtrs:
			r.setFastReroute(ltm.val)

    from ltprotocol.ltprotocol import LTTwistedServer

    def close_conn_callback(conn):
	print "close_conn_callback: Connection closed\n"
	while len(rtrs) > 0:
	    rtr = rtrs.pop()
	    print "Deleting router " + rtr.routerID
	    print str(len(rtrs)) + " routers left"
	    del(rtr)

    def update_rtrs(conn):
	print "Calling update_rtrs"
	if(len(rtrs) == 0):
	    print "No routers left in the list - I'm done with this session"
	    return

	print str(time.time())+ "\tUpdating the status of all routers"
	for r in rtrs:
	    r.checkLinkStatus()
	    r.updateNeighbors()
	    r.getStats()

	for r in rtrs:
	    print "Router :" + r.routerID
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
			dst_port = get_nbr_iface(old_nbrs[0], False)
			if(dst_port >= 0):
			    del_links.append(Link(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port))
			    # if there was a flow delete it
			    if(i.getOldStatsOUTChange()):
				del_flows.append(Flow(Flow.TYPE_UNKNOWN, ip_to_dpid(i.ip), int(i.getStatsChange()*8/1000), src_node, src_port, dst_node, dst_port, list()))

		    # if there is a new nbr and the link is up, add link and flow
		    if((len(new_nbrs) > 0) and i.isLinkUp()):
			dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(new_nbrs[0].getNeighborID()))
			dst_port = get_nbr_iface(new_nbrs[0])
			if(dst_port >= 0):
			    add_linkspecs.append(LinkSpec(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port, GIGABIT))

		# if there is a flow add it
		if(i.haveChangedStatsOUT() and (len(new_nbrs) > 0)):
		    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(new_nbrs[0].getNeighborID()))
		    dst_port = get_nbr_iface(new_nbrs[0])
		    if(dst_port >= 0):
			add_flows.append(Flow(Flow.TYPE_UNKNOWN, ip_to_dpid(i.ip), int(i.getStatsChange()*8/1000), src_node, src_port, dst_node, dst_port, list()))
		# else delete it
		elif(len(old_nbrs) > 0):
		    dst_node = Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(old_nbrs[0].getNeighborID()))
		    dst_port = get_nbr_iface(old_nbrs[0], False)
		    if(dst_port >= 0):
			del_flows.append(Flow(Flow.TYPE_UNKNOWN, ip_to_dpid(i.ip), 0, src_node, src_port, dst_node, dst_port, list()))
		else:
		    print "Interface " + i.getName() + ": No change in flows: link-status ("+ str(i.wasLinkUp()) + "," +str(i.isLinkUp()) + ") , or neighbor-list (" + str(len(old_nbrs)) + "," + str(len(new_nbrs)) + "), or stats (" + str(i.getOldStatsOUTChange()) + "," + str(i.haveChangedStatsOUT()) + ")"

	    if(len(del_links) > 0):
		server.send_msg_to_client(conn, LinksDel(del_links))
		for link in del_links:
		    print "Deleting link: " + str(link.src_node.id) + ":" + str(link.src_port) + " -> " + str(link.dst_node.id) + ":" + str(link.dst_port)
	    if(len(add_linkspecs) > 0):
		server.send_msg_to_client(conn, LinksAdd(add_linkspecs))
		for link in add_linkspecs:
		    print "Adding link: " + str(link.src_node.id) + ":" + str(link.src_port) + " -> " + str(link.dst_node.id) + ":" + str(link.dst_port)
	    if(len(del_flows) > 0):
		server.send_msg_to_client(conn, FlowsDel(del_flows))
		for flow in del_flows:
		    print "Deleting flow " + str(flow.flow_id) + ": " + str(flow.src_node.id) + ":" + str(flow.src_port) + " -> " + str(flow.dst_node.id) + ":" + str(flow.dst_port)
	    if(len(add_flows) > 0):
		server.send_msg_to_client(conn, FlowsAdd(add_flows))
		for flow in add_flows:
		    print "Adding flow " + str(flow.flow_id) + ": " + str(flow.src_node.id) + ":" + str(flow.src_port) + " -> " + str(flow.dst_node.id) + ":" + str(flow.dst_port)

	reactor.callLater(POLL_INTERVAL, lambda: update_rtrs(conn))
	return


    # when the gui connects, tell it about the modules and nodes
    def new_conn_callback(conn):
	################# GUI debug ###############
	################# must be deleted #########

	rtr_nodes = [
		Node(Node.TYPE_OPENFLOW_SWITCH, 1),
		Node(Node.TYPE_OPENFLOW_SWITCH, 2),
		Node(Node.TYPE_OPENFLOW_SWITCH, 3),
		Node(Node.TYPE_OPENFLOW_SWITCH, 4),
		]
	host_nodes = [
		Node(Node.TYPE_HOST, 11),
		Node(Node.TYPE_HOST, 13),
		]
	rtr_links = [
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 2, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 1, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 4), 2, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 4), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 1, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 4), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 2, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 4), 1, GIGABIT),
		]
	host_links = [
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_HOST, 11), 0, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 0, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 0, Node(Node.TYPE_HOST, 11), 0, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_HOST, 13), 0, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 0, GIGABIT),
		LinkSpec(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 0, Node(Node.TYPE_HOST, 13), 0, GIGABIT),
		]
	flows = [
		Flow(Flow.TYPE_UNKNOWN, 12345, 1000, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 2, list()),
		Flow(Flow.TYPE_UNKNOWN, 54321, 1100, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2, list()),
		]
	server.send_msg_to_client(conn, NodesAdd(rtr_nodes))
	server.send_msg_to_client(conn, NodesAdd(host_nodes))
	server.send_msg_to_client(conn, LinksAdd(host_links))
	server.send_msg_to_client(conn, LinksAdd(rtr_links))
	server.send_msg_to_client(conn, FlowsAdd(flows))

	return
	###########################################

	# read in router information
	try:
	    f = open('routers.txt', 'r')
	except IOError:
	    print "Could not open routers.txt for reading!"
	    return
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

	# Get updates the first time (do it 2 times! to get flow info)
	for r in rtrs:
	    r.checkLinkStatus()
	    r.updateNeighbors()
	    r.getStats()
	time.sleep(2)
	for r in rtrs:
	    r.checkLinkStatus()
	    r.updateNeighbors()
	    r.getStats()

	#draw the router nodes first
        nodes = []
	for r in rtrs:
	    print "Drawing router " + r.routerID
	    nodes.append(Node(Node.TYPE_OPENFLOW_SWITCH, ip_to_dpid(r.routerID)))
	if(len(nodes) > 0):
	    server.send_msg_to_client(conn, NodesAdd(nodes))

	# read in host information
	# draw hosts and links
	try:
	    f = open('hosts.txt', 'r')
	except IOError:
	    print "Could not open hosts.txt for reading!"
	    return
	lines = f.readlines()
	f.close()
	hosts = []
	host_linkspecs = []
	host_re = re.compile("(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)")
	for line in lines:
	    res = rtr_re.search(line)
	    if res is not None:
		host_ip = res.group(1)
		src_node = ip_to_dpid(host_ip)
		src_port = 0
		rtr_ip = res.group(2)
		print "Drawing node and flows for host " + host_ip
		(dst_dpid, dst_port) = get_host_nbr(rtr_ip)
		hosts.append(Node(Node.TYPE_HOST, src_node))
		if(dst_dpid > 0 and dst_port >= 0):
			host_linkspecs.append(LinkSpec(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port, GIGABIT))
			host_linkspecs.append(LinkSpec(Link.TYPE_WIRE, dst_node, dst_port, src_node, src_port, GIGABIT))
			print host_ip + ":" + str(src_port) + " -> " + rtr_ip + ":" + str(dst_port)
			print rtr_ip + ":" + str(dst_port) + " -> " + host_ip + ":" + str(src_port)
	if(len(hosts) > 0):
	    server.send_msg_to_client(conn, NodesAdd(hosts))
	if(len(host_linkspecs) > 0):
	    server.send_msg_to_client(conn, LinksAdd(host_linkspecs))

	#draw the router links
	for r in rtrs:
	    print "Drawing links and flows for router " + r.routerID
	    linkspecs = []
	    flows = []
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
			print r.routerID + ":" + str(src_port) + " -> " + i.neighbors[0].getNeighborID() + ":" + str(dst_port)
			linkspecs.append(LinkSpec(Link.TYPE_WIRE, src_node, src_port, dst_node, dst_port, GIGABIT))
			if(i.haveChangedStatsOUT()):
			    flow = Flow(Flow.TYPE_UNKNOWN, ip_to_dpid(i.ip), int(i.getStatsChange()*8/1000), src_node, src_port, dst_node, dst_port, list())
			    flows.append(flow)
			    print "Adding flow " + str(flow.flow_id) + ": " + str(flow.src_node.id) + ":" + str(flow.src_port) + " -> " + str(flow.dst_node.id) + ":" + str(flow.dst_port)
	    if(len(linkspecs) > 0):
		server.send_msg_to_client(conn, LinksAdd(linkspecs))
	    if(len(flows) > 0):
		server.send_msg_to_client(conn, FlowsAdd(flows))

	#thread.start_new_thread(update_rtrs, (conn,))
	reactor.callLater(0, lambda: update_rtrs(conn))

    #server = LTTwistedServer(MPFR_PROTOCOL, print_ltm, new_conn_callback, close_conn_callback)
    server = LTTwistedServer(MPFR_PROTOCOL, receive_ltm, new_conn_callback, close_conn_callback)
    server.listen(OFG_DEFAULT_PORT)
    reactor.run()

if __name__ == "__main__":
    test()
