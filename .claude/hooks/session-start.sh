#!/bin/bash
set -euo pipefail

# Only run in Claude Code on the web (remote, ephemeral container).
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Gemini CLI if not already present.
if ! command -v gemini >/dev/null 2>&1; then
  npm install -g @google/gemini-cli
fi
