#!/usr/bin/env bash
# imsg-remote.sh - Agentainer-side convenience wrapper for iMessage bridge.
# Calls imsg-bridge on a macOS host over Tailscale SSH.
#
# Config (env vars):
#   IMSG_HOST    - Tailscale hostname or IP of the macOS host (default: mac-mini)
#   IMSG_USER    - SSH user on the macOS host (default: current user)
#
# Usage:
#   imsg-remote send "+15551234567" "Hello from Agentainer"
#   imsg-remote list 10
#   imsg-remote watch
set -euo pipefail

IMSG_HOST="${IMSG_HOST:-mac-mini}"
IMSG_USER="${IMSG_USER:-$(whoami)}"

ssh -o ConnectTimeout=5 "${IMSG_USER}@${IMSG_HOST}" "imsg-bridge $*"
