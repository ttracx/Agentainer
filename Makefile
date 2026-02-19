.PHONY: up down shell rebuild logs himalaya playwright whisper start-services \
       test run fetch dockerhost install-hooks

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

# ── Secrets hygiene ────────────────────────────────────────────────
install-hooks:
	cp scripts/pre-commit-secrets.sh .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed."
