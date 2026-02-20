#!/usr/bin/env bash
# One-paste bootstrap to create the full Agentainer repo locally.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ttracx/Agentainer/main/bootstrap.sh | bash
# or
#   bash bootstrap.sh
set -euo pipefail

REPO_DIR="Agentainer"

echo "Creating ${REPO_DIR}/..."
mkdir -p "${REPO_DIR}"/{scripts,dotfiles,tests,.github/workflows,.devcontainer,.agentainer/{runs,downloads,screenshots,notes,transcripts},tools/imsg-bridge}
cd "${REPO_DIR}"

# ── Dockerfile ─────────────────────────────────────────────────────
cat > Dockerfile <<'DOCKERFILE'
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000
ARG NODE_MAJOR=20
ARG HIMALAYA_VERSION=0.7.3

ENV TZ=America/Chicago \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/home/dev/.local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg lsb-release \
    git openssh-client openssh-server \
    build-essential pkg-config \
    python3 python3-pip python3-venv python3-dev \
    jq ripgrep fd-find unzip zip \
    tmux zsh vim nano \
    sqlite3 postgresql-client \
    iputils-ping dnsutils netcat-openbsd \
    shellcheck \
    ffmpeg \
    xz-utils \
    sudo \
  && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/nodesource.gpg; \
  echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
    > /etc/apt/sources.list.d/nodesource.list; \
  apt-get update; \
  apt-get install -y --no-install-recommends nodejs; \
  npm i -g pnpm@latest yarn@latest; \
  rm -rf /var/lib/apt/lists/*

RUN set -eux; \
  install -m 0755 -d /usr/share/keyrings; \
  curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.noarmor.gpg \
    -o /usr/share/keyrings/tailscale-archive-keyring.gpg; \
  curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.tailscale-keyring.list \
    -o /etc/apt/sources.list.d/tailscale.list; \
  apt-get update; \
  apt-get install -y --no-install-recommends tailscale; \
  rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends ddgr \
  && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd

RUN python3 -m pip install --break-system-packages --upgrade pip setuptools wheel \
 && python3 -m pip install --break-system-packages \
    black ruff mypy pytest pytest-cov \
    ipython rich httpx requests \
    pre-commit \
    openai-whisper \
    playwright \
 && rm -rf /root/.cache/pip

RUN python3 -m playwright install --with-deps chromium

RUN npm i -g @openai/codex

RUN set -eux; \
  curl -fsSL https://claude.ai/install.sh | bash || true

RUN set -eux; \
  arch="$(dpkg --print-architecture)"; \
  case "$arch" in \
    amd64) him_arch="linux-x86_64" ;; \
    arm64) him_arch="linux-aarch64" ;; \
    *) echo "unsupported arch: $arch" && exit 1 ;; \
  esac; \
  url="https://github.com/pimalaya/himalaya/releases/download/v${HIMALAYA_VERSION}/himalaya-${him_arch}.tar.gz"; \
  curl -fsSL "$url" -o /tmp/himalaya.tgz; \
  tar -xzf /tmp/himalaya.tgz -C /tmp; \
  install -m 0755 /tmp/himalaya /usr/local/bin/himalaya; \
  rm -rf /tmp/himalaya*; \
  himalaya --version

RUN set -eux; \
  groupadd --gid ${USER_GID} ${USERNAME}; \
  useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/zsh ${USERNAME}; \
  mkdir -p /workspace; chown -R ${USERNAME}:${USERNAME} /workspace; \
  mkdir -p /var/run/sshd; \
  sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config; \
  sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config; \
  echo "PrintMotd yes" >> /etc/ssh/sshd_config

RUN set -eux; \
  echo "${USERNAME} ALL=(root) NOPASSWD: /usr/sbin/sshd, /usr/bin/tailscaled, /usr/bin/tailscale, /usr/bin/service" \
    > /etc/sudoers.d/${USERNAME}; \
  chmod 0440 /etc/sudoers.d/${USERNAME}

COPY --chown=dev:dev scripts/ /opt/scripts/
COPY --chown=dev:dev dotfiles/.zshrc /home/dev/.zshrc
COPY --chown=dev:dev dotfiles/motd.txt /etc/motd

RUN set -eux; \
  chmod +x /opt/scripts/*.sh /opt/scripts/*.py || true; \
  ln -sf /opt/scripts/agentainer-run.sh /usr/local/bin/agentainer; \
  ln -sf /opt/scripts/agentainer-fetch.py /usr/local/bin/agentainer-fetch

RUN mkdir -p /workspace/.agentainer/{runs,downloads,screenshots,notes,transcripts} \
  && chown -R ${USERNAME}:${USERNAME} /workspace/.agentainer

USER ${USERNAME}
WORKDIR /workspace

ENTRYPOINT ["/opt/scripts/entrypoint.sh"]
CMD ["zsh"]
DOCKERFILE

# ── docker-compose.yml ─────────────────────────────────────────────
cat > docker-compose.yml <<'COMPOSE'
services:
  agentainer:
    build:
      context: .
      dockerfile: Dockerfile
    image: agentainer:latest
    container_name: agentainer
    working_dir: /workspace
    read_only: true
    volumes:
      - ./:/workspace
      - agentainer-home:/home/dev
      - /tmp
    tmpfs:
      - /tmp:size=512M
      - /run:size=64M
      - /var/run/sshd:size=1M
    environment:
      - TZ=America/Chicago
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - TS_AUTHKEY=${TS_AUTHKEY:-}
      - O365_EMAIL=${O365_EMAIL:-}
      - O365_PASSWORD=${O365_PASSWORD:-}
      - HIMALAYA_SENDER_NAME=${HIMALAYA_SENDER_NAME:-}
      - HIMALAYA_SIGNATURE=${HIMALAYA_SIGNATURE:-}
      - HIMALAYA_PASSWORD_CMD=${HIMALAYA_PASSWORD_CMD:-}
    ports:
      - "2222:22"
    tty: true
    stdin_open: true
    init: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
      - DAC_OVERRIDE
      - NET_ADMIN
      - NET_RAW
    devices:
      - /dev/net/tun:/dev/net/tun
    healthcheck:
      test: ["CMD", "bash", "-lc", "/opt/scripts/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  agentainer-dockerhost:
    extends:
      service: agentainer
    container_name: agentainer-dh
    profiles:
      - dockerhost
    volumes:
      - ./:/workspace
      - agentainer-home:/home/dev
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp

volumes:
  agentainer-home:
COMPOSE

# ── .env.example ───────────────────────────────────────────────────
cat > .env.example <<'ENVFILE'
# Copy to .env and fill in (do not commit .env)

# Codex (optional)
OPENAI_API_KEY=""

# Tailscale (optional)
TS_AUTHKEY=""

# Office 365 / Himalaya
O365_EMAIL="you@yourdomain.com"
O365_PASSWORD="your_password_or_app_password"
HIMALAYA_SENDER_NAME="Tommy"
HIMALAYA_SIGNATURE="Sent from terminal"

# Alternative: use a command to retrieve the password (e.g., from pass or gpg).
# If set, this takes precedence over O365_PASSWORD.
# HIMALAYA_PASSWORD_CMD="pass show office365/app-password"

# iMessage bridge (optional) - macOS host reachable via Tailscale
# IMSG_HOST="mac-mini"
# IMSG_USER="tommy"
ENVFILE

# ── .gitignore ─────────────────────────────────────────────────────
cat > .gitignore <<'GITIGNORE'
# Secrets
.env
.env.local
.env.production
.secrets.baseline

# OS
.DS_Store

# Python
**/__pycache__/
**/.pytest_cache/
*.pyc

# Docker volumes
agentainer-home/

# Agentainer run artifacts (keep structure, ignore outputs)
.agentainer/runs/*/
.agentainer/downloads/*
.agentainer/screenshots/*
.agentainer/transcripts/*
!.agentainer/**/.gitkeep
GITIGNORE

# ── .gitkeep files for artifact dirs ──────────────────────────────
for dir in .agentainer .agentainer/runs .agentainer/downloads .agentainer/screenshots .agentainer/notes .agentainer/transcripts; do
  touch "$dir/.gitkeep"
done

# ── scripts/entrypoint.sh ─────────────────────────────────────────
cat > scripts/entrypoint.sh <<'ENTRYPOINT'
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
ENTRYPOINT

# ── scripts/himalaya-bootstrap.sh ─────────────────────────────────
cat > scripts/himalaya-bootstrap.sh <<'HIMALAYA'
#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.config/himalaya"

if [[ -z "${O365_EMAIL:-}" ]]; then
  echo "[himalaya] O365_EMAIL not set; skipping config generation."
  exit 0
fi

if [[ -n "${HIMALAYA_PASSWORD_CMD:-}" ]]; then
  PASSWORD_LINE="imap-passwd-cmd = \"${HIMALAYA_PASSWORD_CMD}\""
  SMTP_PASSWORD_LINE="smtp-passwd-cmd = \"${HIMALAYA_PASSWORD_CMD}\""
elif [[ -n "${O365_PASSWORD:-}" ]]; then
  PASSWORD_LINE="imap-passwd = \"${O365_PASSWORD}\""
  SMTP_PASSWORD_LINE="smtp-passwd = \"${O365_PASSWORD}\""
else
  echo "[himalaya] Neither O365_PASSWORD nor HIMALAYA_PASSWORD_CMD is set; skipping."
  exit 0
fi

SENDER_NAME="${HIMALAYA_SENDER_NAME:-}"
SIGNATURE="${HIMALAYA_SIGNATURE:-}"

cat > "$HOME/.config/himalaya/config.toml" <<EOF
# Generated automatically by himalaya-bootstrap.sh

default-account = "office365"

[accounts.office365]
email = "${O365_EMAIL}"
display-name = "${SENDER_NAME}"
signature = "${SIGNATURE}"

backend = "imap"
imap-host = "outlook.office365.com"
imap-port = 993
imap-encryption = "tls"
imap-login = "${O365_EMAIL}"
${PASSWORD_LINE}

smtp-host = "smtp.office365.com"
smtp-port = 587
smtp-encryption = "starttls"
smtp-login = "${O365_EMAIL}"
${SMTP_PASSWORD_LINE}
EOF

chmod 600 "$HOME/.config/himalaya/config.toml"
echo "[himalaya] wrote $HOME/.config/himalaya/config.toml"
HIMALAYA

# ── scripts/healthcheck.sh ────────────────────────────────────────
cat > scripts/healthcheck.sh <<'HEALTH'
#!/usr/bin/env bash
set -euo pipefail

command -v git    >/dev/null
command -v node   >/dev/null
command -v python3 >/dev/null
command -v whisper >/dev/null
command -v ddgr   >/dev/null
python3 -c "import playwright" >/dev/null

exit 0
HEALTH

# ── scripts/post-create.sh ────────────────────────────────────────
cat > scripts/post-create.sh <<'POSTCREATE'
#!/usr/bin/env bash
set -euo pipefail

echo "=== Agentainer post-create ==="

if ! python3 -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.chromium.executable_path; p.stop()" 2>/dev/null; then
  echo "[post-create] Installing Playwright Chromium..."
  python3 -m playwright install --with-deps chromium
else
  echo "[post-create] Playwright Chromium already installed."
fi

/opt/scripts/himalaya-bootstrap.sh || true

mkdir -p /workspace/.agentainer/{runs,downloads,screenshots,notes,transcripts}

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
POSTCREATE

# ── scripts/agentainer-run.sh ─────────────────────────────────────
cat > scripts/agentainer-run.sh <<'AGENTRUN'
#!/usr/bin/env bash
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

echo "[1/4] Web search..."
if command -v ddgr >/dev/null 2>&1; then
  ddgr --json -n 5 "$TASK" > "$RUN_DIR/search_results.json" 2>/dev/null || true
  echo "  -> $RUN_DIR/search_results.json"
else
  echo "  -> ddgr not found, skipping."
fi

echo "[2/4] Browser fetch..."
URL=$(echo "$TASK" | grep -oP 'https?://\S+' | head -1 || true)
if [[ -n "$URL" ]]; then
  python3 /opt/scripts/agentainer-fetch.py "$URL" --out "$RUN_DIR/fetched_page.md" || true
  echo "  -> $RUN_DIR/fetched_page.md"
else
  echo "  -> No URL detected in task, skipping."
fi

echo "[3/4] AI agent (optional)..."
if [[ -n "${OPENAI_API_KEY:-}" ]] && command -v codex >/dev/null 2>&1; then
  echo "  -> codex available. Run: codex \"$TASK\""
else
  echo "  -> codex not configured."
fi
if command -v claude >/dev/null 2>&1; then
  echo "  -> claude available. Run: claude \"$TASK\""
else
  echo "  -> claude not found."
fi

echo "[4/4] Saving metadata..."
cat > "$RUN_DIR/metadata.json" <<EOF
{
  "task": $(echo "$TASK" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'),
  "timestamp": "$TIMESTAMP",
  "run_dir": "$RUN_DIR",
  "url_detected": "${URL:-null}"
}
EOF
echo "  -> $RUN_DIR/metadata.json"
echo ""
echo "=== Run complete: $RUN_DIR/ ==="
AGENTRUN

# ── scripts/agentainer-fetch.py ───────────────────────────────────
cat > scripts/agentainer-fetch.py <<'FETCHPY'
#!/usr/bin/env python3
"""agentainer-fetch: Fetch a URL via headless Chromium and extract rendered text."""

import argparse
import sys
import textwrap
from pathlib import Path

from playwright.sync_api import sync_playwright


def fetch_page(url, out_path=None, screenshot_path=None, html_path=None, timeout_ms=30000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        title = page.title()
        text_content = page.inner_text("body")
        if screenshot_path:
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved: {screenshot_path}", file=sys.stderr)
        if html_path:
            Path(html_path).write_text(page.content(), encoding="utf-8")
            print(f"HTML saved: {html_path}", file=sys.stderr)
        browser.close()

    md = f"# {title}\n\nSource: {url}\n\n---\n\n{text_content}\n"
    if out_path:
        Path(out_path).write_text(md, encoding="utf-8")
        print(f"Rendered text saved: {out_path}", file=sys.stderr)
    else:
        print(md)
    return md


def main():
    parser = argparse.ArgumentParser(description="Fetch URL via headless Chromium.")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--out", "-o", help="Output markdown file")
    parser.add_argument("--screenshot", "-s", help="Save full-page screenshot")
    parser.add_argument("--html", help="Save raw HTML")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in ms")
    args = parser.parse_args()
    fetch_page(args.url, args.out, args.screenshot, args.html, args.timeout)


if __name__ == "__main__":
    main()
FETCHPY

# ── scripts/playwright_smoke.py ───────────────────────────────────
cat > scripts/playwright_smoke.py <<'PWSMOKE'
"""Playwright headless Chromium smoke test."""

from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com", wait_until="domcontentloaded")
        print("TITLE:", page.title())
        browser.close()


if __name__ == "__main__":
    main()
PWSMOKE

# ── scripts/pre-commit-secrets.sh ─────────────────────────────────
cat > scripts/pre-commit-secrets.sh <<'PRECOMMIT'
#!/usr/bin/env bash
set -euo pipefail

BLOCKED_FILES=(".env" ".env.local" ".env.production" "credentials.json" "service-account.json" "*.pem" "*.key" "id_rsa" "id_ed25519")
SECRET_PATTERNS=("OPENAI_API_KEY=['\"]?sk-" "TS_AUTHKEY=['\"]?tskey-" "O365_PASSWORD=['\"]?[^\"]{8,}" "AWS_SECRET_ACCESS_KEY" "PRIVATE.KEY" "BEGIN RSA PRIVATE KEY" "BEGIN OPENSSH PRIVATE KEY")

EXIT_CODE=0

for pattern in "${BLOCKED_FILES[@]}"; do
  matches=$(git diff --cached --name-only -- "$pattern" 2>/dev/null || true)
  if [[ -n "$matches" ]]; then
    echo "BLOCKED: Sensitive file staged: $matches"
    EXIT_CODE=1
  fi
done

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
for file in $STAGED_FILES; do
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if git diff --cached -- "$file" | grep -qEi "$pattern" 2>/dev/null; then
      echo "BLOCKED: Secret pattern in: $file"
      EXIT_CODE=1
    fi
  done
done

if [[ $EXIT_CODE -ne 0 ]]; then
  echo "Commit blocked. Remove sensitive data or use: git commit --no-verify"
fi
exit $EXIT_CODE
PRECOMMIT

# ── dotfiles/.zshrc ───────────────────────────────────────────────
cat > dotfiles/.zshrc <<'ZSHRC'
export EDITOR=vim
export PAGER=less

alias ll='ls -la'
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline --decorate -n 25'
alias py='python3'
alias pip='python3 -m pip'

# Web search
alias web='ddgr'

# Headless browser quick test
alias pw-chromium='python3 /opt/scripts/playwright_smoke.py'

# Whisper local STT
# Example: whisper audio.m4a --model small --language en --task transcribe
ZSHRC

# ── dotfiles/motd.txt ─────────────────────────────────────────────
cat > dotfiles/motd.txt <<'MOTD'

    _                    _        _
   / \   __ _  ___ _ __ | |_ __ _(_)_ __   ___ _ __
  / _ \ / _` |/ _ \ '_ \| __/ _` | | '_ \ / _ \ '__|
 / ___ \ (_| |  __/ | | | || (_| | | | | |  __/ |
/_/   \_\__, |\___|_| |_|\__\__,_|_|_| |_|\___|_|
        |___/

  * codex        (OpenAI Codex CLI)
  * claude       (Claude Code CLI)
  * playwright   (headless Chromium browser)
  * ddgr         (web search)
  * whisper      (local speech-to-text)
  * himalaya     (IMAP/SMTP email CLI)
  * tailscale    (optional VPN)
  * sshd         (optional SSH server)

MOTD

# ── Makefile ───────────────────────────────────────────────────────
cat > Makefile <<'MAKEFILE'
.PHONY: up down shell rebuild logs himalaya playwright whisper start-services \
       test run fetch dockerhost install-hooks

up:
	docker compose up -d --build

down:
	docker compose down

rebuild:
	docker compose build --no-cache

logs:
	docker compose logs -f

shell:
	docker exec -it agentainer zsh

dockerhost:
	docker compose --profile dockerhost up -d --build

start-services:
	docker exec -it agentainer bash -lc "/opt/scripts/entrypoint.sh zsh"

run:
	docker exec -it agentainer bash -lc "agentainer run '$(TASK)'"

fetch:
	docker exec -it agentainer bash -lc "agentainer-fetch '$(URL)'"

himalaya:
	docker exec -it agentainer bash -lc "/opt/scripts/himalaya-bootstrap.sh && himalaya accounts && echo 'OK: himalaya configured'"

playwright:
	docker exec -it agentainer bash -lc "python3 /opt/scripts/playwright_smoke.py"

whisper:
	@echo "Example: docker exec -it agentainer bash -lc \"whisper ./audio.m4a --model small --language en --task transcribe\""
	@true

test:
	docker exec -it agentainer bash -lc "cd /workspace && pytest tests/ -v --tb=short"

install-hooks:
	cp scripts/pre-commit-secrets.sh .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed."
MAKEFILE

# ── .devcontainer/devcontainer.json ───────────────────────────────
cat > .devcontainer/devcontainer.json <<'DEVCONTAINER'
{
  "name": "Agentainer",
  "build": {
    "context": "..",
    "dockerfile": "../Dockerfile"
  },
  "remoteUser": "dev",
  "workspaceFolder": "/workspace",
  "mounts": [
    "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached"
  ],
  "postCreateCommand": "bash -lc '/opt/scripts/post-create.sh'",
  "customizations": {
    "vscode": {
      "settings": {
        "terminal.integrated.defaultProfile.linux": "zsh"
      },
      "extensions": [
        "ms-azuretools.vscode-docker",
        "ms-python.python",
        "esbenp.prettier-vscode",
        "dbaeumer.vscode-eslint"
      ]
    }
  },
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  }
}
DEVCONTAINER

# ── .github/workflows/codespaces-image.yml ────────────────────────
cat > .github/workflows/codespaces-image.yml <<'GHCR_WORKFLOW'
name: Build Agentainer Codespaces Image

on:
  push:
    branches: ["main"]
  workflow_dispatch: {}

permissions:
  contents: read
  packages: write

concurrency:
  group: agentainer-image-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GHCR_PAT || github.token }}

      - name: Compute image name
        id: meta
        run: |
          set -euo pipefail
          OWNER="$(echo '${{ github.repository_owner }}' | tr '[:upper:]' '[:lower:]')"
          REPO="$(echo '${{ github.event.repository.name }}' | tr '[:upper:]' '[:lower:]')"
          echo "image=ghcr.io/${OWNER}/${REPO}/agentainer" >> "$GITHUB_OUTPUT"

      - name: Build and push (multi-arch)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: true
          platforms: linux/amd64,linux/arm64
          tags: |
            ${{ steps.meta.outputs.image }}:latest
            ${{ steps.meta.outputs.image }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
GHCR_WORKFLOW

# ── .github/workflows/test.yml ────────────────────────────────────
cat > .github/workflows/test.yml <<'TEST_WORKFLOW'
name: Agentainer Tests

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build image
        run: docker compose build

      - name: Run smoke tests
        run: |
          docker compose up -d
          docker exec agentainer bash -lc "cd /workspace && pytest tests/ -v --tb=short"

      - name: Run healthcheck
        run: docker exec agentainer bash -lc "/opt/scripts/healthcheck.sh"

      - name: Teardown
        if: always()
        run: docker compose down
TEST_WORKFLOW

# ── .pre-commit-config.yaml ───────────────────────────────────────
cat > .pre-commit-config.yaml <<'PRECOMMITCFG'
repos:
  - repo: local
    hooks:
      - id: block-secrets
        name: Block secrets and sensitive files
        entry: bash scripts/pre-commit-secrets.sh
        language: system
        always_run: true
        pass_filenames: false

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
        args: ["--maxkb=1024"]

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
PRECOMMITCFG

chmod +x scripts/*.sh

echo ""
echo "Created ${REPO_DIR}/"
echo "Next:"
echo "  cd ${REPO_DIR}"
echo "  cp .env.example .env && \$EDITOR .env"
echo "  make up"
echo "  make shell"
