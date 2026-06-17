# Agent Roles

How each agent class fits into the godmode tier system and what its contract is.

## Tier system

```
L3  ClaudeArchitectAgent    ← Governor: reasoning, validation, safety net
L2  CodexEngineerAgent      ← Specialist: code implementation
L2  GeminiVisionAgent       ← Specialist: multimodal / UI
L2  OllamaUtilityAgent      ← Specialist: local, cheap, fast
```

L3 agents validate or override L2 output. The router escalates to L3 when confidence is low or intent requires it.

---

## `BaseAgent` (ABC)

File: `agents/base/agent_base.py`

Contract all API-backed agents must satisfy:

```python
class BaseAgent(ABC):
    def __init__(self, model_id: str, api_key_env_var: str) -> None: ...
    def _validate_input(self, prompt: str) -> None: ...           # raises ValueError
    def execute(self, prompt: str, context: dict | None) -> str: ... # abstract
    async def validate_result_async(self, original_prompt, result) -> tuple[bool, str]: ...
    def log_event(self, message: str, level: str = "info") -> None: ...
```

Raises `EnvironmentError` on init if the required API key env var is unset.

Local agents (`OllamaUtilityAgent`) do **not** inherit `BaseAgent` — they don't need API key enforcement. They mirror the same interface manually.

---

## `ClaudeArchitectAgent` (L3)

File: `agents/claude_architect.py`

- `execute()` — synchronous; calls `anthropic.Anthropic.messages.create()`
- `validate_result_async()` — async; calls `anthropic.AsyncAnthropic.messages.create()`; appends an `--- ARCHITECT ASSESSMENT ---` block to the specialist result
- Default model: `claude-opus-4-8`

**Escalation trigger:** Router overrides `model_id` to `claude_architect` when:
- `conf_result["decision"] == "ESCALATE"` (confidence < 0.5)
- Intent is `Architecture.*` or `Review.*`

---

## `CodexEngineerAgent` (L2)

File: `agents/codex_engineer.py`

- `execute()` — calls `openai.OpenAI.chat.completions.create()` with a senior engineer system prompt
- `validate_result_async()` — lightweight: rejects results shorter than 10 chars
- Default model: `gpt-4o`
- Temperature: `0.3` (deterministic code generation)

---

## `GeminiVisionAgent` (L2)

File: `agents/gemini_vision.py`

- Validates `GOOGLE_API_KEY` on init (raises `EnvironmentError` if absent)
- `execute()` — stub; replace body with `google-generativeai` SDK call
- Routed exclusively for `Multimodal.*` intents via the `multimodal: true` registry flag

**To complete the implementation:**
```bash
pip install google-generativeai
```
Then replace the stub in `execute()` with:
```python
import google.generativeai as genai
genai.configure(api_key=self._api_key)
model = genai.GenerativeModel(self.model)
response = model.generate_content(prompt)
return response.text
```

---

## `OllamaUtilityAgent` (L2)

File: `agents/ollama_utility.py`

- No API key required — local model only
- `execute()` — HTTP POST to `OLLAMA_BASE_URL` (default: `http://localhost:11434/api/chat`) with 30s timeout
- Validates prompt on every call; propagates `requests.exceptions.HTTPError` on failure
- Default model: `llama3` (override via constructor)

**Local-first policy:** Utility intents automatically route here via the `privacy: local` heuristic (+50 score bonus).
