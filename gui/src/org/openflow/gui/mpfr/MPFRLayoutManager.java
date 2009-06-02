package org.openflow.gui.mpfr;

import java.awt.Dimension;
import java.awt.Graphics2D;
import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemListener;

import javax.swing.JPanel;
import javax.swing.JCheckBox;


import org.pzgui.PZWindow;
import org.pzgui.layout.PZLayoutManager;

public class MPFRLayoutManager extends PZLayoutManager {

	public static final int RESERVED_HEIGHT_BOTTOM = 100;
	private JPanel mpfrPanel = new JPanel();
	JCheckBox mpCheckBox = new JCheckBox("Multipath Routing", false);
	JCheckBox frCheckBox = new JCheckBox("Fast Reroute", false);
	
	public MPFRLayoutManager() {
		super();
		/**
		   * The the checkbox.
		   */
		
		frCheckBox.setVisible(true);
		mpfrPanel.setLayout(new FlowLayout());
		mpfrPanel.add(mpCheckBox);
		mpfrPanel.add(frCheckBox);
		mpfrPanel.setVisible(true);

	}
	
	/** Overrides parent to reserve space for custom controls in the new window. */
    public void attachWindow(final PZWindow w) {
        super.attachWindow(w);
        if(getWindowIndex(w) == 0) {
            // set the title
            w.setTitle("CS344 - MultiPath Routing and Fast Reroute");
            w.setCustomTitle("CS344 - MultiPath Routing and Fast Reroute");
            
            // reserve space for a custom panel
            w.getContentPane().add(mpfrPanel);
            w.setReservedHeightBottom(RESERVED_HEIGHT_BOTTOM);
            w.setMySize(w.getWidth(), w.getHeight(), w.getZoom());
            w.setSize(w.getWidth()+1, w.getHeight()+1);
        }
    }

    /**
     * Extends the parent implementation to relayout the custom controls section
     * to fit in the new area. 
     */
    public void setLayoutSize(int w, int h) {
        super.setLayoutSize(w, h);
        int margin = 20; 
        mpfrPanel.setBounds(0, h + margin, w, RESERVED_HEIGHT_BOTTOM - 2 * margin);
    }
    
    public void addCheckBoxListener(ItemListener l) {
    	mpCheckBox.addItemListener(l);
    	frCheckBox.addItemListener(l);
    }


}
