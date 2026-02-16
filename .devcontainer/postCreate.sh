#!/usr/bin/env bash
set -euo pipefail

echo "==> Devcontainer postCreate: ensuring uv exists"

# Ensure curl exists (usually does, but safe)
if ! command -v curl >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y curl
fi

# Install uv if missing
if ! command -v uv >/dev/null 2>&1; then
  echo "==> Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Make sure uv is on PATH for this script run
export PATH="$HOME/.local/bin:$PATH"

echo "==> uv location: $(command -v uv)"
uv --version

echo "==> Syncing dependencies in scheduler_core/"
cd /workspaces/2026sp-420-Maverick/scheduler_core
uv sync

echo "==> Done. Venv should be at scheduler_core/.venv"
