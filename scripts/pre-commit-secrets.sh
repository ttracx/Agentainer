#!/usr/bin/env bash
# Pre-commit hook: block commits containing secrets or sensitive files.
# Install: cp scripts/pre-commit-secrets.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
# Or use pre-commit framework with .pre-commit-config.yaml
set -euo pipefail

BLOCKED_FILES=(
  ".env"
  ".env.local"
  ".env.production"
  "credentials.json"
  "service-account.json"
  "*.pem"
  "*.key"
  "id_rsa"
  "id_ed25519"
)

SECRET_PATTERNS=(
  "OPENAI_API_KEY=['\"]?sk-"
  "TS_AUTHKEY=['\"]?tskey-"
  "O365_PASSWORD=['\"]?[^\"]{8,}"
  "AWS_SECRET_ACCESS_KEY"
  "PRIVATE.KEY"
  "BEGIN RSA PRIVATE KEY"
  "BEGIN OPENSSH PRIVATE KEY"
)

EXIT_CODE=0

# Check staged file names
for pattern in "${BLOCKED_FILES[@]}"; do
  matches=$(git diff --cached --name-only -- "$pattern" 2>/dev/null || true)
  if [[ -n "$matches" ]]; then
    echo "BLOCKED: Sensitive file staged for commit: $matches"
    EXIT_CODE=1
  fi
done

# Check staged file contents for secret patterns
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
for file in $STAGED_FILES; do
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if git diff --cached -- "$file" | grep -qEi "$pattern" 2>/dev/null; then
      echo "BLOCKED: Secret pattern '$pattern' found in staged changes to: $file"
      EXIT_CODE=1
    fi
  done
done

if [[ $EXIT_CODE -ne 0 ]]; then
  echo ""
  echo "Commit blocked. Remove sensitive data before committing."
  echo "If intentional, use: git commit --no-verify"
fi

exit $EXIT_CODE
