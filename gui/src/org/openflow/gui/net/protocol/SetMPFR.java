package org.openflow.gui.net.protocol;

import java.io.DataOutput;
import java.io.IOException;

public class SetMPFR extends OFGMessage {
	
	public static final short TYPE_MP = 0x0;
	public static final short TYPE_FR = 0x1;
	
	/**
	 * Value sent to the backend server
	 * should be 0 or 1
	 */
	public final short value;
	public final short subtype;

	public SetMPFR(OFGMessageType t, short subtype, short value) {
		super(t, 0);
		this.value = value;
		this.subtype = subtype;
		
	}
	
	/** This returns the message length */
    public int length() {
        return super.length() + 4;
    }
    
    /** Writes the header (via super.write()) and a byte representing the subscription state */
    public void write(DataOutput out) throws IOException {
        super.write(out);
        out.writeShort(subtype);
        out.writeShort(value);
    }
    
    public String toString() {
        return super.toString() + TSSEP + subtype + TSSEP + value;
    }

}
