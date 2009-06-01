package org.openflow.gui.mpfr;


import java.awt.AWTEvent;

import org.openflow.gui.ConnectionHandler;
import org.openflow.gui.Topology;
import org.pzgui.Drawable;
import org.pzgui.DrawableEventListener;
import org.openflow.gui.mpfr.MPFRLayoutManager;




public class MPFRConnectionHandler extends ConnectionHandler implements
		DrawableEventListener {

	private final MPFRLayoutManager manager;
	public MPFRConnectionHandler(MPFRLayoutManager manager, String ip, int port) {
		super(new Topology(manager), ip, port, false, false);
		this.manager = manager;
		manager.addDrawableEventListener(this);
	}

	@Override
	public void drawableEvent(Drawable d, AWTEvent e, String event) {

	}

}
