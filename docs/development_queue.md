# Development Queue

Scoring uses the MVP formula from `mvp_catalog.md`.

## Now
1. Validate `docker compose up` on Docker Desktop without profiles (Priority 4.2)
2. Add a test for `metadata.json` type correctness (Priority 3.8)

## Next
1. Add a tailscale smoke test under the `tailscale` profile (Priority 3.6)
2. Add a lightweight status command for `agentainer` (Priority 3.4)

## Later
1. Add optional AI summarization in `agentainer-fetch` (Priority 3.1)
2. Add IMAP search examples for Himalaya in docs (Priority 2.8)

## Completed Recently
1. Added tmpfs mount for `/var/lib/tailscale`
2. Made Tailscale profile opt-in and removed `/dev/net/tun` from default
3. Fixed `agentainer run` metadata JSON generation
