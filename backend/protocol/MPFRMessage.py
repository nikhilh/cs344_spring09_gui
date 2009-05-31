"""Defines the OpenFlow GUI-based OpenPipes protocol."""

import struct

from twisted.internet import reactor

from OFGMessage import OFG_DEFAULT_PORT, OFG_MESSAGES
from OFGMessage import OFGMessage, LinksAdd, LinksDel, Link, Node, NodesAdd, NodesDel, FlowHop, Flow, FlowsAdd, FlowsDel
from ltprotocol.ltprotocol import LTProtocol

MPFR_PROTOCOL = LTProtocol(OFG_MESSAGES, 'H', 'B')

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
    # simply print out all received messages
    def print_ltm(xport, ltm):
        if ltm is not None:
            print 'recv: %s' % str(ltm)
            t = ltm.get_type()
            if t==LinksAdd.get_type() or t==LinksDel.get_type():
                # got request to add/del a link: tell the GUI we've done so
                xport.write(MPFR_PROTOCOL.pack_with_header(ltm))

    from ltprotocol.ltprotocol import LTTwistedServer
    server = LTTwistedServer(MPFR_PROTOCOL, print_ltm)
    server.listen(OFG_DEFAULT_PORT)

    # when the gui connects, tell it about the modules and nodes
    def new_conn_callback(conn):
	"""
	modules = [
            OPModule(Node.TYPE_MODULE_HW, 1, "MAC Lookup"),
            OPModule(Node.TYPE_MODULE_HW, 2, "TTL Decrement"),
            OPModule(Node.TYPE_MODULE_HW, 3, "TTL Decrement (FAULTY)"),
            OPModule(Node.TYPE_MODULE_HW, 4, "Route Lookup"),
            OPModule(Node.TYPE_MODULE_HW, 5, "Checksum Update"),
            OPModule(Node.TYPE_MODULE_HW, 6, "TTL / Checksum Validate"),
            OPModule(Node.TYPE_MODULE_SW, 100, "TTL / Checksum Validate"),
            OPModule(Node.TYPE_MODULE_SW, 101, "Compar-ison Module"),
            ]
        server.send_msg_to_client(conn, OPModulesAdd(modules))

        nodes = [
            Node(Node.TYPE_IN,       111),
            Node(Node.TYPE_OUT,      999),
            Node(Node.TYPE_NETFPGA, 1000),
            Node(Node.TYPE_NETFPGA, 1001),
            Node(Node.TYPE_NETFPGA, 1002),
            Node(Node.TYPE_NETFPGA, 1003),
            Node(Node.TYPE_NETFPGA, 1004),
            Node(Node.TYPE_NETFPGA, 1005),
            Node(Node.TYPE_LAPTOP,  2000),
            Node(Node.TYPE_LAPTOP,  2001),
            Node(Node.TYPE_LAPTOP,  2002),
            ]
        server.send_msg_to_client(conn, NodesAdd(nodes))

        server.send_msg_to_client(conn, OPTestInfo("hello world", "happy world"))

        # tell the gui the route lookup module on netfpga 1000 works
        n = Node(Node.TYPE_NETFPGA, 1000)
        m = Node(Node.TYPE_MODULE_HW, 4)
        server.send_msg_to_client(conn, OPModuleStatusReply(n, m, "it works!"))
	"""
	print "Incoming connection! yay! :P"
        nodes = [
            Node(Node.TYPE_OPENFLOW_SWITCH, 1),
            Node(Node.TYPE_OPENFLOW_SWITCH, 14),
            Node(Node.TYPE_OPENFLOW_SWITCH, 2),
            Node(Node.TYPE_OPENFLOW_SWITCH, 12),
            Node(Node.TYPE_OPENFLOW_SWITCH, 3),
            Node(Node.TYPE_OPENFLOW_SWITCH, 13),
            ]
        server.send_msg_to_client(conn, NodesAdd(nodes))

	links = [
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 1),

		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 2),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 1),

		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 2),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 1),

		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 2),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 12), 1),

		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 2),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 1),

		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 1, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 2),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 2), 2, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 1),

		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 3),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 14), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 3), 3),

		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 3),
		Link(Link.TYPE_WIRE, Node(Node.TYPE_OPENFLOW_SWITCH, 1), 3, Node(Node.TYPE_OPENFLOW_SWITCH, 13), 3),
		]
        server.send_msg_to_client(conn, LinksAdd(links))

	path = [
		#FlowHop(2, 0),
		FlowHop(2, 1),
		FlowHop(3, 2),
		#FlowHop(3, 3),
		#FlowHop(14, 3),
		#FlowHop(14, 2),
		#FlowHop(12, 1),
		#FlowHop(12, 0),
		]
	flows = [Flow(path),]
	server.send_msg_to_client(conn, FlowsAdd(flows))

    server.new_conn_callback = new_conn_callback
    reactor.run()

if __name__ == "__main__":
    test()
