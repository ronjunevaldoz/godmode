# Godmode Skills

Skills extend the godmode agent system with domain knowledge loaded directly into context.

## Structure

```
skills/
  godmode-runtime/     ← project skill (SKILL.md = Claude skill standard)
    SKILL.md
    __init__.py
skills-lock.json       ← pinned skill versions and hashes
```

## Installing Skills

All skills are managed via the `npx skills` CLI, which installs to `~/.agents/skills/` and symlinks into each supported agent automatically.

### Universal install (recommended)

```bash
npx skills add <owner/repo@skill-name> -g -y
```

The `-g` flag installs globally (user-level). `-y` skips interactive prompts.

---

### Claude Code

Skills are symlinked into `~/.claude/skills/`. Claude Code loads any `SKILL.md` file from that directory automatically at the start of a session.

```bash
# Install
npx skills add <owner/repo@skill-name> -g -y

# Verify
ls ~/.claude/skills/
```

To reference a local project skill directly, add its path to your `CLAUDE.md`:

```markdown
# CLAUDE.md
See [skills/godmode-runtime/SKILL.md](skills/godmode-runtime/SKILL.md) for project context.
```

---

### Gemini CLI

Skills are installed as universal copies under `~/.agents/skills/` and picked up by Gemini CLI on startup.

```bash
# Install
npx skills add <owner/repo@skill-name> -g -y

# Verify
ls ~/.agents/skills/
```

To add a project-local skill for Gemini, create a `.geminirc` or `GEMINI.md` in the project root and reference the skill content directly — Gemini CLI reads these on startup.

---

### Codex (OpenAI)

Skills install as universal copies under `~/.agents/skills/`. Codex picks them up automatically.

```bash
# Install
npx skills add <owner/repo@skill-name> -g -y

# Verify
ls ~/.agents/skills/
```

For project-scoped context, add a `AGENTS.md` file at the repo root — Codex reads it automatically when running in that directory.

---

## Locking skills

After installing, commit `skills-lock.json` to pin exact versions:

```bash
# skills-lock.json is auto-updated by npx skills add
git add skills-lock.json
git commit -m "chore: pin skill versions"
```

## Available skills in this project

| Skill | Scope | Description |
|-------|-------|-------------|
| [`godmode-runtime`](godmode-runtime/SKILL.md) | project | Godmode routing, intent hierarchy, agent roles, and CLI |
| [`skill-creator`](https://skills.sh/anthropics/skills/skill-creator) | global | Create new skills from scratch |
| [`python-best-practices`](https://skills.sh/rohitg00/awesome-claude-code-toolkit/python-best-practices) | global | Python 3.12+ type hints, async, testing patterns |

## Creating a new skill

A skill is a single `SKILL.md` file with frontmatter:

```markdown
---
name: my-skill
description: One-liner used for relevance matching — be specific
---

# My Skill

## When to Use
...

## Content
...
```

To scaffold and publish:

```bash
npx skills init my-skill
npx skills publish
```
