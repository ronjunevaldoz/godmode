# Model Registry

Full breakdown of every model in `configs/model_registry.yaml` — what it does, when it wins, whether it is enabled, and its fallback chain.

## Models

### `ollama_qwen_coder` — qwen3-coder:30b (via `OllamaUtilityAgent`)
| Field | Value |
|-------|-------|
| Provider | Ollama |
| Capabilities | `code_review`, `unit_test_generation`, `bug_fixing`, `code_improvement`, `code_execution`, `repo_awareness`, `debugging`, `refactoring` |
| Cost | low |
| Latency | medium |
| Privacy | local |
| Multimodal | no |
| Enabled | yes |

**Wins for:** implementation-heavy and review-heavy tasks that need repo awareness, debugging, refactoring, or bug fixes.
**Role:** `code_review`
**Fallback:** `codex_primary` → `claude_architect`

---

### `ollama_deepseek` — deepseek-r1:14b (via `OllamaUtilityAgent`)
| Field | Value |
|-------|-------|
| Provider | Ollama |
| Capabilities | `security_audit`, `prompt_refinement`, `long_context_reasoning`, `cheap_batch_processing`, `classification` |
| Cost | low |
| Latency | medium |
| Privacy | local |
| Multimodal | no |
| Enabled | yes |

**Wins for:** security audits, prompt refinement, and classification-heavy local tasks.
**Role:** `security_audit`
**Fallback:** `claude_architect`

---

### `ollama_gemma` — gemma4:12b (via `OllamaUtilityAgent`)
| Field | Value |
|-------|-------|
| Provider | Ollama |
| Capabilities | `research_synthesis`, `documentation_generation`, `summarization`, `cheap_batch_processing` |
| Cost | low |
| Latency | low |
| Privacy | local |
| Multimodal | no |
| Enabled | yes |

**Wins for:** Research.General, summarization, and light documentation drafts.
**Role:** `research`
**Fallback:** `claude_architect`

---

### `ollama_qwythos` — Qwythos-9B-Claude-Mythos-5-1M-GGUF:Q4_K_M (via `OllamaUtilityAgent`)
| Field | Value |
|-------|-------|
| Provider | Ollama |
| Capabilities | `research_synthesis`, `long_context_reasoning`, `summarization` |
| Cost | low |
| Latency | medium |
| Privacy | local |
| Multimodal | no |
| Enabled | no |
| Context | 1,048,576 tokens |

**Wins for:** long-context research and reasoning tasks when you want a stronger local 9B model.
**Role:** `research`
**Fallback:** `ollama_gemma` → `claude_architect`

---

### `ollama_qwen_fast` — qwen3:8b (via `OllamaUtilityAgent`)
| Field | Value |
|-------|-------|
| Provider | Ollama |
| Capabilities | `general_assistance`, `classification`, `summarization`, `private_local_processing`, `cheap_batch_processing` |
| Cost | low |
| Latency | low |
| Privacy | local |
| Multimodal | no |
| Enabled | yes |

**Wins for:** `Utility.*`, `Assistant.*`, and lightweight classification tasks.
**Role:** `assistant`
**Fallback:** `ollama_gemma` → `claude_architect`

---

### `ollama_llava` — llava:latest (via `OllamaUtilityAgent`)
| Field | Value |
|-------|-------|
| Provider | Ollama |
| Capabilities | `multimodal_understanding`, `ui_analysis`, `image_reasoning` |
| Cost | low |
| Latency | medium |
| Privacy | local |
| Multimodal | yes |
| Enabled | yes |

**Wins for:** `Multimodal.UI` and `Multimodal.Image` when local vision is sufficient.
**Role:** `vision`
**Fallback:** `gemini_vision` → `claude_architect`

---

### `claude_architect` — claude-opus-4-8 (via `ClaudeArchitectAgent`)
| Field | Value |
|-------|-------|
| Provider | Anthropic |
| Capabilities | `architecture_review`, `final_validation`, `long_context_reasoning`, `documentation_generation` |
| Cost | high |
| Latency | medium |
| Privacy | cloud |
| Multimodal | no |
| Enabled | yes |

**Wins for:** `Architecture.*`, `Review.Architecture`, `Documentation.Spec`, `UNKNOWN`, and low-confidence or escalated requests in standalone mode.
**Env var:** `ANTHROPIC_API_KEY`
**Fallback:** none

---

### `codex_primary` — gpt-4o (via `CodexEngineerAgent`)
| Field | Value |
|-------|-------|
| Provider | OpenAI |
| Capabilities | `code_execution`, `repo_awareness`, `debugging`, `refactoring` |
| Cost | high |
| Latency | medium |
| Privacy | cloud |
| Multimodal | no |
| Enabled | yes |

**Wins for:** `Implementation.*` intents that need execution, repo awareness, debugging, or refactoring.
**Env var:** `OPENAI_API_KEY`
**Fallback:** `claude_architect`

---

### `gemini_vision` — gemini-2.5-pro (via `GeminiVisionAgent`)
| Field | Value |
|-------|-------|
| Provider | Google |
| Capabilities | `multimodal_understanding`, `ui_analysis`, `image_reasoning`, `video_reasoning` |
| Cost | medium |
| Latency | medium |
| Privacy | cloud |
| Multimodal | yes |
| Enabled | no |
| Context | 1M tokens |

**Wins for:** cloud `Multimodal.*` tasks when enabled.
**Env var:** `GOOGLE_API_KEY`
**Fallback:** `ollama_llava` → `claude_architect`

---

## Fallback chains

```
ollama_qwen_coder → codex_primary → claude_architect
ollama_deepseek   → claude_architect
ollama_gemma      → claude_architect
ollama_qwythos    → ollama_gemma → claude_architect
ollama_qwen_fast  → ollama_gemma → claude_architect
ollama_llava      → gemini_vision → claude_architect
codex_primary     → claude_architect
gemini_vision     → ollama_llava → claude_architect
claude_architect  → (terminal — no fallback)
```

## Adding a model

1. Add entry to `configs/model_registry.yaml` with all required fields
2. Add capability mappings in `routing/intent_map.json` if introducing new capabilities
3. Create agent class (extend `BaseAgent` for API-backed, standalone for local)
4. Run `python3 skills/godmode-runtime/scripts/validate_registry.py` to verify no coverage gaps
5. Run `python3 godmode_cli.py eval` to confirm routing accuracy
