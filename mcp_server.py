#!/usr/bin/env python3
"""
Godmode MCP server — exposes godmode routing as native Claude tools.

Registration (add to .mcp.json or Claude Code MCP settings):

  {
    "mcpServers": {
      "godmode": {
        "command": "sh",
        "args": ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
      }
    }
  }

Requires GODMODE_PATH to be set in your shell profile (see README).
"""
import asyncio
import subprocess
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

CLI = Path(__file__).parent / "godmode_cli.py"

server = Server("godmode")


def _run_cli(*args: str, timeout: int = 120) -> str:
    try:
        r = subprocess.run(
            [sys.executable, str(CLI), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = r.stdout.strip()
        err = r.stderr.strip()
        if not out and err:
            return err
        if err:
            return f"{out}\n\n[stderr]\n{err}"
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return f"[godmode] Timed out after {timeout}s"
    except Exception as e:
        return f"[godmode] Error: {e}"


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="run",
            description=(
                "Route a prompt through godmode and execute it. "
                "Pass 'files' to inject source code as context — always use this "
                "for code review, security audit, bug fix, or refactor tasks. "
                "Without files the model has no code to read and will hallucinate."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The task prompt (e.g. 'security review', 'find bugs', 'refactor for readability')",
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File paths relative to the project root to inject as context (e.g. ['src/services/SalaryServiceImpl.kt'])",
                    },
                },
                "required": ["prompt"],
            },
        ),
        Tool(
            name="run_session",
            description=(
                "Route and execute a prompt with persistent multi-turn history. "
                "Prior turns in the session are injected as context. "
                "Pass 'files' to inject source code — required for code tasks."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The task prompt",
                    },
                    "session": {
                        "type": "string",
                        "description": "Session name for conversation history (e.g. 'myproject')",
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File paths relative to project root to inject as context",
                    },
                },
                "required": ["prompt", "session"],
            },
        ),
        Tool(
            name="stats",
            description=(
                "Get the godmode savings dashboard — token usage breakdown per model, "
                "estimated cost savings vs Claude Opus and GPT-4o, and efficiency verdict."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="models",
            description="List pulled Ollama models and their assigned roles in the godmode registry.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "run":
        cmd = ["run", arguments["prompt"]]
        for f in arguments.get("files", []):
            cmd += ["--file", f]
        output = _run_cli(*cmd)
    elif name == "run_session":
        cmd = ["run", arguments["prompt"], "--session", arguments["session"]]
        for f in arguments.get("files", []):
            cmd += ["--file", f]
        output = _run_cli(*cmd)
    elif name == "stats":
        output = _run_cli("stats")
    elif name == "models":
        output = _run_cli("models")
    else:
        output = f"Unknown tool: {name}"

    return [TextContent(type="text", text=output)]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
