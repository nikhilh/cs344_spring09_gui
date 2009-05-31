"""Defines the OpenFlow GUI-based OpenPipes protocol."""

import struct

from twisted.internet import reactor

from OFGMessage import OFG_DEFAULT_PORT, OFG_MESSAGES
from OFGMessage import OFGMessage, LinksAdd, LinksDel, Link, LinkSpec, Node, NodesAdd, NodesDel, FlowHop, Flow, FlowsAdd, FlowsDel
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

    print "This gets printed\n"
    from ltprotocol.ltprotocol import LTTwistedServer

    def close_conn_callback(conn):
	print "close_conn_callback: Connection closed\n"

    # when the gui connects, tell it about the modules and nodes
    def new_conn_callback(conn):
	print "Incoming connection! yay! :P"
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

    #server = LTTwistedServer(MPFR_PROTOCOL, print_ltm)
    server = LTTwistedServer(MPFR_PROTOCOL, print_ltm, new_conn_callback, close_conn_callback)
    #server.new_conn_callback = new_conn_callback
    server.listen(OFG_DEFAULT_PORT)
    reactor.run()

if __name__ == "__main__":
    test()
