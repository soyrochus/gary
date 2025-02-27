import yaml
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.exceptions import OutputParserException
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables from .env file
load_dotenv()

# State to track data
class AgentState(Dict[str, Any]):
    java_code: str = ""
    yaml_ir: str = ""
    user_command: str = ""
    error: str = ""
    output_dir: str = ""  # Renamed to output_file in CLI, kept for consistency here

# Initialize LLM with API key from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)

# Prompt templates
parse_prompt = PromptTemplate.from_template("""
Convert this Java Swing code into a YAML intermediate representation (IR) that captures the form's structure. The IR should have a 'form' key with a 'layout' specifying the top-level layout manager (e.g., BorderLayout, GridBagLayout) and a 'components' list. Each component must include 'type' (e.g., JButton, JLabel, JPanel), a unique 'id' (derive from variable names or assign sequentially like btn1, lbl1), and 'properties' (e.g., 'text' for labels, 'label' for buttons). For containers like JPanel, include a 'layout' key and a 'children' list for nested components. Add 'constraints' for layout-specific details (e.g., region for BorderLayout, gridx/gridy for GridBagLayout). Support common components: JButton, JLabel, JTextField, JCheckBox, JRadioButton, JComboBox, JList, JTable, JTextArea, JPanel, and layouts: FlowLayout, BorderLayout, GridLayout, GridBagLayout, BoxLayout. Return the raw YAML string without Markdown formatting, code block markers (like ```), or additional text.

Java code:

{java_code}

""")

generate_prompt = PromptTemplate.from_template("""
Convert this YAML intermediate representation (IR) into a Python script using NiceGUI. The IR has a 'form' key with a 'layout' (e.g., BorderLayout, GridBagLayout) and 'components' list. Each component has 'type' (e.g., JButton, JLabel, JPanel), 'id', 'properties', and optional 'layout', 'constraints', and 'children' for nesting. Define a `create_form()` function and call `ui.run()`. Map components to NiceGUI equivalents: JButton to ui.button, JLabel to ui.label, JTextField to ui.input, JCheckBox to ui.checkbox, JRadioButton to ui.radio, JComboBox to ui.select, JList to ui.select (multiple=True if needed), JTable to ui.table, JTextArea to ui.textarea, JPanel to ui.element('div') or ui.row()/ui.column(). Use layout hints: BorderLayout as ui.column() with ordered regions, GridBagLayout as ui.grid with gridx/gridy positioning, FlowLayout as ui.row(), BoxLayout as ui.row()/ui.column() per axis, GridLayout as ui.grid. Nest children within container blocks. Return the raw Python code string without Markdown formatting, code block markers (like ```), or additional text.

YAML IR:

{yaml_ir}

""")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_llm(prompt, input_data):
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(input_data)

# Nodes
def convert_to_ir(state: AgentState) -> AgentState:
    try:
        yaml_ir = call_llm(parse_prompt, {"java_code": state["java_code"]})
        yaml_ir = yaml_ir.strip()
        if yaml_ir.startswith("```"):
            yaml_ir = yaml_ir.split("\n", 1)[1].rsplit("\n", 1)[0]
        yaml.safe_load(yaml_ir)
        state["yaml_ir"] = yaml_ir
        state["error"] = ""
    except (OutputParserException, yaml.YAMLError, Exception) as e:
        state["error"] = f"Failed to parse Java code: {str(e)}"
    return state

def user_interaction(state: AgentState) -> AgentState:
    if state["error"]:
        print("Error:", state["error"])
    else:
        print("\nCurrent IR:\n", state["yaml_ir"])
    print("Options: 'visualize', 'add <path> <type> <id> <value>', 'change <path> <key> <value>', 'delete <path>', 'generate', 'exit'")
    return state

def process_command(state: AgentState) -> AgentState:
    if not state["user_command"]:
        return state
    
    command = state["user_command"].strip().lower()
    if command == "exit":
        state["exit"] = True
        return state
    if command == "retry" and state["error"]:
        state["error"] = ""
        return state
    if state["error"]:
        print("Cannot proceed due to error. Try 'retry' or 'exit'.")
        return state

    ir = yaml.safe_load(state["yaml_ir"])
    parts = command.split(maxsplit=1)
    cmd_type = parts[0]
    args = parts[1] if len(parts) > 1 else ""

    try:
        if cmd_type == "visualize":
            pass  # Already shown in user_interaction
        elif cmd_type == "add":
            path, type_, id_, value = args.split(maxsplit=3)
            new_elem = {"type": type_, "id": id_, "properties": {"label" if type_ == "JButton" else "text": value}}
            if path:
                target = find_component(ir["form"]["components"], path.split(".")[0])
                if target and target["type"] == "JPanel":
                    target.setdefault("children", []).append(new_elem)
                else:
                    raise ValueError(f"Parent '{path}' not found or not a JPanel")
            else:
                ir["form"]["components"].append(new_elem)
        elif cmd_type == "change":
            path, key, value = args.split(maxsplit=2)
            target = find_component(ir["form"]["components"], path)
            if target:
                if key.startswith("constraints."):
                    target.setdefault("constraints", {})[key.split(".", 1)[1]] = value
                else:
                    target.setdefault("properties", {})[key] = value
            else:
                raise ValueError(f"Component '{path}' not found")
        elif cmd_type == "delete":
            path = args
            parent, target = find_parent_and_component(ir["form"]["components"], path)
            if target:
                if parent:
                    parent["children"] = [c for c in parent["children"] if c["id"] != path.split(".")[-1]]
                else:
                    ir["form"]["components"] = [c for c in ir["form"]["components"] if c["id"] != path]
            else:
                raise ValueError(f"Component '{path}' not found")
        elif cmd_type == "generate":
            state["yaml_ir"] = yaml.dump(ir)
            return state
        else:
            print("Unknown command.")
        state["yaml_ir"] = yaml.dump(ir)
    except ValueError as e:
        print(f"Invalid command: {e}")
    
    return state

def find_component(components, path):
    parts = path.split(".", 1)
    for comp in components:
        if comp["id"] == parts[0]:
            if len(parts) == 1:
                return comp
            if "children" in comp:
                return find_component(comp["children"], parts[1])
    return None

def find_parent_and_component(components, path):
    parts = path.split(".", 1)
    for i, comp in enumerate(components):
        if comp["id"] == parts[0]:
            if len(parts) == 1:
                return None, comp
            if "children" in comp:
                sub_parent, sub_comp = find_parent_and_component(comp["children"], parts[1])
                if sub_comp:
                    return comp, sub_comp
                return None, None
    return None, None

def generate_nicegui(state: AgentState) -> AgentState:
    try:
        python_code = call_llm(generate_prompt, {"yaml_ir": state["yaml_ir"]})
        python_code = python_code.strip()
        if python_code.startswith("```"):
            python_code = python_code.split("\n", 1)[1].rsplit("\n", 1)[0]
        if "ui.run()" not in python_code:
            raise ValueError("Generated code missing ui.run()")
        
        output_path = state["output_dir"]
        if os.path.exists(output_path):
            overwrite = input(f"File '{output_path}' already exists. Overwrite? (y/n): ").strip().lower()
            if overwrite != "y":
                print("Generation cancelled.")
                state["error"] = "File generation cancelled by user."
                return state

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(python_code)
        print(f"Generated NiceGUI code saved to: {output_path}")
        print("Code:\n", python_code)
    except Exception as e:
        state["error"] = f"Failed to generate NiceGUI code: {str(e)}"
    return state

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("convert", convert_to_ir)
    workflow.add_node("interact", user_interaction)
    workflow.add_node("process", process_command)
    workflow.add_node("generate", generate_nicegui)
    workflow.set_entry_point("convert")
    workflow.add_edge("convert", "interact")
    workflow.add_edge("interact", "process")
    workflow.add_conditional_edges(
        "process",
        lambda state: (
            "generate" if state["user_command"] == "generate"
            else END if state.get("exit", False)
            else "interact"
        ),
    )
    workflow.add_edge("generate", END)
    return workflow.compile(checkpointer=InMemorySaver(), interrupt_after=["interact"])

def run_agent(java_code: str, output_file: str):
    """Run the Gary agent with input Java code and output file."""
    state = AgentState(java_code=java_code, output_dir=output_file)
    thread = {"configurable": {"thread_id": "gary_thread"}}
    graph = build_graph()

    while True:
        events = graph.stream(state, thread)
        for event in events:
            if "interact" in event:
                state.update(event["interact"])
                user_input = input("Your command: ")
                state["user_command"] = user_input
                break
            elif "generate" in event:
                state.update(event["generate"])
                return  # Exit after generating
            elif "process" in event:
                state.update(event["process"])

        if state.get("exit", False):
            print("Exiting...")
            break

        # Resume after interrupt
        events = graph.stream(state, thread)

    print("Gary completed.")
    