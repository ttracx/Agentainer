#!/usr/bin/env bash
set -euo pipefail

command -v git    >/dev/null
command -v node   >/dev/null
command -v python3 >/dev/null
command -v whisper >/dev/null
command -v ddgr   >/dev/null
python3 -c "import playwright" >/dev/null

exit 0
