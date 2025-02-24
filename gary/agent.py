import yaml
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver  # Updated import
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
    output_dir: str = ""
    waiting_for_input: bool = False

# Initialize LLM with API key from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)

# Prompts
parse_prompt = PromptTemplate.from_template("""
Convert this Java Swing code into a YAML IR with a 'form' key and 'elements' list. Each element needs 'type', 'id', and properties (e.g., 'label' for buttons, 'text' for labels). Return only the YAML string.

Java code:

{java_code}

""")

generate_prompt = PromptTemplate.from_template("""
Convert this YAML IR into a Python script using NiceGUI. Define a `create_form()` function and call `ui.run()`. Return only the Python code string.

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
        # Strip Markdown code block markers
        yaml_ir = yaml_ir.strip()
        if yaml_ir.startswith("```"):
            yaml_ir = yaml_ir.split("\n", 1)[1].rsplit("\n", 1)[0]
        yaml.safe_load(yaml_ir)  # Validate
        state["yaml_ir"] = yaml_ir
        state["error"] = ""  # Clear error on success
    except (OutputParserException, yaml.YAMLError, Exception) as e:
        state["error"] = f"Failed to parse Java code: {str(e)}"
        print(state["error"])
    return state

def user_interaction(state: AgentState) -> AgentState:
    return state

def process_command(state: AgentState) -> AgentState:
    if not state["user_command"]:
        return state
    
    command = state["user_command"].strip().lower()
    state["waiting_for_input"] = False
    
    if command == "exit":
        return {"exit": True}
    if command == "retry" and state["error"]:
        state["error"] = ""
        return state

    if state["error"]:
        print("Cannot proceed due to error. Try 'retry' or 'exit'.")
        return state

    ir = yaml.safe_load(state["yaml_ir"])
    elements = ir["form"]["elements"]

    try:
        if command == "visualize":
            pass  # IR already rendered in run_agent
        elif command.startswith("add"):
            _, type_, id_, value = command.split(maxsplit=3)
            new_elem = {"type": type_, "id": id_}
            new_elem["label" if type_ == "button" else "text"] = value
            elements.append(new_elem)
        elif command.startswith("change"):
            _, id_, key, value = command.split(maxsplit=3)
            for elem in elements:
                if elem["id"] == id_:
                    elem[key] = value
                    break
            else:
                print(f"No element with id '{id_}' found.")
        elif command.startswith("delete"):
            _, id_ = command.split(maxsplit=1)
            ir["form"]["elements"] = [e for e in elements if e["id"] != id_]
        elif command == "generate":
            state["yaml_ir"] = yaml.dump(ir)
            return state  # Let generate node handle it
        else:
            print("Unknown command.")
        state["yaml_ir"] = yaml.dump(ir)
    except ValueError as e:
        print(f"Invalid command format: {e}")
    
    return state

def generate_nicegui(state: AgentState) -> AgentState:
    try:
        python_code = call_llm(generate_prompt, {"yaml_ir": state["yaml_ir"]})
        if "ui.run()" not in python_code:
            raise ValueError("Generated code missing ui.run()")
        output_path = os.path.join(state["output_dir"], "form.py")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(python_code)
        print(f"Generated NiceGUI code saved to: {output_path}")
        print("Code:\n", python_code)
    except Exception as e:
        state["error"] = f"Failed to generate NiceGUI code: {str(e)}"
        print(state["error"])
    return state

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("convert", convert_to_ir)
    workflow.add_node("interact", user_interaction)
    workflow.add_node("process", process_command)
    workflow.add_node("generate", generate_nicegui)
    workflow.set_entry_point("convert")
    workflow.add_edge("convert", "interact")
    workflow.add_edge("interact", "process")  # Always process after interact
    workflow.add_conditional_edges(
        "process",
        lambda state: (
            "generate" if state["user_command"] == "generate"
            else END if state.get("exit", False)
            else "interact"  # Loop back for other commands
        ),
    )
    workflow.add_edge("generate", END)
    return workflow.compile(checkpointer=InMemorySaver())

def run_agent(java_code: str, output_dir: str):
    """Run the Gary agent with input Java code and output directory."""
    state = AgentState(java_code=java_code, output_dir=output_dir)
    thread = {"configurable": {"thread_id": "gary_thread"}}
    graph = build_graph()

    # Step 0 & 1: Parse Java and convert to IR
    for event in graph.stream({"java_code": java_code}, thread):
        if "convert" in event:
            state = event["convert"]
            break  # Stop after conversion

    while True:
        # Step 2: Render IR
        if state["error"]:
            print("Error:", state["error"])
            break
        print("\nCurrent IR:\n", state["yaml_ir"])

        # Step 3: Present menu
        print("Options: 'visualize', 'add <type> <id> <value>', 'change <id> <key> <value>', 'delete <id>', 'generate', 'exit'")

        # Step 4: Wait for input
        user_input = input("Your command: ")
        state["user_command"] = user_input

        # Step 5: Process input
        for event in graph.stream(state, thread):
            if "process" in event:
                state = event["process"]
                break  # Process once per command
            elif "generate" in event:
                state = event["generate"]
                break

        # Step 5a or 5b: Check next action
        if state["user_command"] == "generate":
            break  # Step 6 handled by generate node
        elif state.get("exit", False):
            print("Exiting...")
            break
        # Otherwise, loop back to Step 2

    print("Gary completed.")