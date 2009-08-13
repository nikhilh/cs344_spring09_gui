package org.openflow.gui.mpfr;

import java.awt.Color;
import java.awt.Component;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.LayoutManager;
import java.awt.event.ItemListener;

import javax.swing.BorderFactory;
import javax.swing.JPanel;
import javax.swing.JCheckBox;
import javax.swing.border.Border;


import org.pzgui.PZWindow;
import org.pzgui.layout.PZLayoutManager;

public class MPFRLayoutManager extends PZLayoutManager implements LayoutManager{

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
		mpfrPanel.setBackground(Color.YELLOW);
		Border blackline=BorderFactory.createLineBorder(Color.BLACK, 2);
		mpfrPanel.setBorder(blackline);
		mpfrPanel.setLayout(new GridBagLayout());
		
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.HORIZONTAL;
		c.gridx = 0;
		c.gridy = 0;
		mpfrPanel.add(mpCheckBox, c);
		
		c.fill = GridBagConstraints.HORIZONTAL;
		c.gridx = 1;
		c.gridy = 0;
		mpfrPanel.add(frCheckBox, c);

	}
	
	/** Overrides parent to reserve space for custom controls in the new window. */
    public void attachWindow(final PZWindow w) {
        super.attachWindow(w);
        if(getWindowIndex(w) == 0) {
            // set the title
            w.setTitle("CS344 - MultiPath Routing and Fast Reroute");
            w.setCustomTitle("CS344 - MultiPath Routing and Fast Reroute");
            
            // reserve space for a custom panel
            w.setLayout(this);
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
        int top_margin = 25;
        int bottom_margin = 10;
        mpfrPanel.setBounds(0, h + top_margin, w, RESERVED_HEIGHT_BOTTOM - (top_margin + bottom_margin));
    }
    
    public void addCheckBoxListener(ItemListener l) {
    	mpCheckBox.addItemListener(l);
    	frCheckBox.addItemListener(l);
    }

	@Override
	public void addLayoutComponent(String name, Component comp) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void layoutContainer(Container parent) {
		this.setLayoutSizeBasedOnVisibleArea();
	}

	@Override
	public Dimension minimumLayoutSize(Container parent) {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public Dimension preferredLayoutSize(Container parent) {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void removeLayoutComponent(Component comp) {
		// TODO Auto-generated method stub
		
	}


}
