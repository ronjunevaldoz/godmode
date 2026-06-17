# Model Registry

Full breakdown of every model in `configs/model_registry.yaml` — what it does, when it wins, and its fallback chain.

## Models

### `codex_primary` — OpenAI gpt-4o (via `CodexEngineerAgent`)
| Field | Value |
|-------|-------|
| Provider | OpenAI |
| Capabilities | `code_execution`, `repo_awareness`, `debugging`, `refactoring` |
| Cost | high |
| Latency | medium |
| Privacy | cloud |
| Multimodal | no |

**Wins for:** `Implementation.*` intents — Android, KMP, JNI, Backend, DevOps, Web.
**Env var:** `OPENAI_API_KEY`
**Fallback:** `claude_architect`

---

### `claude_architect` — claude-sonnet-4 (via `ClaudeArchitectAgent`)
| Field | Value |
|-------|-------|
| Provider | Anthropic |
| Capabilities | `long_context_reasoning`, `architecture_review`, `documentation_generation`, `final_validation` |
| Cost | high |
| Latency | medium |
| Privacy | cloud |
| Multimodal | no |

**Wins for:** `Architecture.*`, `Review.*`, `Documentation.Spec`, `UNKNOWN`, and any ESCALATE decision.
**Also:** Hard-routed safety net when no model scores ≥ 0 or confidence < 0.5.
**Env var:** `ANTHROPIC_API_KEY`

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
| Context | 1M tokens |

**Wins for:** `Multimodal.UI`, `Multimodal.Image`. Its multimodal flag gives +50 bonus; non-multimodal models get −100 for these intents.
**Env var:** `GOOGLE_API_KEY`
**Fallback:** `claude_architect`

---

### `ollama_qwen` — qwen2.5-coder:14b (via `OllamaUtilityAgent`)
| Field | Value |
|-------|-------|
| Provider | Ollama (local) |
| Capabilities | `private_local_processing`, `cheap_batch_processing`, `classification`, `summarization` |
| Cost | low |
| Latency | low |
| Privacy | local |
| Multimodal | no |

**Wins for:** `Utility.*` intents. Local-first heuristic adds +50 privacy bonus on top of low-cost (+20) and low-latency (+15) bonuses.
**Env var:** `OLLAMA_BASE_URL` (defaults to `http://localhost:11434/api/chat`)
**Fallback:** `codex_primary` → `claude_architect`

---

## Fallback chains

```
codex_primary   → claude_architect
gemini_vision   → claude_architect
ollama_qwen     → codex_primary → claude_architect
claude_architect → (terminal — no fallback)
```

## Adding a model

1. Add entry to `configs/model_registry.yaml` with all required fields
2. Add capability mappings in `routing/intent_map.json` if introducing new capabilities
3. Create agent class (extend `BaseAgent` for API-backed, standalone for local)
4. Run `python3 skills/godmode-runtime/scripts/validate_registry.py` to verify no coverage gaps
5. Run `python3 godmode_cli.py eval` to confirm routing accuracy
