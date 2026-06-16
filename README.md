# Godmode: Agent Model Routing System

A production-ready agent orchestration runtime designed to optimize LLM token usage and efficiency through tiered intent-based routing.

## 🚀 Overview

Godmode uses a three-tier hierarchy to ensure the right model handles the right task at the right cost:

1. **L1 (Triage):** Ollama (Local) classifies the user's intent.
2. **L2 (Specialists):** Codex (Code), Gemini (Visual), or Ollama (Utility) execute the task.
3. **L3 (Governor):** Claude performs high-level reasoning, planning, and final validation.

## 🛠️ Architecture

### Routing Flow
`User Input` $\rightarrow$ `L1 Triage` $\rightarrow$ `Capability Matching` $\rightarrow$ `L2 Execution` $\rightarrow$ `L3 Validation` $\rightarrow$ `Memory Logging`

### Component Breakdown
- **`routing/`**: Contains the triage logic, intent mappings, and capability matrices.
- **`agents/`**: Wrappers for different LLM providers.
- **`memory/`**: Execution logs and persistence.
- **`metrics/`**: Telemetry and performance analysis.
- **`configs/`**: Retry policies, fallback chains, and model limits.
- **`evaluation/`**: Testing suite for routing accuracy.

## 📋 Getting Started

### Prerequisites
- Python 3.10+
- Ollama running locally (`llama3`)
- API keys for Claude, Codex, and Gemini (configured in environment variables)

### Installation
```bash
git clone https://github.com/ronjunevaldoz/godmode.git
cd godmode
pip install -r requirements.txt # (Note: You may need to create this file)
```

### Usage
Run the orchestrator from the terminal:
```bash
python3 main.py "Your request here"
```

## 📈 Telemetry & Evaluation
- **Run Eval:** `python3 evaluation/run_routing_eval.py`
- **View Logs:** Check `memory/task_logs.json`

## 📜 Routing Rules
Detailed routing rules, intent hierarchies, and capability matrices can be found in `rules/agent-model-routing.md`.
