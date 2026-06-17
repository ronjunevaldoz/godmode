import sys
import json
import os
from typing import Optional

# Ensure paths are correct for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import orchestrate
from metrics.metrics_engine import MetricsEngine
from memory.memory_manager import MemoryManager
from evaluation.run_routing_eval import run_eval

def run_request(prompt: str):
    """
    Executes a request through the Godmode routing system.
    """
    print(f"--- Godmode Execution ---")
    orchestrate(prompt)

def get_stats():
    """
    Retrieves and prints the current routing metrics.
    """
    mem = MemoryManager()
    met = MetricsEngine(mem)
    print(met.generate_report())

def run_evaluation():
    """
    Runs the routing accuracy evaluation suite.
    """
    print("--- Running Routing Evaluation ---")
    run_eval()

def clear_memory():
    """
    Clears the task logs.
    """
    if os.path.exists("memory/task_logs.json"):
        with open("memory/task_logs.json", "w") as f:
            json.dump([], f)
        print("Execution memory cleared.")
    else:
        print("No memory file found to clear.")

def print_help():
    print("""
Godmode CLI - AI Runtime Orchestration Interface

Usage:
  python3 godmode_cli.py run "<prompt>"  - Route and execute a prompt
  python3 godmode_cli.py stats            - Show runtime metrics and health
  python3 godmode_cli.py eval             - Run routing accuracy tests
  python3 godmode_cli.py clear           - Reset execution memory
    """)

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]

    if cmd == "run":
        if len(sys.argv) < 3:
            print("Error: Please provide a prompt. Usage: run \"your prompt\"")
            return
        run_request(" ".join(sys.argv[2:]))
    elif cmd == "stats":
        get_stats()
    elif cmd == "eval":
        run_evaluation()
    elif cmd == "clear":
        clear_memory()
    else:
        print(f"Unknown command: {cmd}")
        print_help()

if __name__ == "__main__":
    main()
