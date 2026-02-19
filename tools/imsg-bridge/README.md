# iMessage/SMS Bridge

iMessage and SMS CLIs are macOS-only and cannot run inside this Linux container.
This directory provides a bridge pattern for calling iMessage from Agentainer
over Tailscale SSH to a macOS host.

## Architecture

```
Agentainer (Linux)  --[Tailscale SSH]-->  Mac mini / MacBook
                                           └── imsg-bridge.sh
                                                ├── send <number> <message>
                                                ├── list [count]
                                                └── watch
```

## Setup

### On the macOS host

1. Install the `imsg-bridge.sh` script:
   ```bash
   cp imsg-bridge.sh /usr/local/bin/imsg-bridge
   chmod +x /usr/local/bin/imsg-bridge
   ```

2. Ensure Tailscale is running and SSH is enabled:
   ```bash
   tailscale up --ssh
   ```

3. Grant Terminal/iTerm2 automation access for Messages.app in
   System Preferences > Privacy & Security > Automation.

### From Agentainer

Once Tailscale connects both machines:

```bash
# Send a message
ssh mac-mini "imsg-bridge send '+15551234567' 'Hello from Agentainer'"

# List recent messages
ssh mac-mini "imsg-bridge list 10"

# Watch for new messages (streaming)
ssh mac-mini "imsg-bridge watch"
```

## Wrapper (optional)

Use `imsg-remote.sh` as a convenience wrapper inside Agentainer:

```bash
imsg-remote send "+15551234567" "Hello"
```
