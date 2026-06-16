# Agent Model Routing System - Production Runtime

## 1. System Overview
The Agent Model Routing system is a tiered orchestration runtime designed to maximize efficiency and minimize token costs. It transforms raw user input into a structured execution plan by classifying intent, matching required capabilities to the most cost-effective model, and providing a resilience layer through retries and fallbacks.

### The Routing Flow
`User Input` $\rightarrow$ `L1 Triage (Ollama)` $\rightarrow$ `Intent Classification` $\rightarrow$ `Capability Matching` $\rightarrow$ `L2 Execution (Specialist)` $\rightarrow$ `L3 Validation (Claude)` $\rightarrow$ `Memory/Metrics Logging`

---

## 2. Intent Hierarchy
The system uses a granular intent hierarchy to ensure precise model selection.

| Domain | Intents | Primary Model |
| :--- | :--- | :--- |
| **Implementation** | `.Android`, `.KMP`, `.JNI`, `.Backend`, `.DevOps`, `.Web` | **Codex** |
| **Architecture** | `.System`, `.Mobile`, `.Agent` | **Claude** |
| **Multimodal** | `.UI`, `.Image` | **Gemini** |
| **Utility** | `.Summary`, `.Classification`, `.Extraction` | **Ollama** |
| **Documentation** | `.Spec`, `.Markdown` | **Claude/Codex** |
| **Review** | `.Code`, `.Architecture` | **Claude** |

---

## 3. Capability Matrix
Models are selected based on capabilities rather than hard-coded IDs.

| Capability | Codex | Gemini | Ollama | Claude |
| :--- | :---: | :---: | :---: | :---: |
| `code_execution` | ✅ | | | |
| `repo_awareness` | ✅ | | | |
| `multimodal_understanding` | | ✅ | | |
| `private_local_processing` | | | ✅ | |
| `cheap_batch_processing` | | ✅ | ✅ | |
| `long_context_reasoning` | | | | ✅ |
| `architecture_review` | | | | ✅ |
| `final_validation` | | | | ✅ |
| `documentation_generation` | ✅ | | | ✅ |

---

## 4. Confidence & Decision Rules
L1 Router assigns a confidence score to each intent classification:

- **Score $\ge 0.8$ (DIRECT):** Route directly to the selected L2 specialist.
- **Score $0.5 - 0.79$ (REVIEW):** Route to L2, then invoke L3 Governor (Claude) to validate the result.
- **Score $< 0.5$ (ESCALATE):** Bypass L2 and route directly to L3 Governor (Claude).

---

## 5. Resilience & Reliability

### Retry Policies
Every model attempt is governed by a retry policy defined in `configs/fallback_chain.yaml`.

| Model | Retries | Primary Fallback | Secondary Fallback |
| :--- | :---: | :--- | :--- |
| **Codex** | 1 | Claude | - |
| **Gemini** | 2 | Claude | - |
| **Ollama** | 0 | Codex | Claude |
| **Claude** | 0 | Codex | - |

### Fallback Rules
If all retries fail, the system follows the fallback chain until a successful result is obtained or a user notification is triggered.

---

## 6. Memory & Telemetry
The system tracks every routing event for continuous improvement.

- **Execution Memory:** All tasks are logged to `memory/task_logs.json` including latency, model used, intent, and success status.
- **Metrics Engine:** Aggregates data to track:
    - Model usage distribution.
    - Fallback and escalation frequencies.
    - Average confidence per intent.
    - Model success rates.

---

## 7. Example Routing Decisions

| Request | Detected Intent | Required Cap. | Final Model | Path |
| :--- | :--- | :--- | :--- | :--- |
| "Fix JNI memory leak" | `Implementation.JNI` | `code_execution` | **Codex** | Direct |
| "Design system flow" | `Architecture.System` | `architecture_review` | **Claude** | Direct |
| "UI screenshot review" | `Multimodal.UI` | `multimodal_under.` | **Gemini** | Direct |
| "Summarize local logs" | `Utility.Summary` | `private_local` | **Ollama** | Direct |
| "Review this complex PR"| `Review.Code` | `final_validation` | **Claude** | Direct |
