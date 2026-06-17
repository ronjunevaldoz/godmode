# Test Coverage Matrix

Run: `python3 godmode_cli.py coverage`

Last measured: 2026-06-18 · **121 tests · 72% line coverage**
_(72% overall is dragged down by cloud agents (34-43%) and model_recommender (16%)
which require live API keys / Ollama. Core routing and memory layers are at 86-100%.)_

---

## Module Coverage

| Module | % | Status | Notes |
|--------|--:|--------|-------|
| `memory/memory_manager.py` | 100% | ✓ full | — |
| `routing/confidence.py` | 100% | ✓ full | All 3 decision branches + all boundaries |
| `routing/model_selector.py` | 100% | ✓ full | — |
| `routing/quality_gate.py` | 100% | ✓ full | Heuristics + fail-open path |
| `routing/preset_manager.py` | 97% | ✓ excellent | Write path + matrix covered; 2 lines in `get_preset` edge case |
| `metrics/metrics_engine.py` | 98% | ✓ excellent | All cheer branches; 2 uncovered lines in report footer |
| `agents/ollama_utility.py` | 97% | ✓ excellent | async pass-through stub only |
| `routing/provider_adapter.py` | 86% | ✓ good | Lazy factories covered; `validate_result` asyncio path untested |
| `routing/router.py` | 89% | ✓ good | Both skill + standalone branches covered |
| `main.py` | 77% | ⚠ partial | Quality gate cloud-retry path + standalone L3 governor |
| `godmode_cli.py` | 50% | ⚠ partial | `cmd_run`, `cmd_eval`, `cmd_recommend`, `cmd_coverage` untested (require live services) |
| `agents/gemini_vision.py` | 83% | ⚠ partial | `execute()` stub body |
| `agents/base/agent_base.py` | 74% | ⚠ partial | `log_event`, `validate_result_async` default body |
| `routing/capability_resolver.py` | 81% | ⚠ partial | `_load()` error branch |
| `routing/model_recommender.py` | 16% | ✗ low | Requires live Ollama + system RAM calls |
| `agents/claude_architect.py` | 34% | ✗ low | `execute()` needs `ANTHROPIC_API_KEY` |
| `agents/codex_engineer.py` | 43% | ✗ low | `execute()` needs `OPENAI_API_KEY` |

---

## Feature Coverage Matrix

| Feature | Unit | Integration | Notes |
|---------|:----:|:-----------:|-------|
| Agent init / key validation | ✓ | — | All 3 cloud + Ollama |
| Ollama execute | ✓ mock | ✓ live | HTTP error, empty, valid, token counts |
| Capability resolver | ✓ | — | Known + unknown intents |
| Model selector scoring | ✓ | — | Local, multimodal, no-match fallback |
| Confidence boundaries | ✓ | — | 0.0 / 0.499 / 0.5 / 0.799 / 0.8 / 1.0 |
| Complexity gate keywords | ✓ | — | Low / medium / high, case-insensitive |
| Quality gate heuristics | ✓ | — | Refusal, short, empty, fail-open |
| Quality gate LLM judge | — | — | Requires live Ollama |
| Skill mode review flags | ✓ mock | ✓ live | Fix.Bug, Architecture, utility |
| Standalone cloud escalation | ✓ | — | Fix.Bug→codex, Arch→claude, low-conf→claude |
| Preset list / tier sort | ✓ | — | All 5 tiers present and sorted |
| Preset auto-select | ✓ | — | 6→6gb, 10→8gb, 20→16gb, 40→32gb, 80→64gb |
| Preset dry-run safety | ✓ | — | File unchanged after dry run |
| Preset apply (write) | ✓ | — | File patched; second apply = no changes |
| Preset generate_matrix | ✓ | — | All tier labels and role names present |
| Provider adapter lazy init | ✓ | — | Cache, unknown model, cloud key errors |
| Token count extraction | ✓ | — | After execute, before execute |
| MemoryManager persist | ✓ | — | Log, timestamp, multi-log, corrupted file |
| MemoryManager query | ✓ | — | Filter by model, empty result |
| MetricsEngine calculations | ✓ | — | Cost, savings, split, latency, rates |
| MetricsEngine report | ✓ | — | Dashboard header, savings lines, model rows |
| **Cheer / verdict** | ✓ | — | PERFECT / WINNING / NEUTRAL / WARNING / IN THE RED |
| Router route_request shape | ✓ mock | — | All required keys present |
| main.orchestrate() contract | ✓ mock | ✓ live | Log shape, review flag, NEEDS REVIEW header |
| godmode_cli preset commands | ✓ | — | list, show, unknown subcommand |
| godmode_cli models (offline) | ✓ | — | Graceful error when Ollama down |
| godmode_cli help / unknown cmd | ✓ | — | All commands listed, exit code 1 |
| Model recommender | — | — | Requires live Ollama + server RAM |

---

## Test Files

| File | Tests | Focus |
|------|------:|-------|
| `tests/test_agents_smoke.py` | 16 | Agent init, Ollama execute, Gemini stub |
| `tests/test_config.py` | 2 | Registry YAML loading, fallback chain |
| `tests/test_routing.py` | 29 | Capability resolver, model selector, complexity gate, quality gate heuristics, preset manager, router (mocked) |
| `tests/test_memory_metrics.py` | 36 | MemoryManager, MetricsEngine, `_cost()`, `calculate_confidence()` |
| `tests/test_integration.py` | 8 | orchestrate() unit (mocked) + live Ollama (`@pytest.mark.integration`) |
| `tests/test_coverage_gaps.py` | 30 | ProviderAdapter, router standalone branches, preset write path, cheer branches, CLI commands |

---

## Remaining Gaps (not worth closing without live services)

| Gap | Blocker |
|-----|---------|
| `agents/claude_architect.execute()` | `ANTHROPIC_API_KEY` |
| `agents/codex_engineer.execute()` | `OPENAI_API_KEY` |
| `routing/model_recommender.py` | Live Ollama + `sysctl` / `/proc/meminfo` |
| `godmode_cli.cmd_run / cmd_eval / cmd_recommend` | Live Ollama |
| `main.py` standalone L3 governor path | `ANTHROPIC_API_KEY` |

---

## Running Coverage

```bash
# Quick (no API keys, no Ollama needed)
python3 godmode_cli.py coverage

# Skip live integration tests
python3 -m pytest tests/ -m "not integration" --cov --cov-report=term-missing

# HTML report
python3 -m pytest tests/ --cov --cov-report=html && open htmlcov/index.html

# Only integration tests (Ollama must be up)
python3 -m pytest tests/ -m integration -v
```
