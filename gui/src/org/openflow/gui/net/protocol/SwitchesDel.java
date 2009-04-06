package org.openflow.gui.net.protocol;

import java.io.DataInput;
import java.io.IOException;

/**
 * Switch(es) deleted message.
 * 
 * @author David Underhill
 */
public class SwitchesDel extends SwitchList {
    public SwitchesDel(final long[] dpids) {
        this(0, dpids);
    }
    
    public SwitchesDel(int xid, final long[] dpids) {
        super(OFGMessageType.SWITCHES_DELETE, xid, dpids);
    }
    
    public SwitchesDel(final int len, final int xid, final DataInput in) throws IOException {
        super(len, OFGMessageType.SWITCHES_DELETE, xid, in);
    }
}