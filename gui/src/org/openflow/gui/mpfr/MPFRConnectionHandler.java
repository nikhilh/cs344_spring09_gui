package org.openflow.gui.mpfr;


import java.awt.AWTEvent;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.io.IOException;

import javax.swing.JCheckBox;

import org.openflow.gui.ConnectionHandler;
import org.openflow.gui.Topology;
import org.pzgui.Drawable;
import org.pzgui.DrawableEventListener;
import org.openflow.gui.mpfr.MPFRLayoutManager;
import org.openflow.gui.net.protocol.OFGMessageType;
import org.openflow.gui.net.protocol.SetMPFR;



public class MPFRConnectionHandler extends ConnectionHandler implements
		DrawableEventListener, ItemListener {

	private final MPFRLayoutManager manager;
	public MPFRConnectionHandler(MPFRLayoutManager manager, String ip, int port) {
		super(new Topology(manager), ip, port, false, false);
		this.manager = manager;
		manager.addDrawableEventListener(this);
		manager.addCheckBoxListener(this);
		
		// Clear Multipath and Fast-Reroute
		try {
			connection.sendMessage(new SetMPFR(OFGMessageType.SET_MPFR, SetMPFR.TYPE_MP, (short)0));
		}
		catch (IOException excp) {
			System.out.println(excp.toString());
		}
		try {
			connection.sendMessage(new SetMPFR(OFGMessageType.SET_MPFR, SetMPFR.TYPE_FR, (short)0));
		}
		catch (IOException excp) {
			System.out.println(excp.toString());
		}
	}

	@Override
	public void drawableEvent(Drawable d, AWTEvent e, String event) {
			//System.out.println(event);
			//System.out.println(e.toString());
			//System.out.println(d.toString());
	}

	@Override
	public void itemStateChanged(ItemEvent e) {
		//System.out.println(e.toString());
		JCheckBox cb = (JCheckBox) e.getItemSelectable();
		//System.out.println(cb.getText());
		if(cb.getText() == "Multipath Routing") {
			if(cb.isSelected()) {
				System.out.println("Multipath enabled");
				try {
					connection.sendMessage(new SetMPFR(OFGMessageType.SET_MPFR, SetMPFR.TYPE_MP, (short)1));
				}
				catch (IOException excp) {
					System.out.println(excp.toString());
				}
			}
			else {
				System.out.println("Multipath disabled");
				try {
					connection.sendMessage(new SetMPFR(OFGMessageType.SET_MPFR, SetMPFR.TYPE_MP, (short)0));
				}
				catch (IOException excp) {
					System.out.println(excp.toString());
				}
			}
		}
		else if(cb.getText() == "Fast Reroute") {
			if(cb.isSelected()) {
				System.out.println("Fast reroute enabled");
				try {
					connection.sendMessage(new SetMPFR(OFGMessageType.SET_MPFR, SetMPFR.TYPE_FR, (short)1));
				}
				catch (IOException excp) {
					System.out.println(excp.toString());
				}
			}
			else {
				System.out.println("Fast reroute disabled");
				try {
					connection.sendMessage(new SetMPFR(OFGMessageType.SET_MPFR, SetMPFR.TYPE_FR, (short)0));
				}
				catch (IOException excp) {
					System.out.println(excp.toString());
				}
			}
		}
	}
	
	
}
