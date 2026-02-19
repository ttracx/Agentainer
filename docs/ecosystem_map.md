# Ecosystem Map

## Overview
Agentainer is a terminal-first, containerized development environment for running coding agents and automation workflows. The ecosystem centers on a Docker-based runtime with opt-in integrations (AI agents, email, Tailscale, iMessage) and standardized artifact outputs.

## Layers
### Infrastructure
- Docker image and compose service for local use
- Devcontainer for GitHub Codespaces
- Optional Render deployment via Dockerfile
- GH Actions workflows for CI and image builds

### Core Runtime
- `/opt/scripts/entrypoint.sh` for service bootstrapping
- Healthcheck to validate core tools
- Read-only root filesystem with writable mounts for workspace, home, and tmp

### Agent Workflow
- `agentainer run` orchestrates search, fetch, and agent invocation
- `agentainer-fetch` renders pages via Playwright and extracts text
- Standard artifact layout under `.agentainer/`

### Integrations
- AI: OpenAI Codex CLI, Claude Code CLI (best-effort)
- Email: Himalaya with Office 365 bootstrap
- Networking: Tailscale (opt-in profile)
- Messaging: iMessage bridge via Tailscale SSH to macOS host

### QA and Delivery
- Pytest smoke tests inside container
- CI workflows for tests and Codespaces image publishing

## Artifact Topology
- `.agentainer/runs/<timestamp>`: per-run outputs and metadata
- `.agentainer/downloads`: fetched files
- `.agentainer/screenshots`: browser captures
- `.agentainer/notes`: freeform notes
- `.agentainer/transcripts`: Whisper output

## External Dependencies
- Ubuntu base image
- Node.js, Python, Playwright Chromium
- Himalaya releases on GitHub
- Tailscale packages
- Docker runtime with optional `/dev/net/tun` access
