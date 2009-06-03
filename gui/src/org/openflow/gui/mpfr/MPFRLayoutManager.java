package org.openflow.gui.mpfr;

import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.event.ItemListener;

import javax.swing.BorderFactory;
import javax.swing.JPanel;
import javax.swing.JCheckBox;
import javax.swing.border.Border;


import org.pzgui.PZWindow;
import org.pzgui.layout.PZLayoutManager;

public class MPFRLayoutManager extends PZLayoutManager {

	public static final int RESERVED_HEIGHT_BOTTOM = 100;
	private JPanel mpfrPanel = new JPanel();
	private JCheckBox mpCheckBox = new JCheckBox("Multipath Routing", false);
	private JCheckBox frCheckBox = new JCheckBox("Fast Reroute", false);
	
	public MPFRLayoutManager() {
		super();
		/**
		   * The MPFR checkboxes.
		   */

		mpCheckBox.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 20));
		frCheckBox.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 20));
		mpfrPanel.setLayout(new FlowLayout());
		mpfrPanel.setBackground(Color.getHSBColor((float)0.0, (float)0.0, (float)0.7));
		Border blackline=BorderFactory.createLineBorder(Color.GRAY, 2);
		mpfrPanel.setBorder(blackline);
		mpfrPanel.add(mpCheckBox);
		mpfrPanel.add(frCheckBox);

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
        int margin = 10; 
        mpfrPanel.setBounds(0, h + margin, w, RESERVED_HEIGHT_BOTTOM - 2 * margin);
    }
    
    public void addCheckBoxListener(ItemListener l) {
    	mpCheckBox.addItemListener(l);
    	frCheckBox.addItemListener(l);
    }


}
