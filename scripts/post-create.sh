#!/usr/bin/env bash
# postCreateCommand for GitHub Codespaces / devcontainers.
# Idempotent: safe to re-run.
set -euo pipefail

echo "=== Agentainer post-create ==="

# ── Playwright browsers (idempotent) ───────────────────────────────
if ! python3 -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.chromium.executable_path; p.stop()" 2>/dev/null; then
  echo "[post-create] Installing Playwright Chromium..."
  python3 -m playwright install --with-deps chromium
else
  echo "[post-create] Playwright Chromium already installed."
fi

# ── Himalaya config ────────────────────────────────────────────────
/opt/scripts/himalaya-bootstrap.sh || true

# ── Artifact directories ──────────────────────────────────────────
mkdir -p /workspace/.agentainer/{runs,downloads,screenshots,notes,transcripts}

# ── Diagnostics report ─────────────────────────────────────────────
echo ""
echo "=== Diagnostics ==="
echo "node     : $(node --version 2>/dev/null || echo 'MISSING')"
echo "python3  : $(python3 --version 2>/dev/null || echo 'MISSING')"
echo "git      : $(git --version 2>/dev/null || echo 'MISSING')"
echo "codex    : $(command -v codex 2>/dev/null && codex --version 2>/dev/null || echo 'not found (optional)')"
echo "claude   : $(command -v claude 2>/dev/null && claude --version 2>/dev/null || echo 'not found (optional)')"
echo "whisper  : $(command -v whisper 2>/dev/null && echo 'OK' || echo 'MISSING')"
echo "ddgr     : $(command -v ddgr 2>/dev/null && echo 'OK' || echo 'MISSING')"
echo "himalaya : $(command -v himalaya 2>/dev/null && himalaya --version 2>/dev/null || echo 'MISSING')"
echo "playwright: $(python3 -c 'import playwright; print("OK")' 2>/dev/null || echo 'MISSING')"
echo ""
echo "Agentainer ready."
