import json
import os
import re
import sys
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

_FILE_RE = re.compile(
    r'\b((?:[\w.\-]+/)*[\w.\-]+\.(?:kt|java|py|ts|tsx|js|jsx|go|rs|rb|cpp|c|h|cs|swift|json|yaml|yml|toml|sql|sh|md))\b'
)
_MAX_FILE_CHARS = 12_000


def _inject_file_context(prompt: str) -> str:
    """Scan prompt for file paths, read any that exist, prepend their content."""
    found: list[str] = []
    seen: set[str] = set()
    for match in _FILE_RE.finditer(prompt):
        path_str = match.group(1)
        if path_str in seen:
            continue
        seen.add(path_str)
        p = Path(path_str)
        if not p.is_file():
            p = Path.cwd() / path_str
        if p.is_file():
            try:
                content = p.read_text(errors="replace")[:_MAX_FILE_CHARS]
                found.append(f"<file path=\"{path_str}\">\n{content}\n</file>")
            except OSError:
                pass
    if not found:
        return prompt
    file_block = "\n\n".join(found)
    return f"{file_block}\n\n{prompt}"

_LOGS_DIR = Path(__file__).parent / "logs"
_FAILURE_LOG = _LOGS_DIR / "failures.jsonl"


def _log_failure(
    intent: str,
    model_id: str,
    prompt: str,
    response: str,
    score: float | None,
    reason: str,
) -> None:
    try:
        _LOGS_DIR.mkdir(exist_ok=True)
        entry = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "intent":  intent,
            "model":   model_id,
            "score":   round(score, 3) if score is not None else None,
            "reason":  reason,
            "prompt":  prompt[:500],
            "response": response[:2000],
        }
        with _FAILURE_LOG.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

from routing.router import route_request, SKILL_MODE
from routing.provider_adapter import ProviderAdapter
from routing.model_selector import ModelSelector
from routing.quality_gate import assess as quality_assess, should_escalate
from memory.memory_manager import MemoryManager
from metrics.metrics_engine import MetricsEngine

memory  = MemoryManager()
metrics = MetricsEngine(memory)
adapter = ProviderAdapter()
selector = ModelSelector()

with open("configs/fallback_chain.yaml") as f:
    FALLBACK_CONFIG = yaml.safe_load(f)

LOCAL_IDS: frozenset[str] = frozenset({
    "ollama_qwen_coder", "ollama_deepseek", "ollama_gemma",
    "ollama_qwen_fast", "ollama_llava", "ollama_qwen",
})

_REVIEW_HEADER = """\
╔══════════════════════════════════════════════════════════╗
║  ⚠  GODMODE · NEEDS REVIEW                              ║
║  Local model result — verify before applying             ║
╚══════════════════════════════════════════════════════════╝"""

_REVIEW_FOOTER = """\
╔══════════════════════════════════════════════════════════╗
║  END GODMODE RESULT                                      ║
╚══════════════════════════════════════════════════════════╝"""


def _wrap_review(result: str, reason: str, intent: str, model: str, score: float | None = None) -> str:
    score_line = f"  Quality score : {score:.2f}\n" if score is not None else ""
    return (
        f"{_REVIEW_HEADER}\n"
        f"  Intent        : {intent}\n"
        f"  Local model   : {model}\n"
        f"  Reason        : {reason}\n"
        f"{score_line}"
        f"\n{result}\n\n"
        f"{_REVIEW_FOOTER}"
    )


def run_with_retry(model_id: str, prompt: str, context: dict | None = None, stream: bool = False) -> Tuple[str, bool, bool]:
    policy = selector.get_fallback_chain(model_id)
    retries = 0 if model_id.startswith("ollama") else 1
    fallback_used = False

    for attempt in range(retries + 1):
        try:
            result = adapter.execute(model_id, prompt, context, stream=stream)
            return result, True, fallback_used
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed for {model_id}: {e}")

    # In skill mode, skip cloud fallbacks — Claude is the fallback
    if SKILL_MODE:
        return "Local model failed. Please handle this request directly.", False, False

    for fallback in policy:
        print(f"  Falling back to {fallback}...")
        fallback_used = True
        try:
            result = adapter.execute(fallback, prompt, context)
            return result, True, fallback_used
        except Exception as e:
            print(f"  Fallback {fallback} also failed: {e}")

    return "All attempts and fallbacks failed.", False, fallback_used


def orchestrate(user_input: str, session: str | None = None) -> None:
    print(f"\n{'─' * 60}")
    start = time.time()

    # ── Session history ───────────────────────────────────────────────────────
    context: dict = {}
    sm = None
    if session:
        from memory.session_manager import SessionManager
        sm = SessionManager()
        history = sm.truncate_to_budget(sm.load(session))
        if history:
            context["history"] = history
            print(f"  Session   : {session!r}  ({sm.turn_count(session)} prior turn(s))")
        else:
            print(f"  Session   : {session!r}  (new)")

    routing           = route_request(user_input)
    intent            = routing["intent"]
    decision          = routing["decision"]
    model_id          = routing["model_id"]
    complexity        = routing.get("complexity", "low")
    escalation_reason = routing.get("escalation_reason")
    review_required   = routing.get("review_required", False)

    # Enrich execution prompt with file contents if any paths are mentioned
    execution_prompt = _inject_file_context(user_input)
    files_injected = execution_prompt != user_input

    mode_tag = "[skill]" if SKILL_MODE else "[standalone]"
    print(f"  Mode      : {mode_tag}")
    print(f"  Intent    : {intent}  [{complexity} complexity]")
    print(f"  Model     : {model_id}  [{decision}]  confidence={routing['confidence']:.2f}")
    if files_injected:
        print(f"  Files     : injected file context into prompt")
    if escalation_reason:
        flag = "⚑ review" if SKILL_MODE else "↑ cloud"
        print(f"  {flag}  : {escalation_reason}")

    escalation_used    = bool(escalation_reason)
    quality_escalation = False
    q_score: float | None = None

    # Stream local responses unless we know upfront the result will be wrapped
    should_stream = model_id in LOCAL_IDS and not review_required
    if should_stream:
        print(f"{'─' * 60}")

    result, success, fallback_used = run_with_retry(model_id, execution_prompt, context or None, stream=should_stream)
    raw_result = result   # preserve unwrapped text for session history

    # ── Quality gate ─────────────────────────────────────────────────────────
    if success and model_id in LOCAL_IDS:
        q_score, q_reason = quality_assess(execution_prompt, result, model_id)
        if should_escalate(q_score):
            print(f"\n  ⚠ Quality gate: score={q_score:.2f} — {q_reason}")
            if SKILL_MODE:
                review_required   = True
                escalation_reason = f"quality gate ({q_reason})"
                print(f"  Flagging for review (skill mode — no cloud retry).")
            else:
                print(f"  Retrying with cloud model (codex_primary)...")
                cloud_result, cloud_success, _ = run_with_retry("codex_primary", execution_prompt)
                if cloud_success:
                    result             = cloud_result
                    raw_result         = cloud_result
                    quality_escalation = True
                    print(f"  ✓ Cloud retry succeeded.")
        else:
            print(f"  Quality gate: score={q_score:.2f} ✓")

    # ── L3 validation (standalone only) ──────────────────────────────────────
    if not SKILL_MODE and decision == "REVIEW" and success:
        print("  L3 Governor: reviewing specialist output...")
        _, result = adapter.validate_result(model_id, user_input, result)
        raw_result = result

    # ── Wrap flagged results for Claude to review ─────────────────────────────
    if review_required and success:
        result = _wrap_review(
            result,
            reason=escalation_reason or "flagged",
            intent=intent,
            model=model_id,
            score=q_score if should_escalate(q_score or 1.0) else None,
        )
        _log_failure(intent, model_id, user_input, raw_result, q_score, escalation_reason or "flagged")

    latency = time.time() - start

    tokens_in, tokens_out = adapter.get_token_counts(model_id)
    if not tokens_in:
        tokens_in  = len(user_input) // 4
        tokens_out = len(result) // 4

    memory.log_task({
        "user_input":         user_input,
        "intent":             intent,
        "target_model":       model_id,
        "ollama_model":       getattr(adapter._agents.get(model_id), "model", None),
        "confidence":         routing["confidence"],
        "latency":            latency,
        "success":            success,
        "fallback_used":      fallback_used,
        "escalation_used":    escalation_used,
        "review_required":    review_required,
        "tokens_in":          tokens_in,
        "tokens_out":         tokens_out,
        "quality_escalation": quality_escalation,
        "session":            session,
        "notes": f"Decision: {decision}" + (f" | {escalation_reason}" if escalation_reason else ""),
    })

    # ── Persist session turn ──────────────────────────────────────────────────
    if sm and session and success:
        sm.append(session, "user", user_input)
        sm.append(session, "assistant", raw_result)

    # ── Output ───────────────────────────────────────────────────────────────
    if not should_stream:
        print(f"\n{result}")
    elif review_required:
        # Was streamed but quality gate flagged it — print the wrapper after
        print(f"\n{result}")

    print(f"\n  ✓ {latency:.1f}s  |  tokens in={tokens_in} out={tokens_out}  |  "
          f"fallback={fallback_used}  review={review_required}")
    print(f"{'─' * 60}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        orchestrate(" ".join(sys.argv[1:]))
    else:
        print("Usage: python3 main.py 'your prompt'")
