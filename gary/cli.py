import sys
import os
from .agent import run_agent

def main():
    """CLI entry point for gary."""
    if len(sys.argv) != 3:
        print("Usage: python -m gary <input-file-path> <output-file-path>")
        print("Example: python -m gary examples/form.java output/test.py")
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Validate input file
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' does not exist or is not a file.")
        return 1
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            java_code = f.read()
    except Exception as e:
        print(f"Error: Failed to read input file '{input_file}': {str(e)}")
        return 1

    try:
        run_agent(java_code, output_file)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1