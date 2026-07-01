import logging
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# Cloud cost reference rates (USD per 1K tokens)
CLOUD_RATES: dict[str, dict[str, float]] = {
    "claude_architect": {"input": 0.015,  "output": 0.075},
    "codex_primary":    {"input": 0.0025, "output": 0.010},
    "gemini_vision":    {"input": 0.00125,"output": 0.010},
}

# What local tasks would have cost if routed to Claude Opus (the "savings" benchmark)
CLAUDE_OPUS_RATE = {"input": 0.015, "output": 0.075}
GPT4O_RATE       = {"input": 0.0025, "output": 0.010}

LOCAL_MODEL_ROLES: dict[str, str] = {
    "qwen3-coder:30b":   "code review · bug fix · unit tests",
    "deepseek-r1:14b":   "audit · security · prompt quality",
    "gemma4:12b":        "research · docs · analysis",
    "qwen3:8b":          "assistant · classification",
    "qwen2.5-coder:14b": "code tasks (legacy)",
    "llava:latest":      "vision · UI",
}

LOCAL_MODEL_IDS = {
    "ollama_qwen_coder", "ollama_deepseek", "ollama_gemma",
    "ollama_qwen_fast",  "ollama_llava",    "ollama_qwen",
}


def _cost(tokens_in: int, tokens_out: int, rate: dict[str, float]) -> float:
    return (tokens_in / 1000 * rate["input"]) + (tokens_out / 1000 * rate["output"])


class MetricsEngine:
    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory = memory_manager

    def get_metrics(self) -> dict:
        logs = self.memory.get_all_logs()
        if not logs:
            return {"status": "No data yet — run: python3 godmode_cli.py run 'your prompt'"}

        total = len(logs)
        local_logs  = [l for l in logs if l.get("target_model") in LOCAL_MODEL_IDS]
        cloud_logs  = [l for l in logs if l.get("target_model") not in LOCAL_MODEL_IDS]

        # ── Token totals ──────────────────────────────────────────────────
        local_in  = sum(l.get("tokens_in",  0) for l in local_logs)
        local_out = sum(l.get("tokens_out", 0) for l in local_logs)
        cloud_in  = sum(l.get("tokens_in",  0) for l in cloud_logs)
        cloud_out = sum(l.get("tokens_out", 0) for l in cloud_logs)

        # ── Actual cloud spend ────────────────────────────────────────────
        cloud_cost = 0.0
        for log in cloud_logs:
            model = log.get("target_model", "")
            rate  = CLOUD_RATES.get(model, CLAUDE_OPUS_RATE)
            cloud_cost += _cost(log.get("tokens_in", 0), log.get("tokens_out", 0), rate)

        # ── Savings: what local tasks WOULD have cost on cloud ────────────
        saved_vs_opus  = _cost(local_in, local_out, CLAUDE_OPUS_RATE)
        saved_vs_gpt4o = _cost(local_in, local_out, GPT4O_RATE)

        # ── Local model breakdown ─────────────────────────────────────────
        local_by_model: dict[str, int] = {}
        for log in local_logs:
            m = log.get("ollama_model", log.get("target_model", "unknown"))
            local_by_model[m] = local_by_model.get(m, 0) + 1

        # ── Latency ───────────────────────────────────────────────────────
        local_latencies  = [l["latency"] for l in local_logs  if "latency" in l]
        cloud_latencies  = [l["latency"] for l in cloud_logs  if "latency" in l]
        avg_local_lat  = sum(local_latencies)  / len(local_latencies)  if local_latencies  else 0
        avg_cloud_lat  = sum(cloud_latencies)  / len(cloud_latencies)  if cloud_latencies  else 0

        # ── Classic routing metrics ───────────────────────────────────────
        model_counts: dict[str, int] = {}
        fallback_count = escalation_count = 0
        intent_confidence: dict[str, list[float]] = {}
        model_success: dict[str, list[int]] = {}

        for log in logs:
            model = log.get("target_model", "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1
            if log.get("fallback_used"):   fallback_count += 1
            if log.get("escalation_used"): escalation_count += 1

            intent = log.get("intent", "unknown")
            intent_confidence.setdefault(intent, []).append(log.get("confidence", 0.0))

            model_success.setdefault(model, [0, 0])
            model_success[model][1] += 1
            if log.get("success"):
                model_success[model][0] += 1

        return {
            "total_tasks": total,
            "local_tasks":  len(local_logs),
            "cloud_tasks":  len(cloud_logs),
            "local_tokens_in":  local_in,
            "local_tokens_out": local_out,
            "cloud_tokens_in":  cloud_in,
            "cloud_tokens_out": cloud_out,
            "cloud_cost_usd":      round(cloud_cost, 4),
            "saved_vs_opus_usd":   round(saved_vs_opus, 4),
            "saved_vs_gpt4o_usd":  round(saved_vs_gpt4o, 4),
            "local_model_breakdown": local_by_model,
            "avg_local_latency_s":  round(avg_local_lat, 2),
            "avg_cloud_latency_s":  round(avg_cloud_lat, 2),
            "model_usage": model_counts,
            "fallback_frequency": fallback_count / total,
            "escalation_frequency": escalation_count / total,
            "average_confidence_per_intent": {
                i: sum(s) / len(s) for i, s in intent_confidence.items()
            },
            "success_rate_per_model": {
                m: (v[0] / v[1]) if v[1] > 0 else 0
                for m, v in model_success.items()
            },
        }

    def generate_report(self) -> str:
        m = self.get_metrics()
        if "status" in m:
            return m["status"]

        t  = m["total_tasks"]
        lc = m["local_tasks"]
        cc = m["cloud_tasks"]
        lp = (lc / t * 100) if t else 0
        cp = (cc / t * 100) if t else 0

        lines = [
            "",
            "╔══════════════════════════════════════════════════════════╗",
            "║            Godmode Token Savings Dashboard               ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
            f"  Total Requests : {t}",
            "",
            f"  LOCAL  (free)  {lc:>4} requests  {lp:4.1f}%",
        ]

        for model, count in sorted(m["local_model_breakdown"].items(), key=lambda x: -x[1]):
            role = LOCAL_MODEL_ROLES.get(model, "")
            lines.append(f"    ├─ {model:<22} {count:>3} runs   {role}")

        local_tok = m["local_tokens_in"] + m["local_tokens_out"]
        lines += [
            f"  Tokens processed : ~{local_tok:,}   Cost: $0.00",
            "",
            f"  CLOUD  (paid)  {cc:>4} requests  {cp:4.1f}%",
            f"  Tokens processed : ~{m['cloud_tokens_in'] + m['cloud_tokens_out']:,}"
            f"   Cost: ${m['cloud_cost_usd']:.4f}",
            "",
            "  ──────────────────────────────────────────────────────────",
            "  ESTIMATED SAVINGS (local tasks vs cloud alternatives)",
            f"  vs Claude Opus  : ${m['saved_vs_opus_usd']:.4f}",
            f"  vs GPT-4o       : ${m['saved_vs_gpt4o_usd']:.4f}",
            "",
            f"  Avg latency  local: {m['avg_local_latency_s']:.1f}s   "
            f"cloud: {m['avg_cloud_latency_s']:.1f}s",
            "  ──────────────────────────────────────────────────────────",
            "",
            "  Model usage breakdown:",
        ]

        for model, count in sorted(m["model_usage"].items(), key=lambda x: -x[1]):
            tag = "local" if model in LOCAL_MODEL_IDS else "cloud"
            rate = m["success_rate_per_model"].get(model, 0)
            lines.append(f"    {model:<28} {count:>3} tasks  [{tag}]  {rate:.0%} success")

        if m["fallback_frequency"] > 0 or m["escalation_frequency"] > 0:
            lines += [
                "",
                f"  Fallback rate  : {m['fallback_frequency']:.1%}",
                f"  Escalation rate: {m['escalation_frequency']:.1%}",
            ]

        lines += ["", "  " + "─" * 56, _cheer(m), ""]
        return "\n".join(lines)


def _cheer(m: dict) -> str:
    """Return a single-line verdict based on local routing ratio and savings."""
    t   = m["total_tasks"]
    lp  = (m["local_tasks"] / t * 100) if t else 0
    saved = m["saved_vs_opus_usd"]
    quality_hits = round(m.get("escalation_frequency", 0) * t)

    if lp == 100:
        return f"  PERFECT  100% local — saved ~${saved:.2f} vs Claude Opus. Keep it up!"
    if lp >= 80:
        return f"  WINNING  {lp:.0f}% local — ~${saved:.2f} saved vs Opus. Nice efficiency."
    if lp >= 50:
        verdict = f"  NEUTRAL  {lp:.0f}% local, {100-lp:.0f}% cloud — ${saved:.2f} saved."
        if quality_hits:
            verdict += f" ({quality_hits} quality escalation{'s' if quality_hits > 1 else ''} — consider a bigger local model)"
        return verdict
    if lp > 0:
        return (
            f"  WARNING  Only {lp:.0f}% local — most tokens are hitting the cloud. "
            f"Run 'models research' or 'recommend' to improve routing."
        )
    return "  IN THE RED  0% local — all requests went to cloud. Check Ollama is running."
