#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.config/himalaya"

if [[ -z "${O365_EMAIL:-}" ]]; then
  echo "[himalaya] O365_EMAIL not set; skipping config generation."
  exit 0
fi

# Support HIMALAYA_PASSWORD_CMD: read password from a command (e.g. pass, gpg)
# instead of storing it in an environment variable.
if [[ -n "${HIMALAYA_PASSWORD_CMD:-}" ]]; then
  PASSWORD_LINE="imap-passwd-cmd = \"${HIMALAYA_PASSWORD_CMD}\""
  SMTP_PASSWORD_LINE="smtp-passwd-cmd = \"${HIMALAYA_PASSWORD_CMD}\""
elif [[ -n "${O365_PASSWORD:-}" ]]; then
  PASSWORD_LINE="imap-passwd = \"${O365_PASSWORD}\""
  SMTP_PASSWORD_LINE="smtp-passwd = \"${O365_PASSWORD}\""
else
  echo "[himalaya] Neither O365_PASSWORD nor HIMALAYA_PASSWORD_CMD is set; skipping."
  exit 0
fi

SENDER_NAME="${HIMALAYA_SENDER_NAME:-}"
SIGNATURE="${HIMALAYA_SIGNATURE:-}"

cat > "$HOME/.config/himalaya/config.toml" <<EOF
# Generated automatically by himalaya-bootstrap.sh

default-account = "office365"

[accounts.office365]
email = "${O365_EMAIL}"
display-name = "${SENDER_NAME}"
signature = "${SIGNATURE}"

backend = "imap"
imap-host = "outlook.office365.com"
imap-port = 993
imap-encryption = "tls"
imap-login = "${O365_EMAIL}"
${PASSWORD_LINE}

smtp-host = "smtp.office365.com"
smtp-port = 587
smtp-encryption = "starttls"
smtp-login = "${O365_EMAIL}"
${SMTP_PASSWORD_LINE}
EOF

chmod 600 "$HOME/.config/himalaya/config.toml"
echo "[himalaya] wrote $HOME/.config/himalaya/config.toml"
