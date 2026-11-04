# Companion product and Qwen3.5 profiles — 2026-11-04

## Decision and authority
The user explicitly requested companion-first behavior and a faster upgraded Mac Qwen. Keep AIControlCenter as the single Mac control plane. Shopping remains paused; no Ubuntu, Caddy, DNS, commerce, external-app permissions or credentials are changed.

## Product boundary
Personal: provider-independent identity, explicitly approved memories and optional Notes; planned original skins, outfits, environments and site customization. GPT/Gemini API adapters and provider-key ownership, quotas and spend caps remain unimplemented. Host AI apps use scoped MCP tools where supported; a common protocol does not establish universal consumer-app or OAuth compatibility.
Business: customer-specific Mac runtime and recurring operations/support. The current hosted Site queue and hosted memory store mean local inference, not a fully on-premises data path. A fully local tier needs a customer-local gateway, queue, identity, database, backups and capacity tests. Billing, customer provisioning and app-store submission are not activated.
Web: original 3D garden, autonomous preference/time-based activities, no care meters, penalties or background model calls. Native upgrade path: PWA and shared core, then desktop/mobile shell with device credential storage.

## Runtime candidate
Pinned fast model qwen3.5:4b-q4_K_M; explicit larger-model profile qwen3.5:9b-q4_K_M. No arbitrary model or provider selection. Both think=false, context 4096, keep_alive 60m. Fast output max 256 tokens; larger max 512. One shared admission lock across profiles. The system prompt preserves tentative facts and denies nonexistent app/tool activity. Runtime activation uses new immutable release directories and three LaunchAgent generation changes, preserving the original avatar artwork and old rollback releases.
Both outbound bridges identify their actual default model and completed-job model. The notebook worker carries only allowlisted fast/quality mode metadata. No Mac ingress or public Ollama endpoint is introduced.

## Measurements and validation
M4 / 24 GiB / Ollama 0.32.1, one synthetic local comparison: Qwen3 8B mean 19.60 tokens/s, Qwen3.5 4B 28.48, Qwen3.5 9B 16.89. Three warm Korean tasks; 192-token limit, seed 17, no thinking. This is a latency sample, not a broad accuracy claim. Initial prompts overconfirmed a tentative appointment; the revised companion prompt returned an unconfirmed-plan response for both models in a real source-port smoke test (5.927s fast / 10.241s larger). Host/browser queue overhead is additional. End-to-end response streaming remains next work.
Mac transport/local checks: 30 passed. Site companion boundary/behavior checks: 55 passed. Hardware WebGL, physical mobile keyboard and full external-host account linking remain unverified. The web companion keeps bounded, explicit account-scoped memories separate from Notes; no silent full-chat persistence.

## Activation record
Candidate source and tests are complete. Production activation and deployed release IDs are recorded by the task's runtime checkpoint and final delivery. Preserve prior generations for rollback; do not claim GPT/Gemini, subscription or native-app completion.

## Next milestones
1. Personal provider pilot: one adapter, credential ownership, streaming and spend controls, then two-account/host tests (about two focused sprints, account access dependent).
2. Indie-game art/animation/audio and Fold performance pass (one to two asset-dependent sprints).
3. Business fully local data path, recovery and measured capacity before paid pilot (two to three sprints).

References: https://docs.ollama.com/api/chat ; https://ollama.com/library/qwen3.5 ; https://developers.openai.com/plugins/build/app-quickstart ; https://geminicli.com/docs/tools/mcp-server/

## Verified activation — 2026-11-04
Code release d5bdc23b52fe5c4e9a88a89fa80eb435c1baa8c5 is active under the original loopback-only service and both existing outbound bridges. Both fast and larger live HTTP profiles returned nonempty replies with the pinned model and no tools. Existing avatar assets remain intact. An initial launchd bootstrap returned code 5 during immediate unload/reload; old settings were restored, the old service was explicitly verified/restarted, then a staged transition waiting for removal completed successfully. The private runtime deployment checkpoint retains the previous plists and immutable releases for rollback. The public companion Site version 17 contains profile/memory persistence, behavior preferences and fast/larger selection. Authenticated metadata reports connected=true and qwen3.5:4b-q4_K_M.
