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

# ── Core packages ───────────────────────────────────────────────────
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

# ── Node.js (NodeSource) ───────────────────────────────────────────
RUN set -eux; \
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/nodesource.gpg; \
  echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
    > /etc/apt/sources.list.d/nodesource.list; \
  apt-get update; \
  apt-get install -y --no-install-recommends nodejs; \
  npm i -g pnpm@latest yarn@latest; \
  rm -rf /var/lib/apt/lists/*

# ── Tailscale (official repo for Ubuntu noble) ─────────────────────
RUN set -eux; \
  install -m 0755 -d /usr/share/keyrings; \
  curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.noarmor.gpg \
    -o /usr/share/keyrings/tailscale-archive-keyring.gpg; \
  curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.tailscale-keyring.list \
    -o /etc/apt/sources.list.d/tailscale.list; \
  apt-get update; \
  apt-get install -y --no-install-recommends tailscale; \
  rm -rf /var/lib/apt/lists/*

# ── Web search CLI (DuckDuckGo) ────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends ddgr \
  && rm -rf /var/lib/apt/lists/*

# ── Convenience: fd is named fdfind on Ubuntu ──────────────────────
RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd

# ── Python tooling: whisper + playwright ───────────────────────────
RUN python3 -m pip install --break-system-packages --upgrade pip setuptools wheel \
 && python3 -m pip install --break-system-packages \
    black ruff mypy pytest pytest-cov \
    ipython rich httpx requests \
    pre-commit \
    openai-whisper \
    playwright \
 && rm -rf /root/.cache/pip

# ── Playwright Chromium (headless browser) ─────────────────────────
RUN python3 -m playwright install --with-deps chromium

# ── Codex CLI ──────────────────────────────────────────────────────
RUN npm i -g @openai/codex

# ── Claude Code CLI (best-effort; container remains usable if it fails)
RUN set -eux; \
  curl -fsSL https://claude.ai/install.sh | bash || true

# ── Himalaya CLI (download release tarball) ────────────────────────
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

# ── Non-root user + sshd basics ───────────────────────────────────
RUN set -eux; \
  groupadd --gid ${USER_GID} ${USERNAME}; \
  useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/zsh ${USERNAME}; \
  mkdir -p /workspace; chown -R ${USERNAME}:${USERNAME} /workspace; \
  mkdir -p /var/run/sshd; \
  sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config; \
  sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config; \
  echo "PrintMotd yes" >> /etc/ssh/sshd_config

# ── Passwordless sudo for specific daemons ─────────────────────────
RUN set -eux; \
  echo "${USERNAME} ALL=(root) NOPASSWD: /usr/sbin/sshd, /usr/bin/tailscaled, /usr/bin/tailscale, /usr/bin/service" \
    > /etc/sudoers.d/${USERNAME}; \
  chmod 0440 /etc/sudoers.d/${USERNAME}

# ── Copy project files ─────────────────────────────────────────────
COPY --chown=dev:dev scripts/ /opt/scripts/
COPY --chown=dev:dev dotfiles/.zshrc /home/dev/.zshrc
COPY --chown=dev:dev dotfiles/motd.txt /etc/motd

# ── Create agentainer CLI symlinks ─────────────────────────────────
RUN set -eux; \
  chmod +x /opt/scripts/*.sh /opt/scripts/*.py || true; \
  ln -sf /opt/scripts/agentainer-run.sh /usr/local/bin/agentainer; \
  ln -sf /opt/scripts/agentainer-fetch.py /usr/local/bin/agentainer-fetch

# ── Create standard artifact directories ───────────────────────────
RUN mkdir -p /workspace/.agentainer/{runs,downloads,screenshots,notes,transcripts} \
  && chown -R ${USERNAME}:${USERNAME} /workspace/.agentainer

USER ${USERNAME}
WORKDIR /workspace

ENTRYPOINT ["/opt/scripts/entrypoint.sh"]
CMD ["zsh"]
