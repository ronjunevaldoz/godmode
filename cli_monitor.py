import os
import time
import json
from datetime import datetime
from memory.memory_manager import MemoryManager
from metrics.metrics_engine import MetricsEngine

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 60)
    print(f" GODMODE | AI RUNTIME MONITOR | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def render_dashboard():
    # Initialize components
    memory = MemoryManager()
    metrics = MetricsEngine(memory)

    logs = memory.get_all_logs()

    clear_screen()
    print_header()

    # 1. Runtime Health Summary
    print("\n[ RUNTIME HEALTH ]")
    report = metrics.generate_report()
    print(report)

    # 2. Live Execution Stream (Last 5 Tasks)
    print("\n" + "-" * 60)
    print(f"{'TIMESTAMP':<20} | {'INTENT':<20} | {'MODEL':<15} | {'S'}")
    print("-" * 60)

    for log in logs[-5:]:
        ts = log.get("timestamp", "")[11:19] # Extract HH:MM:SS
        intent = log.get("intent", "Unknown")
        model = log.get("target_model", "Unknown")
        success = "✅" if log.get("success") else "❌"
        print(f"{ts:<20} | {intent[:20]:<20} | {model[:15]:<15} | {success}")

    print("\n" + "=" * 60)
    print(" Monitoring... (Ctrl+C to exit)")

def main():
    try:
        while True:
            render_dashboard()
            time.sleep(2) # Update every 2 seconds
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()
