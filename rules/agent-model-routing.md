# Agent Model Routing System - Production Runtime

## 1. System Overview
The Agent Model Routing system is a tiered orchestration runtime designed to maximize efficiency and minimize token costs. It has evolved from simple provider routing to a **Capability-Centric Model Registry** architecture.

### The Routing Flow
`User Input` $\rightarrow$ `L1 Triage (Ollama)` $\rightarrow$ `Intent Classification` $\rightarrow$ `Capability Resolution` $\rightarrow$ `Model Scoring/Selection` $\rightarrow$ `Provider Adapter Execution` $\rightarrow$ `L3 Validation` $\rightarrow$ `Memory Logging`

---

## 2. Model Registry Architecture
The system no longer routes by hard-coded provider names. Instead, it uses a `model_registry.yaml` that defines model identities, their capabilities, and performance tiers.

### Registry Components:
- **Model ID:** A unique identifier (e.g., `codex_primary`).
- **Capabilities:** A list of specific skills the model possesses (e.g., `repo_awareness`).
- **Tiers:** Cost and Latency tiers used for scoring.
- **Privacy:** Indicates if the model is `local` or `cloud`.
- **Fallbacks:** A chain of alternative models if the primary fails.

---

## 3. Intent Hierarchy & Capability Mapping
Intents are mapped to **Required Capabilities**.

| Domain | Example Intent | Required Capabilities | Primary Target |
| :--- | :--- | :--- | :--- |
| **Implementation** | `.JNI` | `code_execution`, `repo_awareness` | **Codex** |
| **Architecture** | `.System` | `architecture_review`, `long_context` | **Claude** |
| **Multimodal** | `.UI` | `multimodal_understanding`, `ui_analysis` | **Gemini** |
| **Utility** | `.Summary` | `private_local_processing` | **Ollama** |
| **Review** | `.Code` | `final_validation` | **Claude** |

---

## 4. Model Selection & Scoring
The `ModelSelector` ranks candidates using a weighted scoring system:

### Scoring Factors:
1. **Capability Match (+10 per match):** Baseline score based on how many required capabilities the model provides.
2. **Privacy Match (+50 for local if requested):** Heavily weighted if the intent implies a need for privacy/local processing.
3. **Multimodal Match (+50):** Mandatory boost if visual reasoning is required.
4. **Cost/Latency Tier (+0 to +20):** Preference for `low` $\rightarrow$ `medium` $\rightarrow$ `high`.
5. **Enabled State:** Disabled models are immediately disqualified.

**Decision:** The model with the highest total score is selected. If no model scores positively, the system defaults to `claude_architect`.

---

## 5. Resilience & Reliability

### Retry & Fallback Chain
If a model fails, the system follows the chain defined in the registry:
`Primary Model` $\rightarrow$ `Fallback 1` $\rightarrow$ `Fallback 2` $\rightarrow$ `User Notification`

### Confidence-Based Governance
- **DIRECT:** Score $\ge 0.8$. Execution is trusted.
- **REVIEW:** Score $0.5 - 0.79$. Execution is followed by a Claude-tier validation check.
- **ESCALATE:** Score $< 0.5$. Bypasses specialists and goes directly to Claude.

---

## 6. Provider Abstraction Layer
The `ProviderAdapter` decouples the routing logic from the actual API calls. It maps the selected `ModelID` to the specific `Agent` implementation class, making it trivial to swap models or providers without touching the router.

---

## 7. Memory & Telemetry
- **Execution Memory:** All tasks are logged to `memory/task_logs.json`.
- **Metrics Engine:** Tracks model usage, success rates per capability, and escalation frequency.
