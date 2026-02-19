#!/usr/bin/env bash
# agentainer run <task-description>
#
# Standard agent runner entrypoint. Orchestrates:
#   1. Web search (ddgr)
#   2. Headless browser fetch (playwright via agentainer-fetch)
#   3. Optional codex/claude calls
#   4. Writes artifacts under /workspace/.agentainer/runs/<timestamp>/
#
# Usage:
#   agentainer run "research playwright python examples"
#   agentainer run "fetch https://example.com and save rendered text"
set -euo pipefail

TASK="${1:-}"
if [[ -z "$TASK" ]]; then
  echo "Usage: agentainer run <task-description>" >&2
  exit 1
fi

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="/workspace/.agentainer/runs/${TIMESTAMP}"
mkdir -p "$RUN_DIR"

echo "=== Agentainer Run ==="
echo "Task : $TASK"
echo "Run  : $RUN_DIR"
echo "Time : $(date -Iseconds)"
echo ""

# ── Step 1: Web search ─────────────────────────────────────────────
echo "[1/4] Web search..."
SEARCH_QUERY="$TASK"
if command -v ddgr >/dev/null 2>&1; then
  ddgr --json -n 5 "$SEARCH_QUERY" > "$RUN_DIR/search_results.json" 2>/dev/null || true
  echo "  -> $RUN_DIR/search_results.json"
else
  echo "  -> ddgr not found, skipping web search."
fi

# ── Step 2: Browser fetch (if URL detected) ───────────────────────
echo "[2/4] Browser fetch..."
URL=$(echo "$TASK" | grep -oP 'https?://\S+' | head -1 || true)
if [[ -n "$URL" ]]; then
  if [[ -f /opt/scripts/agentainer-fetch.py ]]; then
    python3 /opt/scripts/agentainer-fetch.py "$URL" --out "$RUN_DIR/fetched_page.md" || true
    echo "  -> $RUN_DIR/fetched_page.md"
  else
    echo "  -> agentainer-fetch not available."
  fi
else
  echo "  -> No URL detected in task, skipping browser fetch."
fi

# ── Step 3: AI agent call (optional) ──────────────────────────────
echo "[3/4] AI agent (optional)..."
if [[ -n "${OPENAI_API_KEY:-}" ]] && command -v codex >/dev/null 2>&1; then
  echo "  -> codex available (OPENAI_API_KEY set). Run manually:"
  echo "     codex \"$TASK\""
else
  echo "  -> codex not configured (no OPENAI_API_KEY or binary missing)."
fi

if command -v claude >/dev/null 2>&1; then
  echo "  -> claude CLI available. Run manually:"
  echo "     claude \"$TASK\""
else
  echo "  -> claude CLI not found."
fi

# ── Step 4: Save run metadata ─────────────────────────────────────
echo "[4/4] Saving run metadata..."
cat > "$RUN_DIR/metadata.json" <<EOF
{
  "task": $(echo "$TASK" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'),
  "timestamp": "$TIMESTAMP",
  "run_dir": "$RUN_DIR",
  "url_detected": "${URL:-null}",
  "search_results": "search_results.json",
  "fetched_page": "fetched_page.md"
}
EOF
echo "  -> $RUN_DIR/metadata.json"

echo ""
echo "=== Run complete ==="
echo "Artifacts: $RUN_DIR/"
ls -la "$RUN_DIR/"
