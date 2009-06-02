package org.openflow.gui.net.protocol;

import java.io.DataInput;
import java.io.IOException;

import org.openflow.gui.net.protocol.auth.*;
import org.openflow.protocol.StatsType;

/**
 * Enumerates what types of messages are in the OpenFlow GUI protocol.
 * 
 * @author David Underhill
 */
public enum OFGMessageType {
    /** Disconnection message */
    DISCONNECT((byte)0x00),

    /** request for an echo reply (keep-alive) */
    ECHO_REQUEST((byte)0x01),
    
    /** reply to an echo request (keep-alive) */
    ECHO_REPLY((byte)0x02),
    
    /** Authentication request */
    AUTH_REQUEST((byte)0x03),

    /** Authentication reply */
    AUTH_REPLY((byte)0x04),
    
    /** Information about whether a user has been authenticated */
    AUTH_STATUS((byte)0x05),
    
    /** Tell the backend to start polling a message */
    POLL_START((byte)0x0E),
    
    /** Tell the backend to stop polling a message */
    POLL_STOP((byte)0x0F),

    /** Query for nodes */
    NODES_REQUEST((byte)0x10),

    /** Reply with list of nodes added. */
    NODES_ADD((byte)0x11),

    /** Reply with list of nodes deleted. */
    NODES_DELETE((byte)0x12),

    /** Query of links */
    LINKS_REQUEST((byte)0x13),

    /** Reply with list of links added.  Body is array of book_link_spec. */
    LINKS_ADD((byte)0x14),

    /** Reply with list of links deleted.  Body is array of book_link_spec. */
    LINKS_DELETE((byte)0x15),
    
    /** Query for flows */
    FLOWS_REQUEST((byte)0x16),

    /** List of flows to add. */
    FLOWS_ADD((byte)0x17),

    /** List of flows to delete. */
    FLOWS_DELETE((byte)0x18),
    
    /**
     * Statistics request.  Body is book_stat_message, with osr_body as defined 
     * in OpenFlow for ofp_stats_request.
     */
    STAT_REQUEST((byte)0x20),

    /**
     * Aggregated statistics reply.  Body is book_stat_message, with osr_body
     * as defined for ofp_stats_reply in OpenFlow, with exception of 
     * ofp_desc_stats having ofp_switch_features appended.
     */
    STAT_REPLY((byte)0x21),
    
    /**
     * Set Multipath/FastRe routing
     */
    SET_MPFR((byte)0xF0),
 


    ;

    /** the special value used to identify messages of this type */
    private final byte typeID;

    private OFGMessageType(byte typeID) {
        this.typeID = typeID;
    }

    /** returns the special value used to identify this type */
    public byte getTypeID() {
        return typeID;
    }

    /** Returns the OFGMessageType constant associated with typeID, if any */
    public static OFGMessageType typeValToMessageType(byte typeID) {
        for(OFGMessageType t : OFGMessageType.values())
            if(t.getTypeID() == typeID)
                return t;

        return null;
    }
    
    /** 
     * Constructs the object representing the received message.  The message is 
     * known to be of length len and len - 4 bytes representing the rest of the 
     * message should be extracted from buf.
     */
    public static OFGMessage decode(int len, DataInput in) throws IOException {
        // parse the message header (except length which was already done)
        byte typeByte = in.readByte();
        OFGMessageType t = OFGMessageType.typeValToMessageType(typeByte);
        if(t == null)
            throw new IOException("Unknown type ID: " + typeByte);
        
        int xid = in.readInt();
        OFGMessage msg = decode(len, t, xid, in);
        msg.xid = xid;
        return msg;
    }
     
    /** 
     * Constructs the object representing the received message.  The message is 
     * known to be of length len.  The header of the message (length, type,
     * and transaction ID) have been read, but the remainder is still on the 
     * input stream.
     */
    private static OFGMessage decode(int len, OFGMessageType t, int xid, DataInput in) throws IOException {
        // parse the rest of the message
        switch(t) {
            case AUTH_REQUEST:
                return new AuthRequest(len, xid, in);
            
            case AUTH_STATUS:
                return new AuthStatus(len, xid, in);
            
            case NODES_ADD:
                return new NodesAdd(len, xid, in);
                
            case NODES_DELETE:
                return new NodesDel(len, xid, in);
                
            case LINKS_ADD:
                return new LinksAdd(len, xid, in);
                
            case LINKS_DELETE:
                return new LinksDel(len, xid, in);
                
            case FLOWS_ADD:
                return new FlowsAdd(len, xid, in);
                
            case FLOWS_DELETE:
                return new FlowsDel(len, xid, in);
            
            case STAT_REPLY:
                return StatsType.decode(len, t, xid, in);

            case ECHO_REQUEST:
            case ECHO_REPLY:
                return new OFGMessage(t, xid);
                
            case DISCONNECT:
            case AUTH_REPLY:
            case POLL_START:
            case POLL_STOP:
            case NODES_REQUEST:
            case LINKS_REQUEST:
            case FLOWS_REQUEST:
            case STAT_REQUEST:
            case SET_MPFR:
                throw new IOException("Received unexpected message type: " + t.toString() + " (len=" + len + "B)");
                
            default:
                throw new IOException("Unhandled type received: " + t.toString() + " (len=" + len + "B)");
        }
    }
}
