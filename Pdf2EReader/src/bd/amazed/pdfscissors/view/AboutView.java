package bd.amazed.pdfscissors.view;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextArea;

import java.awt.Cursor;
import java.awt.Desktop;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Frame;
import java.awt.BorderLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.net.URL;

import javax.swing.JDialog;

public class AboutView extends JDialog {

	private static final long serialVersionUID = 1L;
	private String url = "www.pdfscissors.com"; // @jve:decl-index=0:
	private String versionValue = "1 beta";
	private String authorLabel = "Author";
	private String authorValue = "Amr Emam";

	private JPanel jContentPane = null;
	private JLabel image = null;
	private JPanel centerPanel = null;
	private JLabel description = null;
	private JPanel bottomPanel = null;
	private JButton button = null;
	private JButton sourceForgeButton = null;

	/**
	 * This is the default constructor
	 */
	public AboutView(Frame owner) {
		super(owner);
		initialize();
		Dimension screen = getToolkit().getScreenSize();
		this.setBounds((screen.width - getWidth()) / 2, (screen.height - getHeight()) / 2, getWidth(), getHeight());
	}

	/**
	 * This method initializes this
	 * 
	 * @return void
	 */
	private void initialize() {
		this.setSize(621, 283);
		this.setContentPane(getJContentPane());
		this.setTitle("About PDF Scissors");
		this.setResizable(false);
	}

	/**
	 * This method initializes jContentPane
	 * 
	 * @return javax.swing.JPanel
	 */
	private JPanel getJContentPane() {
		if (jContentPane == null) {
			image = new JLabel();
			URL imageURL = MainFrame.class.getResource("/res/logo.png");
			if (imageURL != null) { // image found
				image.setIcon(new ImageIcon(imageURL));
			}
			jContentPane = new JPanel();
			jContentPane.setLayout(new BorderLayout());
			jContentPane.add(image, BorderLayout.WEST);
			jContentPane.add(getCenterPanel(), BorderLayout.CENTER);
		}
		return jContentPane;
	}

	/**
	 * This method initializes centerPanel
	 * 
	 * @return javax.swing.JPanel
	 */
	private JPanel getCenterPanel() {
		if (centerPanel == null) {

			centerPanel = new JPanel();
			centerPanel.setLayout(new BorderLayout());
			centerPanel.add(getBottomPanel(), BorderLayout.SOUTH);
		}
		return centerPanel;
	}

	/**
	 * This method initializes description
	 * 
	 * @return javax.swing.JTextArea
	 */

	/**
	 * This method initializes bottomPanel
	 * 
	 * @return javax.swing.JPanel
	 */
	private JPanel getBottomPanel() {
		if (bottomPanel == null) {
			bottomPanel = new JPanel();
			bottomPanel.setLayout(new FlowLayout(FlowLayout.CENTER));
			bottomPanel.add(getButton());
		}
		return bottomPanel;
	}

	/**
	 * This method initializes button
	 * 
	 * @return javax.swing.JButton
	 */
	private JButton getButton() {
		if (button == null) {
			button = new JButton("url");
			button.setBorderPainted(false);
			button.setContentAreaFilled(false);
			button.setRolloverEnabled(true);
			button.setFocusPainted(false);
			button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
			button.addActionListener(new ActionListener() {
				@Override
				public void actionPerformed(ActionEvent e) {
					try {
						if (Desktop.isDesktopSupported()) {
							Desktop.getDesktop().browse(new java.net.URI(url));
						}
					} catch (Exception e1) {
						e1.printStackTrace();
					}
				}
			});
		}
		return button;
	}

}
