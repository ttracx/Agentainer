#!/usr/bin/env bash
set -euo pipefail

# Generate Himalaya config if env is provided
/opt/scripts/himalaya-bootstrap.sh || true

# Start sshd
if command -v service >/dev/null 2>&1; then
  sudo service ssh start || true
else
  sudo /usr/sbin/sshd || true
fi

# Start tailscaled if auth key is provided
if [[ -n "${TS_AUTHKEY:-}" ]]; then
  sudo mkdir -p /var/lib/tailscale
  sudo tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
  sleep 1
  sudo tailscale up --authkey="${TS_AUTHKEY}" --hostname="agentainer" --accept-dns=true --accept-routes=true || true
fi

exec "$@"
