# Agentainer

Terminal-first, reusable coding agent development container. Deploy on **GitHub Codespaces**, **Render**, or **locally with Docker**.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ttracx/Agentainer?quickstart=1)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ttracx/Agentainer)

## What's inside

| Tool | Purpose |
|---|---|
| **Node 20** + pnpm/yarn | JavaScript/TypeScript runtime |
| **Python 3** + pip/venv | Python runtime + package management |
| **Git** + zsh + tmux | Version control + terminal environment |
| **Codex CLI** (`codex`) | OpenAI agent (requires `OPENAI_API_KEY`) |
| **Claude Code CLI** (`claude`) | Anthropic agent (best-effort install) |
| **Playwright + Chromium** | Headless browser automation |
| **ddgr** | Terminal web search (DuckDuckGo) |
| **Whisper** (`openai-whisper`) | Local speech-to-text (no API key needed) |
| **Himalaya** | IMAP/SMTP email CLI (Office 365 preconfigured) |
| **Tailscale** | Optional mesh VPN |
| **sshd** | Optional SSH server (port 2222) |

## Quick start

### Local (Docker)

```bash
cd Agentainer
cp .env.example .env
# edit .env with your keys
make up
make shell
```

### One-liner install

```bash
curl -fsSL https://raw.githubusercontent.com/ttracx/Agentainer/main/bootstrap.sh | bash
cd Agentainer && cp .env.example .env && make up && make shell
```

This downloads and runs the bootstrap script which creates the full Agentainer directory structure, writes all configuration files, and initializes a git repo. After that, just configure `.env` with your API keys and start the container.

### GitHub Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ttracx/Agentainer?quickstart=1)

The repo includes `.devcontainer/devcontainer.json` that builds from the local Dockerfile. Click the button above or open the repo in Codespaces and it works out of the box. The `postCreateCommand` runs diagnostics and configures tools automatically.

To use the prebuilt GHCR image instead, update `devcontainer.json`:
```json
{
  "image": "ghcr.io/ttracx/Agentainer/agentainer:latest"
}
```

### Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ttracx/Agentainer)

Click the button above to deploy directly to Render. The included `render.yaml` blueprint configures the Docker service automatically. Set your API keys and environment variables in the Render dashboard after deployment.

## Agent runner

Agentainer includes a standard agent runner interface:

```bash
# Inside the container
agentainer run "research playwright python examples"
agentainer run "fetch https://example.com and summarize"
```

The runner orchestrates:
1. **Web search** (ddgr) - saves results as JSON
2. **Browser fetch** (Playwright) - renders pages to markdown
3. **AI agent** (codex/claude) - prints instructions for manual invocation
4. **Artifacts** - all outputs saved under `/workspace/.agentainer/runs/<timestamp>/`

## Browser fetch utility

```bash
# Fetch rendered text from a URL
agentainer-fetch https://example.com
agentainer-fetch https://example.com --out ./page.md
agentainer-fetch https://example.com --screenshot ./shot.png --html ./raw.html

# Via make
make fetch URL="https://example.com"
```

## Artifact directories

All outputs follow a standard layout for reproducibility:

```
.agentainer/
├── runs/<timestamp>/     # Per-run artifacts (search results, fetched pages, metadata)
├── downloads/            # Downloaded files
├── screenshots/          # Browser screenshots
├── notes/                # Freeform notes
└── transcripts/          # Whisper transcription output
```

## Tool usage

### Web search

```bash
ddgr "playwright python examples"
# or
web "playwright python examples"    # alias
```

### Headless browser

```bash
python3 /opt/scripts/playwright_smoke.py
# or
make playwright
```

### Whisper (local speech-to-text)

```bash
whisper ./audio.m4a --model small --language en --task transcribe
```

### Himalaya (Office 365 email)

Fill `.env` with `O365_EMAIL` and `O365_PASSWORD` (or `HIMALAYA_PASSWORD_CMD` for secret managers):

```bash
make himalaya

himalaya list inbox
himalaya read inbox 1
himalaya search inbox "invoice"
himalaya write
himalaya reply inbox 1
himalaya forward inbox 1
```

**Password security**: Instead of storing passwords in `.env`, use `HIMALAYA_PASSWORD_CMD` to read from a secret manager:
```bash
HIMALAYA_PASSWORD_CMD="pass show office365/app-password"
```

### iMessage/SMS (macOS bridge)

iMessage is macOS-only. Agentainer provides a bridge pattern via Tailscale SSH:

```bash
# On macOS host: install imsg-bridge
cp tools/imsg-bridge/imsg-bridge.sh /usr/local/bin/imsg-bridge

# From Agentainer: use the remote wrapper
tools/imsg-bridge/imsg-remote.sh send "+15551234567" "Hello"
tools/imsg-bridge/imsg-remote.sh list 10
```

See `tools/imsg-bridge/README.md` for full setup.

## Security

### Container hardening

- **read_only** filesystem by default; only `/workspace`, `/home/dev`, `/tmp`, and `/run` are writable
- **no-new-privileges** security option
- **All capabilities dropped** except the minimum required (CHOWN, SETUID, SETGID, DAC_OVERRIDE, NET_ADMIN, NET_RAW)
- **Docker socket not mounted** by default. Use the `dockerhost` profile to opt in:
  ```bash
  make dockerhost
  # or
  docker compose --profile dockerhost up -d
  ```
- **tmpfs** mounts for `/tmp` and `/run` (not persisted)
- SSH: password authentication disabled, root login disabled

### Secrets hygiene

- `.env` is in `.gitignore` and will never be committed
- Pre-commit hook blocks commits containing secrets or sensitive files:
  ```bash
  make install-hooks
  # or with pre-commit framework:
  pre-commit install
  ```
- Supports `HIMALAYA_PASSWORD_CMD` for reading secrets from `pass`, `gpg`, or other managers

## Testing

```bash
# Run smoke tests inside the container
make test

# Tests verify:
#   - Core tools present (git, node, python3, whisper, ddgr, himalaya)
#   - Playwright can fetch example.com
#   - Codex/claude binaries (warnings only, not hard failures)
#   - Whisper can process audio (tiny model, silent sample)
```

Tests run automatically on PRs via `.github/workflows/test.yml`.

## Codespaces prebuilds

For faster Codespaces startup:
1. Go to repo Settings > Codespaces > Set up prebuild
2. The prebuild caches the Docker image build, Playwright browsers, and pip/npm installs
3. First open uses the cached image instead of building from scratch

## GitHub Actions

Two workflows included:

- **`codespaces-image.yml`**: Builds and pushes multi-arch image to GHCR on main push
- **`test.yml`**: Runs smoke tests on PRs and main push

### GHCR setup

1. Create a GitHub PAT named `GHCR_PAT` with `read:packages` + `write:packages` scopes
2. Add as repo secret: Settings > Secrets and variables > Actions > New repository secret
3. After the workflow runs, Codespaces can use the published image

## Make targets

| Target | Description |
|---|---|
| `make up` | Build and start container |
| `make down` | Stop container |
| `make shell` | Open zsh in container |
| `make rebuild` | Rebuild without cache |
| `make logs` | Follow container logs |
| `make dockerhost` | Start with Docker socket access |
| `make run TASK="..."` | Run agent task |
| `make fetch URL="..."` | Fetch URL via headless browser |
| `make test` | Run smoke tests |
| `make himalaya` | Configure and test Himalaya |
| `make playwright` | Run Playwright smoke test |
| `make install-hooks` | Install pre-commit secrets hook |
