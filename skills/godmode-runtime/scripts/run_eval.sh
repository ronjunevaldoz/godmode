#!/usr/bin/env bash
# Run the godmode routing evaluation suite.
# Usage: bash skills/godmode-runtime/scripts/run_eval.sh
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || dirname "$(dirname "$(dirname "$(dirname "$0")")")")"
cd "$REPO_ROOT"

echo "Running godmode routing eval..."
python3 godmode_cli.py eval
