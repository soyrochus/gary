import yaml
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
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
    waiting_for_input: bool = False  # Added to signal interrupt

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
        yaml.safe_load(yaml_ir)
        state["yaml_ir"] = yaml_ir
        print("Parsed to YAML IR:\n", yaml_ir)
    except (OutputParserException, yaml.YAMLError, Exception) as e:
        state["error"] = f"Failed to parse Java code: {str(e)}"
        print(state["error"])
    return state

def user_interaction(state: AgentState) -> AgentState:
    if state["error"]:
        print("Error:", state["error"])
        print("What would you like to do? (e.g., retry, exit)")
    else:
        print("\nCurrent IR:\n", state["yaml_ir"])
        print("Options: 'visualize', 'add <type> <id> <value>', 'change <id> <key> <value>', 'delete <id>', 'generate', 'exit'")
    state["waiting_for_input"] = True  # Signal interrupt
    return state

def process_command(state: AgentState) -> AgentState:
    if not state["user_command"]:
        return state  # No command yet, wait for input
    
    command = state["user_command"].strip().lower()
    state["waiting_for_input"] = False  # Reset interrupt flag
    
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
            print("Visualizing:\n", state["yaml_ir"])
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
            return generate_nicegui(state)
        else:
            print("Unknown command.")
    except ValueError as e:
        print(f"Invalid command format: {e}")
    
    state["yaml_ir"] = yaml.dump(ir)
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
    workflow.add_conditional_edges(
        "interact",
        lambda state: "process" if state["waiting_for_input"] else "interact",
    )
    workflow.add_conditional_edges(
        "process",
        lambda state: (
            END if state.get("exit", False) or state["user_command"] == "generate"
            else "convert" if state["user_command"] == "retry" and state["error"]
            else "interact"
        ),
    )
    workflow.add_edge("generate", END)
    return workflow.compile(checkpointer=MemorySaver())

def run_agent(java_code: str, output_dir: str):
    """Run the Gary agent with input Java code and output directory."""
    state = AgentState(java_code=java_code, output_dir=output_dir)
    thread = {"configurable": {"thread_id": "gary_thread"}}
    graph = build_graph()

    while True:
        events = graph.stream(state, thread)
        for event in events:
            if event.get("interact") and state["waiting_for_input"]:
                user_input = input("Your command: ")
                state["user_command"] = user_input
                break
        else:
            break  # Exit if workflow completes
        # Resume with user input
        events = graph.stream(state, thread)
        for event in events:
            pass
        state = graph.get_state(thread).values

    print("Gary completed.")