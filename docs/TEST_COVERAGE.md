# Test Coverage Matrix

Run: `python3 -m pytest tests/ --cov --cov-report=term-missing`

Last measured: 2026-06-18 · **45 tests · 72% line coverage**

---

## Module Coverage

| Module | Lines | Covered | % | Status | Missing |
|--------|------:|--------:|--:|--------|---------|
| `agents/base/agent_base.py` | 23 | 17 | 74% | ⚠ partial | `log_event`, `validate_result_async` body |
| `agents/claude_architect.py` | 32 | 11 | 34% | ✗ low | `execute()`, `validate_result_async()` — need API key to test live |
| `agents/codex_engineer.py` | 23 | 10 | 43% | ✗ low | `execute()` — needs `OPENAI_API_KEY` |
| `agents/gemini_vision.py` | 24 | 20 | 83% | ✓ good | `execute()` stub body |
| `agents/ollama_utility.py` | 39 | 38 | 97% | ✓ excellent | line 120 (async pass-through) |
| `routing/capability_resolver.py` | 16 | 13 | 81% | ✓ good | edge cases in `load()` |
| `routing/confidence.py` | 11 | 8 | 73% | ⚠ partial | score boundary branches |
| `routing/model_selector.py` | 42 | 42 | 100% | ✓ full | — |
| `routing/preset_manager.py` | 76 | 49 | 64% | ⚠ partial | `generate_matrix()`, `apply_preset()` write path |
| `routing/quality_gate.py` | 35 | 28 | 80% | ✓ good | live LLM judge path (requires Ollama) |
| `routing/router.py` | 80 | 51 | 64% | ⚠ partial | `classify_intent()` live path, standalone escalation branches |
| `main.py` | 94 | 0 | 0% | ✗ none | full orchestrate() — integration test needed |
| `godmode_cli.py` | 113 | 0 | 0% | ✗ none | all CLI commands — integration test needed |
| `metrics/metrics_engine.py` | — | — | — | ✗ none | not yet imported in any test |
| `memory/memory_manager.py` | — | — | — | ✗ none | not yet imported in any test |

---

## Feature Coverage Matrix

| Feature | Unit tested | Integration tested | Notes |
|---------|:-----------:|:-----------------:|-------|
| **Agent init / key validation** | ✓ | — | All 3 cloud agents + Ollama |
| **Ollama execute** | ✓ (mock) | — | HTTP error, empty, valid |
| **Capability resolver** | ✓ | — | Known + unknown intents |
| **Model selector scoring** | ✓ | — | Local preference, multimodal, fallback |
| **Complexity gate keywords** | ✓ | — | Low / medium / high bands |
| **Quality gate heuristics** | ✓ | — | Refusal, short, empty, fail-open |
| **Quality gate LLM judge** | — | — | Requires live Ollama |
| **Skill mode review flags** | ✓ (mock) | — | Fix.Bug, Architecture, utility |
| **Standalone cloud escalation** | — | — | Requires live API keys |
| **Preset list / tier sort** | ✓ | — | All 5 tiers |
| **Preset auto-select** | ✓ | — | 5 RAM values |
| **Preset dry-run safety** | ✓ | — | File unchanged after dry run |
| **Preset apply (write)** | — | — | Skipped — modifies registry file |
| **Router classify_intent** | ✓ (mock) | — | Ollama call mocked |
| **Router route_request** | ✓ (mock) | — | Key result keys verified |
| **Model recommender** | — | — | Requires live Ollama |
| **MetricsEngine report** | — | — | No test yet |
| **MemoryManager log/read** | — | — | No test yet |
| **main.orchestrate()** | — | — | Full integration, needs Ollama |
| **godmode_cli commands** | — | — | Integration only |

---

## Test Files

| File | Tests | Focus |
|------|------:|-------|
| `tests/test_agents_smoke.py` | 16 | Agent init, Ollama execute, Gemini stub |
| `tests/test_config.py` | 2 | Registry YAML loading, fallback chain |
| `tests/test_routing.py` | 29 | Capability resolver, model selector, complexity gate, quality gate heuristics, preset manager, router (mocked) |

---

## Coverage Gaps by Priority

### P1 — High value, achievable without API keys

| Gap | What to add |
|-----|-------------|
| `metrics/metrics_engine.py` | Unit test `get_metrics()` and `generate_report()` with synthetic log data |
| `memory/memory_manager.py` | Unit test `log_task()` / `get_all_logs()` with a temp file |
| `routing/confidence.py` | Test all score boundary cases (PASS / ESCALATE thresholds) |
| `routing/preset_manager.generate_matrix()` | Test output contains all tier labels |
| `routing/router.py` standalone branches | Set `GODMODE_MODE=standalone` and test cloud escalation paths |

### P2 — Requires Ollama (server must be reachable)

| Gap | What to add |
|-----|-------------|
| `routing/quality_gate` LLM path | Integration test with `@pytest.mark.integration` marker |
| `routing/router.classify_intent` live | Integration test full round-trip intent classification |
| `main.orchestrate()` | End-to-end test: prompt → Ollama → memory log |

### P3 — Requires cloud API keys (skip in CI without them)

| Gap | What to add |
|-----|-------------|
| `agents/claude_architect.execute()` | `@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), ...)` |
| `agents/codex_engineer.execute()` | Same pattern with `OPENAI_API_KEY` |
| Standalone escalation full path | Needs both keys |

---

## Running Coverage

```bash
# Quick — unit tests only (no API keys, no Ollama)
python3 -m pytest tests/ --cov --cov-report=term-missing

# With HTML report
python3 -m pytest tests/ --cov --cov-report=html
open htmlcov/index.html

# Via CLI
python3 godmode_cli.py coverage
```
