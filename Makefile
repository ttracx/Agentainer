.PHONY: up down shell rebuild logs himalaya playwright whisper start-services \
       test run fetch dockerhost install-hooks \
       memory-up memory-down memory-logs memory-health memory-test

# ── Core lifecycle ─────────────────────────────────────────────────
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

# ── Docker host access (opt-in profile) ────────────────────────────
dockerhost:
	docker compose --profile dockerhost up -d --build

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
	docker exec -it agentainer bash -lc "cd /workspace && pytest tests/ -v --tb=short"

# ── MCP Memory Server (opt-in profile) ────────────────────────────
memory-up:
	docker compose --profile memory up -d --build

memory-down:
	docker compose --profile memory down

memory-logs:
	docker compose --profile memory logs -f mcp-memory

memory-health:
	@curl -sf http://localhost:7411/health | python3 -m json.tool || echo "ERROR: mcp-memory not reachable"

memory-test:
	cd services/mcp-memory && docker compose up -d postgres redis && \
	sleep 3 && \
	pip install -q -r requirements-test.txt && \
	pytest tests/ -v --tb=short

# ── Secrets hygiene ────────────────────────────────────────────────
install-hooks:
	cp scripts/pre-commit-secrets.sh .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed."
