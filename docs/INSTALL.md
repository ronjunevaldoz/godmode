# Installation Guide

Godmode works as a standalone CLI or as a tool/skill callable from any AI agent that supports MCP or shell commands.

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) running locally or remotely (at least one model pulled)
- Optional: API keys for cloud escalation (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`)

---

## 1. Base install (all environments)

```bash
git clone https://github.com/ronjunevaldoz/godmode.git
cd godmode
pip install -r requirements.txt
python3 godmode_cli.py setup   # interactive wizard
```

The setup wizard detects Ollama, lists available models, assigns roles, and writes `.env.local`.

Then create `GODMODE_CONTEXT.md` in your project root with your stack and conventions — this is injected automatically for code tasks to prevent hallucinations:

```markdown
## Stack
- Language: Kotlin · Framework: Ktor · Database: MongoDB
- No Spring — never suggest @PreAuthorize or JDBC patterns

## Key conventions
- Auth: JWT, per-guild scoping via guildId
- Payments: atomic CAS via MongoDB updateOne
```

---

## 2. Claude Code (skill)

The fastest way to use godmode inside Claude Code.

```bash
npx skills add ronjunevaldoz/godmode   # install
npx skills update godmode-runtime      # update to latest
```

Add to your shell profile so the skill finds the CLI:
```bash
export GODMODE_PATH="$(find ~ -maxdepth 5 -name 'godmode_cli.py' -not -path '*/__pycache__/*' 2>/dev/null | head -1)"
```

Allow the CLI in Claude Code settings (Settings → Permissions → Add Rule):
```
Bash(python3 /your/path/to/godmode_cli.py *)
```

---

## 3. Claude Desktop (MCP)

The project ships a `.mcp.json` — Claude Desktop picks it up automatically when you open the godmode project folder.

For global registration (available in all projects), add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "godmode": {
      "command": "sh",
      "args": ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
    }
  }
}
```

Requires `GODMODE_PATH` in your shell profile (see section 2).

**Available MCP tools:** `run`, `run_session`, `stats`, `models`

```
godmode.run(prompt="security review", files=["src/services/SalaryServiceImpl.kt"])
godmode.stats()
```

---

## 4. Cursor

Cursor supports MCP servers via `.cursor/mcp.json` in the project root:

```json
{
  "mcpServers": {
    "godmode": {
      "command": "sh",
      "args": ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
    }
  }
}
```

Restart Cursor after adding. Godmode tools appear in the Cursor tool panel.

---

## 5. Continue (VS Code / JetBrains)

Continue supports MCP. Add to `~/.continue/config.json`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "sh",
          "args": ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
        }
      }
    ]
  }
}
```

Reload Continue after saving. Godmode tools are callable from the Continue chat panel.

---

## 6. Windsurf

Add to Windsurf MCP settings (`~/.codeium/windsurf/mcp_settings.json`):

```json
{
  "mcpServers": {
    "godmode": {
      "command": "sh",
      "args": ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
    }
  }
}
```

---

## 7. OpenAI Codex CLI

Codex CLI supports MCP servers. Add godmode to your Codex config (`~/.codex/config.toml`):

```toml
[[mcp_servers]]
name = "godmode"
command = "sh"
args = ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
```

Enable cloud escalation for best results with code tasks:
```bash
GODMODE_MODE=standalone OPENAI_API_KEY=... python3 godmode_cli.py run "task" --file src/Foo.py
```

---

## 8. Gemini CLI / Google AI Studio

Gemini CLI supports MCP via `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "godmode": {
      "command": "sh",
      "args": ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
    }
  }
}
```

To use Gemini as a cloud escalation target in standalone mode, set:
```bash
GOOGLE_API_KEY=your_key GODMODE_MODE=standalone python3 godmode_cli.py run "task"
```

---

## 9. Standalone CLI (no agent)

Use godmode directly from any terminal without an AI agent:

```bash
# Code task — always pass --file
python3 godmode_cli.py run "security review" --file src/SalaryServiceImpl.kt

# Enable cloud escalation
GODMODE_MODE=standalone ANTHROPIC_API_KEY=... python3 godmode_cli.py run "task" --file src/Foo.kt

# Track savings
python3 godmode_cli.py stats

# View failure patterns
python3 godmode_cli.py report
```

---

## Environment variables

| Variable | Default | Notes |
|----------|---------|-------|
| `GODMODE_PATH` | — | Shell env var — full path to `godmode_cli.py`; required for MCP and skill |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Base URL only — no `/api/chat` suffix |
| `OLLAMA_SERVER_RAM_GB` | auto | Improves preset auto-selection |
| `GODMODE_MODE` | `skill` | `skill` (flag bad output) or `standalone` (cloud retry) |
| `ANTHROPIC_API_KEY` | — | Standalone mode — Claude cloud fallback |
| `OPENAI_API_KEY` | — | Standalone mode — Codex cloud fallback |
| `GOOGLE_API_KEY` | — | Optional — Gemini vision model |

Set personal values in `.env.local` (gitignored, created by `setup`). Set `GODMODE_PATH` in your shell profile only — it must be available before Python starts.

---

## Verifying your install

```bash
python3 skills/godmode-runtime/scripts/health_check.py
```

Expected output:
```
  ✓  model_registry.yaml readable
  ✓  intent_map.json readable
  ✓  Ollama reachable
```

API key checks will show ✗ unless you are in standalone mode — that is expected for skill mode.
