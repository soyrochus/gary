# Gary - A Test  for LangGraph Agents

Gary is a little sandbox for tinkering with LangGraph agents. It takes a Java Swing form, turns it into a YAML intermediate representation (IR) using OpenAI’s GPT-4o, lets you tweak it via a command-line chat, and spits out a Python NiceGUI script. Named after SpongeBob’s snail (as a wink to an internal joke, but also in hommage to the ever resilient pet), it’s hoping to grow into something more than just a quirky experiment.

![Gary](img/gary_small.png)

## Features  
- Convert Java Swing code to YAML IR via OpenAI’s GPT-4o.  
- Interactive CLI for visualizing and modifying the IR (add, change, delete elements).  
- Generate NiceGUI Python scripts from the IR.  
- Resilient design with retries and error handling.

## Prerequisites  
- Python 3.10 or higher  
- An OpenAI API key (stored in a `.env` file)  
- `uv` (a modern Python package manager)

## Installation

****Clone the Repository**** (if applicable, or create the project locally):  

```bash 
   git clone https://github.com/yourusername/gary.git  
   cd gary
```

**Set Up the Environment with** `uv`: Install `uv` if you haven’t already; [see the home page](https://docs.astral.sh/uv/getting-started/installation/).


Then sync dependencies from `pyproject.toml`:  

```bash
 uv sync  
```

**Configure the OpenAI API Key**: Create a `.env` file in the `gary/` directory:  
```bash
echo "OPENAI_API_KEY=your-openai-key-here" > .env  
Replace `your-openai-key-here` with your actual OpenAI API key. Add `.env` to `.gitignore` to keep it private.
```

**Usage**

Gary can be run as a command-line application to process Java Swing code (from a file or string) and output NiceGUI Python code.

**Command Syntax**



uv run python -m gary <input_file_path> <outputput_file_path>

**Examples**


```bash
uv run python -m gary "d:/src/legacy/example.java" "d:/src/output/test.py"  
```
   
   * Input: A Java Swing file (e.g., `example.java`).  
   * Output: A `form.py` file in `d:/src/output/`.   

**Interactive Commands**

After running, Gary prompts for input:

* `visualize`: Display the current YAML IR.  
* `add <type> <id> <value>`: Add an element (e.g., `add button btn2 Submit`).  
* `change <id> <key> <value>`: Modify an element (e.g., `change btn1 label Go`).  
* `delete <id>`: Remove an element (e.g., `delete btn1`).  
* `generate`: Create the NiceGUI Python file.  
* `exit`: Quit the program.

**Running the Generated Code**

After generating `form.py`, run it:

```bash
uv run python d:/src/output/form.py
```

**Example Java Swing File**

You can find it in the examples/form.java file:

```java
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

```

**Dependencies**

Managed via `uv` and listed in `pyproject.toml`:

* `langgraph`: Workflow management  
* `langchain` & `langchain_openai`: LLM integration  
* `pyyaml`: YAML handling  
* `nicegui`: UI generation  
* `tenacity`: Retry logic  
* `python-dotenv`: Environment variable loading

**License**

This project is licensed under the MIT License. See the LICENSE file for details.

**Contributing**

Feel free to open issues or submit pull requests to improve Gary. Contributions are welcome!

**Author**

Created by Iwan van der Kleijn, 2025.

