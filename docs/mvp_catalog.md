# MVP Catalog

Priority formula:
`Priority = (Market Value × 0.4) + (Technical Feasibility × 0.3) + (Time-to-Market × 0.2) + (Strategic Importance × 0.1)`

Scoring scale: 1 (low) to 5 (high).

| MVP | Goal | AI Slice | Backend Slice | Frontend Slice | Dependencies | MV | TF | TTM | SI | Priority |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| Agent Runner | Standardize agent execution with artifacts | Codex/Claude CLI handoff | `agentainer run`, metadata, artifacts | CLI UX + docs | ddgr, Playwright, bash | 5 | 5 | 5 | 5 | 5.0 |
| Browser Fetch | Render and extract web content reliably | Optional AI summarization downstream | `agentainer-fetch.py` + Playwright | CLI flags and outputs | Playwright, Chromium | 4 | 5 | 4 | 4 | 4.3 |
| Codespaces/CI Image | Fast onboarding + reproducible tooling | N/A | Dockerfile + GH Actions | Devcontainer UX | GH Actions, GHCR | 4 | 4 | 4 | 4 | 4.0 |
| Email Integration | Send/receive email via CLI | Optional AI processing of inbox | Himalaya bootstrap + config | CLI workflows | Office 365, Himalaya | 3 | 4 | 3 | 3 | 3.3 |
| iMessage Bridge | SMS/iMessage bridge via macOS host | Optional AI reply routing | Tailscale SSH bridge | CLI wrapper | macOS host, Tailscale | 3 | 3 | 2 | 2 | 2.7 |

Status key:
- Planned: defined but not complete
- In Progress: actively being built
- Ready: functional and documented
