#!/usr/bin/env bash
# imsg-bridge.sh - macOS-side iMessage/SMS bridge.
# Install on macOS host: cp imsg-bridge.sh /usr/local/bin/imsg-bridge && chmod +x /usr/local/bin/imsg-bridge
#
# Commands:
#   imsg-bridge send <phone-or-email> <message>
#   imsg-bridge list [count]
#   imsg-bridge watch
set -euo pipefail

CMD="${1:-help}"
shift || true

case "$CMD" in
  send)
    RECIPIENT="${1:?Usage: imsg-bridge send <recipient> <message>}"
    shift
    MESSAGE="$*"
    osascript -e "
      tell application \"Messages\"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant \"$RECIPIENT\" of targetService
        send \"$MESSAGE\" to targetBuddy
      end tell
    "
    echo "Sent to $RECIPIENT"
    ;;

  list)
    COUNT="${1:-10}"
    # Query the Messages SQLite database for recent messages
    sqlite3 ~/Library/Messages/chat.db \
      "SELECT datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as date,
              h.id as contact,
              m.text
       FROM message m
       LEFT JOIN handle h ON m.handle_id = h.ROWID
       WHERE m.text IS NOT NULL
       ORDER BY m.date DESC
       LIMIT $COUNT;" \
      -header -column
    ;;

  watch)
    echo "Watching for new messages (Ctrl+C to stop)..."
    LAST_ROWID=$(sqlite3 ~/Library/Messages/chat.db "SELECT MAX(ROWID) FROM message;")
    while true; do
      sleep 2
      NEW=$(sqlite3 ~/Library/Messages/chat.db \
        "SELECT h.id, m.text
         FROM message m
         LEFT JOIN handle h ON m.handle_id = h.ROWID
         WHERE m.ROWID > $LAST_ROWID AND m.text IS NOT NULL
         ORDER BY m.date ASC;" 2>/dev/null || true)
      if [[ -n "$NEW" ]]; then
        echo "$NEW"
        LAST_ROWID=$(sqlite3 ~/Library/Messages/chat.db "SELECT MAX(ROWID) FROM message;")
      fi
    done
    ;;

  help|*)
    echo "Usage: imsg-bridge <command> [args]"
    echo ""
    echo "Commands:"
    echo "  send <recipient> <message>  Send an iMessage/SMS"
    echo "  list [count]                List recent messages (default: 10)"
    echo "  watch                       Watch for new messages (streaming)"
    ;;
esac
