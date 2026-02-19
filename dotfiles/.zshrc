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

# Note: iMessage/SMS CLI (imsg) is macOS-only; run it on the mac host, not in this container.
