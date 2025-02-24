import sys
import os
from .agent import run_agent

def main():
    """CLI entry point for gary."""
    if len(sys.argv) != 3:
        print("Usage: python -m gary <input_path_or_string> <output_dir>")
        print("Example: python -m gary d:/src/legacy/example.java d:/src/output")
        print("         python -m gary \"JButton b = new JButton();\" d:/src/output")
        return 1

    input_arg = sys.argv[1]
    output_dir = sys.argv[2]

    if os.path.isfile(input_arg):
        with open(input_arg, 'r', encoding='utf-8') as f:
            java_code = f.read()
    else:
        java_code = input_arg

    if not os.path.isdir(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return 1

    try:
        run_agent(java_code, output_dir)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1