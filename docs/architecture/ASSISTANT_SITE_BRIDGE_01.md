# Personal assistant Site bridge v1

- Web UI: https://bok-personal-assistant.kyouhan.chatgpt.site (owner-private).
- The Site authenticates visitors and stores short-lived, tenant-scoped conversation jobs in D1.
- A Mac-only outbound worker leases one job, calls the existing loopback conversation API on 127.0.0.1:58090, and returns the Qwen answer.
- Caddy, DNS, Ubuntu, Shopping services and the original main worktree are not changed. No incoming Mac port, tunnel or new public endpoint is opened.
- Two boundaries protect worker requests: Sites service access plus ASSISTANT_BRIDGE_KEY. Keys live in the Site secret store and a Mac-only 0600 JSON file under a 0700 runtime directory; never in Git or client code.
- Existing ConversationService remains responsible for message validation, serial local inference and no-tools policy. The bridge is a transport adapter, not another control plane.
- User queue reads require the authenticated owner ID; worker result writes require the exact one-time lease. There is no automatic inference replay after claim. Delivery-only retries are bounded.
- Per-owner pending cap 2, global cap 8, context at most 7 alternating messages / 12,000 characters. Job expiry 150 seconds. Input is erased after completion; expired jobs/results are purged after ten minutes by the connected worker, so cleanup pauses while Mac is offline.
- Operational diagnose creates only a fixed synthetic prompt under the reserved bridge-self-test owner, and cannot fetch another user's conversations.
- The main web view has a real articulated Three.js animal mesh with head/ear/paw/tail/blink motion, drag rotation and reduced motion. SVGRenderer is the software fallback when WebGL is unavailable; PNG is a last-resort fallback.
- Gmail, Calendar, Creative Notes, shell execution and infrastructure commands remain unavailable to the model.

## Operations

Service: com.aicontrolcenter.assistant-site-bridge.
Source: integrations/ollama/site_bridge.py.
Runtime config: /Users/kyouhan/AIControlCenterRuntime/personal-assistant/site-bridge/config.json.
Status: launchctl print gui/$(id -u)/com.aicontrolcenter.assistant-site-bridge.
Detach: launchctl bootout gui/$(id -u)/com.aicontrolcenter.assistant-site-bridge (keeps code/config).
Reattach: launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.aicontrolcenter.assistant-site-bridge.plist.
Bridge errors are logged only as sanitized state labels. Never print the config file.
If Sites service access is revoked or the Site audience changes, stop and re-establish an owner-authorized connection; do not weaken access.
The published UI must show a recent worker heartbeat to accept new AI jobs, and preserve input on failure.

## Validation

Transport tests cover config modes, destination allowlist, fixed local API, provider validation, one inference invocation, and delivery-only retries.
Existing local conversation tests cover validation, origin, size, timeout/error and concurrency boundaries.
Site SQLite tests cover tenant isolation, duplicate request IDs, owner/global caps, lease races, stale completion, expiry and purge.
Live deployment validation must record sanitized heartbeat and fixed synthetic request results; visitor-session authenticated conversation needs its own browser session verification.

## Live verification — 2026-11-03
Owner-private Site version 254ae392aace5272801b8cf234490748315c5fbd published successfully. The launchd worker was running, loopback health passed, and a fixed synthetic Site queue request completed with Qwen response “연결 성공.” through the deployed worker endpoint. Browser QA verified software 3D rotation; cloud GPU is disabled, so GPU rendering and signed-in visitor chat were not visually tested. Runtime evidence: site-bridge/verification.json.
