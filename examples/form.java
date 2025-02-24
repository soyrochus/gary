import javax.swing.*;

public class Example {
    public static void main(String[] args) {
        // Create the frame
        JFrame frame = new JFrame("Test Form");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(300, 200);

        // Add a button
        JButton button = new JButton("Submit");
        button.setBounds(100, 50, 100, 30);
        frame.add(button);

        // Add a label
        JLabel label = new JLabel("Welcome!");
        label.setBounds(100, 100, 100, 30);
        frame.add(label);

        // Set layout and make visible
        frame.setLayout(null);
        frame.setVisible(true);
    }
}