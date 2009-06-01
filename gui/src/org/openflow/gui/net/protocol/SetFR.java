package org.openflow.gui.net.protocol;

import java.io.DataOutput;
import java.io.IOException;

public class SetFR extends OFGMessage {

	/**
	 * Value sent to the backend server
	 * should be 0 or 1
	 */
	public final short value;
	
	public SetFR(OFGMessageType t, short val) {
		super(t, 0);
		this.value = val;
	}
	
	/** This returns the message length */
    public int length() {
        return super.length() + 2;
    }
    
    /** Writes the header (via super.write()) and a byte representing the subscription state */
    public void write(DataOutput out) throws IOException {
        super.write(out);
        out.writeShort(value);
    }
    
    public String toString() {
        return super.toString() + TSSEP + value;
    }

}
