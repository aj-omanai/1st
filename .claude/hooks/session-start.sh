#!/bin/bash
# Session startup for Claude Code on the web.
#  1. Installs the Gemini CLI so the `gemini` command is available alongside
#     Claude Code.
#  2. Installs Python dependencies for every example MCP server so that
#     `python` can import each server module during a web session (needed for
#     syntax checks, quick smoke runs, and any test tooling added later).
set -euo pipefail

# Only run in Claude Code on the web (remote, ephemeral container); local
# sessions likely already have their own environment set up.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Gemini CLI if not already present.
if ! command -v gemini >/dev/null 2>&1; then
  npm install -g @google/gemini-cli
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Install every requirements.txt found under examples/.
# --user + --ignore-installed keeps pip from touching system apt-installed
# packages (like PyJWT) whose RECORDs it can't uninstall. Retry once
# without --break-system-packages for older pip that doesn't accept it.
PIP_FLAGS="--user --ignore-installed --no-cache-dir --disable-pip-version-check"

while IFS= read -r req; do
  echo "Installing deps from $req" >&2
  pip install $PIP_FLAGS --break-system-packages -r "$req" >&2 \
    || pip install $PIP_FLAGS -r "$req" >&2
done < <(find examples -maxdepth 3 -name requirements.txt)

# Make ~/.local/bin available for anything the user runs after startup.
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${CLAUDE_ENV_FILE:-/dev/null}"
