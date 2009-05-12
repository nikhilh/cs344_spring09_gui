"""Defines the OpenFlow GUI protocol and some associated helper functions."""

import array
import struct

from twisted.internet import reactor

from ltprotocol.ltprotocol import LTMessage, LTProtocol

OFG_DEFAULT_PORT = 2503

def array_to_octstr(arr):
    bstr = ''
    for byte in arr:
        if bstr != '':
            bstr += ':%02x' % (byte,)
        else:
            bstr += '%02x' %(byte,)
    return bstr

def dpidstr(ll):
    return array_to_octstr(array.array('B',struct.pack('!Q',ll))).replace('00:', '')

OFG_MESSAGES = []

class OFGMessage(LTMessage):
    SIZE = 4

    def __init__(self, xid=0):
        LTMessage.__init__(self)
        self.xid = xid

    def length(self):
        return self.SIZE

    def pack(self):
        return struct.pack('> I', self.xid)

    @staticmethod
    def unpack(body):
        return OFGMessage(struct.unpack('> I', body[:4])[0])

    def __str__(self):
        return 'xid=%u' % self.xid

class Disconnect(OFGMessage):
    @staticmethod
    def get_type():
        return 0x00

    def __init__(self, xid=0):
        OFGMessage.__init__(self, xid)

    def __str__(self):
        return 'DISCONNECT: ' + OFGMessage.__str__(self)
OFG_MESSAGES.append(Disconnect)

class PollStart(OFGMessage):
    @staticmethod
    def get_type():
        return 0x0E

    def __init__(self, interval_in_100ms_units, lm, xid=0):
        OFGMessage.__init__(self, xid)
        self.interval = interval_in_100ms_units
        self.lm = lm

    def length(self):
        return OFGMessage.SIZE + 2 + self.lm.length()

    def pack(self):
        return OFGMessage.pack(self) + struct.pack('> S', self.interval) + self.lm.pack()

    @staticmethod
    def unpack(body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
        interval = struct.unpack('> H', body[:2])[0]
        body = body[2:]

        _ = struct.unpack('> H', body[:2])[0]  # inner message length
        body = body[2:]
        type_val = struct.unpack('> B', body[:1])[0]
        body = body[1:]
        lm = OFG_PROTOCOL.unpack_received_msg(type_val, body)

        return PollStart(interval, lm, xid)

    def __str__(self):
        fmt = 'POLL_START: ' + OFGMessage.__str__(self) + ' interval=%.1fsec msg=%s'
        return fmt % (self.interval * 10.0, str(self.lm))
OFG_MESSAGES.append(PollStart)

class PollStop(OFGMessage):
    @staticmethod
    def get_type():
        return 0x0F

    def __init__(self, xid_to_stop_polling, xid=0):
        OFGMessage.__init__(self, xid)
        self.xid_to_stop_polling = xid_to_stop_polling

    def length(self):
        return OFGMessage.SIZE + 4

    def pack(self):
        return OFGMessage.pack(self) + struct.pack('> I', self.xid_to_stop_polling)

    @staticmethod
    def unpack(body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
        xid_to_stop_polling = struct.unpack('> I', body[:4])[0]
        return PollStop(xid_to_stop_polling, xid)

    def __str__(self):
        return 'POLL_STOP: ' + OFGMessage.__str__(self) + ' xid_to_stop_polling=%u' % self.xid_to_stop_polling
OFG_MESSAGES.append(PollStop)

class Node:
    SIZE = 10

    # default types
    TYPE_UNKNOWN = 0
    TYPE_OPENFLOW_SWITCH = 1
    TYPE_OPENFLOW_WIRELESS_ACCESS_POINT = 2
    TYPE_HOST = 100

    def __init__(self, node_type, node_id):
        self.node_type = int(node_type)
        self.id = long(node_id)

    def pack(self):
        return struct.pack('> HQ', self.node_type, self.id)

    @staticmethod
    def unpack(buf):
        t = struct.unpack('> HQ', buf[:Node.SIZE])
        return Node(t[0], t[1])

    @staticmethod
    def type_to_str(node_type):
        if node_type == Node.TYPE_OPENFLOW_SWITCH:
            return 'OFSwitch'
        elif node_type == Node.TYPE_OPENFLOW_WIRELESS_ACCESS_POINT:
            return 'AP'
        elif node_type == Node.TYPE_HOST:
            return 'Host'
        else:
            return 'unknown'

    def __str__(self):
        return '%s{%s}' % (Node.type_to_str(self.node_type), dpidstr(self.id))

class NodesList(OFGMessage):
    def __init__(self, nodes, xid=0):
        OFGMessage.__init__(self, xid)
        self.nodes = nodes

    def length(self):
        return OFGMessage.SIZE + len(self.nodes) * Node.SIZE

    def pack(self):
        return OFGMessage.pack(self) + ''.join([node.pack() for node in self.nodes])

    @staticmethod
    def unpack_child(clz, body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
        num_nodes = len(body) / Node.SIZE
        nodes = []
        for _ in range(num_nodes):
            nodes.append(Node.unpack(body[Node.SIZE:]))
            body = body[:Node.SIZE]
        return clz(nodes, xid)

    def __str__(self):
        return OFGMessage.__str__(self) + ' nodes=[%s]' % ''.join([str(node) + ',' for node in self.nodes])

class NodesAdd(NodesList):
    @staticmethod
    def get_type():
        return 0x11

    def __init__(self, nodes, xid=0):
        NodesList.__init__(self, nodes, xid)

    @staticmethod
    def unpack(body):
        return NodesList.unpack_child(NodesAdd, body)

    def __str__(self):
        return 'NODES_ADD: ' + NodesList.__str__(self)
OFG_MESSAGES.append(NodesAdd)

class NodesDel(NodesList):
    @staticmethod
    def get_type():
        return 0x12

    def __init__(self, dpids, xid=0):
        NodesList.__init__(self, dpids, xid)

    @staticmethod
    def unpack(body):
        return NodesList.unpack_child(NodesDel, body)

    def __str__(self):
        return 'NODES_DEL: ' + NodesList.__str__(self)
OFG_MESSAGES.append(NodesDel)

class Link:
    SIZE = 2 + (2 * (Node.SIZE + 2))

    TYPE_UNKNOWN = 0
    TYPE_WIRE = 1
    TYPE_WIRELESS = 2
    TYPE_TUNNEL = 4

    def __init__(self, link_type, src_node, src_port, dst_node, dst_port):
        self.link_type = link_type
        self.src_node = src_node
        self.src_port = src_port
        self.dst_node = dst_node
        self.dst_port = dst_port

    def pack(self):
        src = self.src_node.pack() + struct.pack('> H', self.src_port)
        dst = self.dst_node.pack() + struct.pack('> H', self.dst_port)
        return struct.pack('> H', self.link_type) + src + dst

    @staticmethod
    def unpack(buf):
        link_type = struct.unpack('> H', buf[:2])[0]
        buf = buf[2:]
        src_node = Node.unpack(buf[:Node.SIZE])
        buf = buf[Node.SIZE:]
        src_port = struct.unpack('> H', buf[:2])[0]
        buf = buf[2:]
        dst_node = Node.unpack(buf[:Node.SIZE])
        buf = buf[Node.SIZE:]
        dst_port = struct.unpack('> H', buf[:2])[0]
        return Link(link_type, src_node, src_port, dst_node, dst_port)

    @staticmethod
    def type_to_str(link_type):
        if link_type == Link.TYPE_WIRE:
            return 'wire'
        elif link_type == Link.TYPE_WIRELESS:
            return 'wireless'
        elif link_type == Link.TYPE_TUNNEL:
            return 'tunnel'
        else:
            return 'unknown'

    def __str__(self):
        return '%s:%u --(%s)-> %s:%u' % (str(self.src_node), self.src_port,
                                         Link.type_to_str(self.link_type),
                                         str(self.dst_node), self.dst_port)

class LinksList(OFGMessage):
    def __init__(self, links, xid=0):
        OFGMessage.__init__(self, xid)
        self.links = links

    def length(self):
        return OFGMessage.SIZE + len(self.links) * Link.SIZE

    def pack(self):
        hdr = OFGMessage.pack(self)
        return hdr + ''.join([link.pack() for link in self.links])

    @staticmethod
    def unpack_child(clz, body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
        num_links = len(body) / Link.SIZE
        links = []
        for _ in range(num_links):
            links.append(Link.unpack(body[:Link.SIZE]))
            body = body[Link.SIZE:]
        return clz(links, xid)

    def links_to_string(self):
        return '[' + ', '.join([str(l) for l in self.links]) + ']'

    def __str__(self):
        return OFGMessage.__str__(self) + ' links=%s' % str(self.links_to_string())

class LinksAdd(LinksList):
    @staticmethod
    def get_type():
        return 0x14

    def __init__(self, links, xid=0):
        LinksList.__init__(self, links, xid)

    @staticmethod
    def unpack(body):
        return LinksList.unpack_child(LinksAdd, body)

    def __str__(self):
        return 'LINKS_ADD: ' + LinksList.__str__(self)
OFG_MESSAGES.append(LinksAdd)

class LinksDel(LinksList):
    @staticmethod
    def get_type():
        return 0x15

    def __init__(self, links, xid=0):
        LinksList.__init__(self, links, xid)

    @staticmethod
    def unpack(body):
        return LinksList.unpack_child(LinksDel, body)

    def __str__(self):
        return 'LINKS_DEL: ' + LinksList.__str__(self)
OFG_MESSAGES.append(LinksDel)

class FlowHop:
    SIZE = 10

    def __init__(self, dpid, port):
        self.dpid = long(dpid)
        self.port = port

    def pack(self):
        return struct.pack('> QH', self.dpid, self.port)

    @staticmethod
    def unpack(buf):
        t = struct.unpack('> QH', buf[:FlowHop.SIZE])
        return FlowHop(t[0], t[1])

    def __str__(self):
        return '%s/%u' % (dpidstr(self.dpid), self.port)

class Flow:
    TYPE_UNKNOWN = 0

    def __init__(self, flow_type, flow_id, path):
        self.flow_type = int(flow_type)
        self.flow_id = int(flow_id)
        self.path = path

    def pack(self):
        header = struct.pack('> H 2I', self.flow_type, self.flow_id, len(self.path))
        body = ''.join(struct.pack('QH', hop.dpid, hop.port) for hop in self.path)
        return header + body

    @staticmethod
    def unpack(buf):
        flow_type, flow_id, num_hops = struct.unpack('> H 2I', buf[:10])
        buf = buf[10:]
        path = []
        for _ in range(num_hops):
            path.append(FlowHop.unpack(buf[:FlowHop.SIZE]))
            buf = buf[FlowHop.SIZE:]

        return Flow(flow_type, flow_id, path)

    def length(self):
        return 10 + FlowHop.SIZE * len(self.path)

    @staticmethod
    def type_to_str(flow_type):
        return 'unknown'

    def __str__(self):
        return 'Flow:%s:%u{%s}' % (Flow.type_to_str(self.flow_type), self.flow_id,
                                   ''.join('%s:%u' % (dpidstr(hop.dpid), hop.port) for hop in self.path))

class FlowsList(OFGMessage):
    def __init__(self, flows, xid=0):
        OFGMessage.__init__(self, xid)
        self.flows = flows

    def length(self):
        return OFGMessage.SIZE + 4 + sum(flow.length() for flow in self.flows)

    def pack(self):
        hdr = OFGMessage.pack(self) + struct.pack('> I', len(self.flows))
        return hdr + ''.join([flow.pack() for flow in self.flows])

    @staticmethod
    def unpack_child(clz, body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
        num_flows = struct.unpack('> I', body)[0]
        body = body[4:]
        flows = []
        for _ in range(num_flows):
            f = Flow.unpack(body)
            flows.append(f)
            body = body[f.length():]
        return clz(flows, xid)

    def flows_to_string(self):
        return '[' + ', '.join([str(f) for f in self.flows]) + ']'

    def __str__(self):
        return OFGMessage.__str__(self) + ' flows=%s' % str(self.flows_to_string())

class FlowsAdd(FlowsList):
    @staticmethod
    def get_type():
        return 0x18

    def __init__(self, flows, xid=0):
        FlowsList.__init__(self, flows, xid)

    @staticmethod
    def unpack(body):
        return FlowsList.unpack_child(FlowsAdd, body)

    def __str__(self):
        return 'FLOWS_ADD: ' + FlowsList.__str__(self)
OFG_MESSAGES.append(FlowsAdd)

class FlowsDel(FlowsList):
    @staticmethod
    def get_type():
        return 0x19

    def __init__(self, flows, xid=0):
        FlowsList.__init__(self, flows, xid)

    @staticmethod
    def unpack(body):
        return FlowsList.unpack_child(FlowsDel, body)

    def __str__(self):
        return 'FLOWS_DEL: ' + FlowsList.__str__(self)
OFG_MESSAGES.append(FlowsDel)

class Request(OFGMessage):
    TYPE_UNKNOWN = 0
    TYPE_ONETIME = 1
    TYPE_SUBSCRIBE = 2
    TYPE_UNSUBSCRIBE = 3

    def __init__(self, request_type, otype, xid=0):
        OFGMessage.__init__(self, xid)
        self.request_type = request_type
        self.type = otype

    def length(self):
        return OFGMessage.SIZE + 3

    def pack(self):
        return OFGMessage.pack(self) + struct.pack('> 2H', self.request_type, self.type)

    @staticmethod
    def unpack_child(clz, body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
        t = struct.unpack('> BH', body)
        return clz(t[0], t[1], xid)

    @staticmethod
    def type_to_str(request_type):
        if request_type == Request.TYPE_ONETIME:
            return 'ONETIME'
        elif request_type == Request.TYPE_SUBSCRIBE:
            return 'SUBSCRIBE'
        elif request_type == Request.TYPE_UNSUBSCRIBE:
            return 'UNSUBSCRIBE'
        else:
            return 'unknown'

    def otype_to_str(self, otype):
        return str(otype)

    def __str__(self):
        rstr = Request.type_to_str(self.request_type)
        ostr = self.otype_to_str(self.type)
        return OFGMessage.__str__(self) + ' %s %s' % (rstr, ostr)

class NodesRequest(Request):
    @staticmethod
    def get_type():
        return 0x10

    def __init__(self, request_type, node_type, xid=0):
        Request.__init__(self, request_type, node_type, xid)

    @staticmethod
    def unpack(body):
        return Request.unpack_child(NodesRequest, body)

    def otype_to_str(self, otype):
        return Node.type_to_str(otype)

    def __str__(self):
        return 'REQUEST for Nodes: ' + Request.__str__(self)
OFG_MESSAGES.append(NodesRequest)

class LinksRequest(Request):
    @staticmethod
    def get_type():
        return 0x13

    def __init__(self, request_type, link_type, src_node, xid=0):
        Request.__init__(self, request_type, link_type, xid)
        self.src_node = src_node

    def pack(self):
        return Request.pack(self) + self.src_node.pack()

    @staticmethod
    def unpack(body):
        xid = struct.unpack('> I', body[:4])[0]
        body = body[4:]
        t = struct.unpack('> BH', body[:3])
        body = body[3:]
        src_node = Node.unpack(body)
        return LinksRequest(t[0], t[1], src_node, xid)

    def otype_to_str(self, otype):
        return Link.type_to_str(otype)

    def __str__(self):
        return 'REQUEST for Links: ' + Request.__str__(self)
OFG_MESSAGES.append(LinksRequest)

class FlowsRequest(Request):
    @staticmethod
    def get_type():
        return 0x16

    def __init__(self, request_type, flow_type, xid=0):
        Request.__init__(self, request_type, flow_type, xid)

    @staticmethod
    def unpack(body):
        return Request.unpack_child(FlowsRequest, body)

    def otype_to_str(self, otype):
        return Flow.type_to_str(otype)

    def __str__(self):
        return 'REQUEST for Flows: ' + Request.__str__(self)
OFG_MESSAGES.append(FlowsRequest)

OFG_PROTOCOL = LTProtocol(OFG_MESSAGES, 'H', 'B')

def create_ofg_server(port, recv_callback):
    """Starts a server which listens for OFG clients on the specified port.

    @param port  the port to listen on
    @param recv_callback  the function to call with received message content
                         (takes two arguments: transport, msg)

    @return returns the new LTTwistedServer
    """
    from ltprotocol.ltprotocol import LTTwistedServer
    server = LTTwistedServer(OFG_PROTOCOL, recv_callback)
    server.listen(port)
    return server

def run_ofg_server(port, recv_callback):
    """Creates (see create_ofg_server()) and runs a OFG server.

    @return this method does not return until the server shuts down (e.g. ctrl-c)
    """
    create_ofg_server(port, recv_callback)
    reactor.run()

def test():
    # test: simply print out all received messages
    def print_ltm(_, ltm):
        if ltm is not None:
            print 'recv: %s' % str(ltm)
            if ltm.get_type() == NodesRequest.get_type():
                nodes = [Node(Node.TYPE_OPENFLOW_SWITCH, i+1) for i in range(20)]
                server.send(NodesAdd(nodes))
                server.send(LinksAdd([Link(i % 2 + 1, nodes[i], 0, nodes[i+1], 1) for i in range(19)]))

    server = create_ofg_server(OFG_DEFAULT_PORT, print_ltm)
    reactor.run()

if __name__ == "__main__":
    test()
