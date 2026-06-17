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
                "Classifies intent, selects the best local Ollama model, runs it, "
                "and returns the result with routing metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to route and execute",
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
                "Use the same session name across calls to maintain continuity."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to route and execute",
                    },
                    "session": {
                        "type": "string",
                        "description": "Session name for conversation history (e.g. 'myproject')",
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
        output = _run_cli("run", arguments["prompt"])
    elif name == "run_session":
        output = _run_cli("run", arguments["prompt"], "--session", arguments["session"])
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
