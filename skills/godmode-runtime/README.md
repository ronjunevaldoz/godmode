# Godmode Runtime Skills

Project-level skills for the godmode AI routing system.

## Structure

```
godmode-runtime/
  SKILL.md                        ← main project skill (Claude standard)
  skills/
    analysis/
      analysis_skill.md
      architecture_skill.md
      code_generation_skill.md
      code_review_skill.md
      documentation_skill.md
```

All skill files follow the Claude skill standard: YAML frontmatter with `name` and `description`, followed by markdown content.

## Adding a Skill

Create a `.md` file with frontmatter in the appropriate subdirectory:

```markdown
---
name: my-skill
description: One-liner used for relevance matching — be specific
---

# My Skill
...
```

See [SKILL.md](SKILL.md) for the full project context skill.
