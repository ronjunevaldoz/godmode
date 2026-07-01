"""Lightweight local benchmark for comparing Ollama-backed models."""

from __future__ import annotations

import time
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests
import yaml

from routing.quality_gate import assess

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "configs" / "model_registry.yaml"


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    prompt: str


DEFAULT_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        name="research",
        prompt=(
            "Summarize the tradeoffs between long-context models and retrieval-augmented "
            "generation for codebase analysis in 5 concise bullets."
        ),
    ),
    BenchmarkCase(
        name="reasoning",
        prompt=(
            "Given a 9B model, 12 GB VRAM, and 48 GB RAM, what quantization would you try first "
            "for a local Ollama deployment and why?"
        ),
    ),
]


DEFAULT_MODEL_IDS: list[str] = [
    "ollama_qwythos",
    "ollama_gemma",
    "ollama_qwen_fast",
]


def _load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def _pulled_models() -> set[str]:
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").replace("/api/chat", "")
    try:
        resp = requests.get(f"{base}/api/tags", timeout=5)
        resp.raise_for_status()
        return {m["name"] for m in resp.json().get("models", [])}
    except Exception:
        return set()


def _registry_model_name(model_id: str) -> str | None:
    registry = _load_registry()
    model = registry.get("models", {}).get(model_id, {})
    return model.get("model")


def _ollama_chat(model_name: str, prompt: str) -> str:
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").replace("/api/chat", "")
    resp = requests.post(
        f"{base}/api/chat",
        json={
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "Answer directly and concisely in under 150 words.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 256,
            },
        },
        timeout=90,
    )
    resp.raise_for_status()
    message = resp.json()["message"]
    content = message.get("content", "")
    thinking = message.get("thinking", "")
    if content.strip():
        return content
    if thinking.strip():
        return thinking
    return ""


def run_benchmark(
    model_ids: Iterable[str] | None = None,
    cases: Iterable[BenchmarkCase] | None = None,
) -> dict:
    model_ids = list(model_ids or DEFAULT_MODEL_IDS)
    cases = list(cases or DEFAULT_CASES)
    pulled = _pulled_models()

    results: list[dict] = []
    skipped: list[dict] = []

    for model_id in model_ids:
        model_name = _registry_model_name(model_id)
        if not model_name:
            skipped.append({"model_id": model_id, "reason": "unknown registry model"})
            continue
        if model_name not in pulled:
            skipped.append({"model_id": model_id, "model": model_name, "reason": "not pulled"})
            continue

        for case in cases:
            started = time.perf_counter()
            try:
                response = _ollama_chat(model_name, case.prompt)
                error = None
            except Exception as exc:
                response = ""
                error = str(exc)
            latency = time.perf_counter() - started
            score, reason = assess(case.prompt, response, model_id)
            results.append(
                {
                    "model_id": model_id,
                    "model": model_name,
                    "case": case.name,
                    "latency_s": round(latency, 2),
                    "score": round(score, 3),
                    "reason": reason if not error else error,
                    "tokens_in": len(case.prompt) // 4,
                    "tokens_out": len(response) // 4,
                }
            )

    return {
        "results": results,
        "skipped": skipped,
        "cases": [case.name for case in cases],
        "models": list(model_ids),
    }


def render_report(benchmark: dict) -> str:
    rows = benchmark["results"]
    skipped = benchmark["skipped"]
    cases = benchmark["cases"]

    by_model: dict[str, list[dict]] = {}
    for row in rows:
        by_model.setdefault(row["model_id"], []).append(row)

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════╗",
        "║                 Godmode Model Benchmark                  ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  Cases: {', '.join(cases)}",
        "",
        "  Per-model summary:",
    ]

    ranked: list[tuple[float, float, str, str]] = []
    for model_id, model_rows in sorted(by_model.items()):
        avg_score = sum(r["score"] for r in model_rows) / len(model_rows)
        avg_latency = sum(r["latency_s"] for r in model_rows) / len(model_rows)
        model_name = model_rows[0]["model"]
        ranked.append((avg_score, avg_latency, model_id, model_name))
        lines.append(
            f"    {model_id:<20} {model_name:<40} "
            f"score={avg_score:.3f} latency={avg_latency:.2f}s"
        )
        for row in model_rows:
            lines.append(
                f"      - {row['case']:<10} score={row['score']:.3f} "
                f"latency={row['latency_s']:.2f}s tokens={row['tokens_in']}/{row['tokens_out']}"
            )

    lines += ["", "  Ranking:"]
    for idx, (avg_score, avg_latency, model_id, model_name) in enumerate(
        sorted(ranked, key=lambda x: (-x[0], x[1])), start=1
    ):
        lines.append(
            f"    {idx}. {model_id} ({model_name})  avg_score={avg_score:.3f} "
            f"avg_latency={avg_latency:.2f}s"
        )

    if skipped:
        lines += ["", "  Skipped models:"]
        for item in skipped:
            model_id = item.get("model_id", "unknown")
            model_name = item.get("model", "")
            reason = item.get("reason", "")
            if model_name:
                lines.append(f"    {model_id} ({model_name}) — {reason}")
            else:
                lines.append(f"    {model_id} — {reason}")

    lines += [""]
    return "\n".join(lines)
