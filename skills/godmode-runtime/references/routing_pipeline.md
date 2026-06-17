# Routing Pipeline

Full detail on how a user prompt moves from raw text to a selected model.

## Step-by-step flow

```
User Prompt
    │
    ▼
1. classify_intent()          ← Ollama LLM call, returns (intent, confidence 0–1)
    │
    ▼
2. calculate_confidence()     ← thresholds: <0.5 → ESCALATE, ≥0.5 → PROCEED
    │
    ▼
3. resolve_capabilities()     ← intent_map.json lookup → list[str] of required caps
    │
    ▼
4. select_best_model()        ← scores every enabled model in model_registry.yaml
    │
    ▼
5. Governance overrides       ← ESCALATE or Architecture.*/Review.* → claude_architect
    │
    ▼
Selected model_id
```

## Scoring algorithm (step 4)

For each enabled model, a score is computed:

```
score = 0

# Capability match (most important)
matches = required_caps ∩ model_caps
if matches:   score += len(matches) × 10
else:         score -= 100          # disqualifies the model

# Privacy (local-first policy)
if options.privacy == "local" and model.privacy == "local":  score += 50
if options.privacy == "cloud" and model.privacy == "cloud":  score += 10

# Multimodal
if options.multimodal and model.multimodal:     score += 50
if options.multimodal and not model.multimodal: score -= 100   # disqualifies

# Cost tier
low → +20,  medium → +10,  high → +0

# Latency tier
low → +15,  medium → +5,   high → +0

# Context window (minor tiebreaker)
score += context_window / 100_000
```

The model with the highest score wins. If the top score is negative, `claude_architect` is used as the safety net.

## Local-first heuristic

`Utility.*` and `Classification` intents automatically set `privacy: local`, boosting Ollama by 50 points. This keeps cheap, repetitive tasks off paid APIs.

## Confidence thresholds

| Score | Decision | Effect |
|-------|----------|--------|
| ≥ 0.5 | PROCEED | Use scored model |
| < 0.5 | ESCALATE | Override to `claude_architect` regardless of score |

## Governance hard-routes

Even with high confidence, these intents always go to `claude_architect`:
- `Architecture.*`
- `Review.*`

Rationale: these need deterministic quality — the registry score is bypassed entirely.
