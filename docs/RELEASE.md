# Release Process

Godmode follows [Semantic Versioning](https://semver.org/):

- **PATCH** `0.5.x` — bug fixes, documentation, test additions
- **MINOR** `0.x.0` — new features, new commands, new agent integrations
- **MAJOR** `x.0.0` — breaking changes to CLI flags, config format, or MCP tool signatures

---

## Cutting a release

### 1. Update version

Edit `version.py`:
```python
__version__ = "0.6.0"
```

### 2. Update CHANGELOG.md

Add a new section at the top:
```markdown
## [0.6.0] — YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

### 3. Run the full test suite

```bash
python3 -m pytest tests/ -m "not integration" -q
```

All tests must pass before tagging.

### 4. Commit

```bash
git add version.py CHANGELOG.md
git commit -m "Release: bump to v0.6.0"
```

### 5. Tag and push

```bash
git tag v0.6.0
git push origin main --tags
```

The CI badge updates automatically on push. The GitHub release is created from the tag.

### 6. Create GitHub release

```bash
gh release create v0.6.0 \
  --title "v0.6.0 — <short description>" \
  --notes "$(sed -n '/## \[0.6.0\]/,/## \[0.5/p' CHANGELOG.md | head -n -1)"
```

### 7. Update the skill

After pushing, users update their installed skill with:
```bash
npx skills update godmode-runtime
```

The skill is auto-indexed on skills.sh — no manual submission needed.

---

## Registry submissions

### skills.sh (auto-indexed)

No action needed. skills.sh indexes via install telemetry — the skill updates automatically when users run `npx skills update`.

To verify the published version:
```bash
npx skills find godmode
```

### PyPI (future)

Not yet published. When ready:
```bash
pip install build twine
python -m build
twine upload dist/*
```

---

## What NOT to include in a release

- `.env.local` — personal credentials, gitignored
- `logs/failures.jsonl` — personal runtime data, gitignored
- `memory/task_logs.json` — personal usage data
- `GODMODE_CONTEXT.md` — per-project context, gitignored

---

## Version compatibility

| godmode | Python | Ollama API |
|---------|--------|------------|
| 0.5.x   | 3.10+  | /api/chat v1 |
| 0.4.x   | 3.10+  | /api/chat v1 |

Breaking changes to `configs/model_registry.yaml` or `routing/intent_map.json` format are noted in CHANGELOG with migration steps.
