.PHONY: up down shell rebuild logs himalaya playwright whisper start-services \
       test run fetch dockerhost tailscale install-hooks \
       memory-up memory-down memory-logs memory-health memory-test

# Prefer `docker compose` (plugin) but fall back to standalone `docker-compose`.
DC := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

# ── Core lifecycle ─────────────────────────────────────────────────
up:
	$(DC) up -d --build

down:
	$(DC) down

rebuild:
	$(DC) build --no-cache

logs:
	$(DC) logs -f

shell:
	docker exec -it agentainer zsh

# ── Docker host access (opt-in profile) ────────────────────────────
dockerhost:
	$(DC) --profile dockerhost up -d --build

# ── Tailscale (opt-in profile) ─────────────────────────────────────
tailscale:
	$(DC) --profile tailscale up -d --build

# ── Services inside container ──────────────────────────────────────
start-services:
	docker exec -it agentainer bash -lc "/opt/scripts/entrypoint.sh zsh"

# ── Agent runner ───────────────────────────────────────────────────
# Usage: make run TASK="research playwright python examples"
run:
	docker exec -it agentainer bash -lc "agentainer run '$(TASK)'"

# ── Browser fetch ──────────────────────────────────────────────────
# Usage: make fetch URL="https://example.com"
fetch:
	docker exec -it agentainer bash -lc "agentainer-fetch '$(URL)'"

# ── Tool-specific targets ─────────────────────────────────────────
himalaya:
	docker exec -it agentainer bash -lc "/opt/scripts/himalaya-bootstrap.sh && himalaya accounts && echo 'OK: himalaya configured'"

playwright:
	docker exec -it agentainer bash -lc "python3 /opt/scripts/playwright_smoke.py"

whisper:
	@echo "Example: docker exec -it agentainer bash -lc \"whisper ./audio.m4a --model small --language en --task transcribe\""
	@true

# ── Testing ────────────────────────────────────────────────────────
test:
	docker exec agentainer bash -lc "cd /workspace && pytest tests/ -v --tb=short"

# ── MCP Memory Server (opt-in profile) ────────────────────────────
memory-up:
	$(DC) --profile memory up -d --build

memory-down:
	$(DC) --profile memory down

memory-logs:
	$(DC) --profile memory logs -f mcp-memory

memory-health:
	@curl -sf http://localhost:7411/health | python3 -m json.tool || echo "ERROR: mcp-memory not reachable"

memory-test:
	cd services/mcp-memory && $(DC) up -d postgres redis && \
	sleep 3 && \
	pip install -q -r requirements-test.txt && \
	pytest tests/ -v --tb=short

# ── Secrets hygiene ────────────────────────────────────────────────
install-hooks:
	cp scripts/pre-commit-secrets.sh .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed."
