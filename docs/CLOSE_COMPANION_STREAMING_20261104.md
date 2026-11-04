# Close companion and response streaming — 2026-11-04

AIControlCenter remains the Mac control plane. Shopping stays paused; Ubuntu and public ingress are unchanged.

## Runtime contract

The existing loopback chat API remains compatible. New POST /api/chat/stream emits bounded NDJSON content deltas followed by a pinned model/provider terminal event. It shares the same origin/host/history/profile validation and generation admission lock. Thinking output is never relayed; truncated streams and provider failures never become successful replies. Disconnect closes the iterator and releases its lock.

The notebook bridge alone uses streaming and publishes cumulative provisional content (maximum 12 offered updates, 8000 characters; a single background sender coalesces to the latest pending snapshot so network RTT never blocks generation). A worker lease, job expiry and monotonic sequence bound progress writes. The final response clears provisional content. Failures delivering progress do not replay the model. Final delivery retry remains bounded and does not rerun generation. Private legacy site keeps its non-streaming path. Notebook idle polling: 1 second; other bridge: 3 seconds. No logs contain prompts, secrets or replies.

Fast: Qwen3.5 4B Q4_K_M, think=false, ctx4096, output256. Quality: 9B Q4_K_M output512. Residency 60m. Streaming improves first-visible text, not guaranteed model throughput. Same synthetic diagnostic question must be measured before/after activation; warm/cold/model and completed latency must be distinguished.

## Product boundary

Site foreground replaces play activities and broad landscape with close lateral pacing and camera approach on input. Explicit memories remain separate from selected source documents. Full document ingestion/RAG, external provider keys, billing/entitlements and customer-local queue/DB are future work. Current inference is local but hosted queue and hosted profiles/memories remain; do not advertise fully on-premises data.

Next knowledge pilot: explicitly selected sources, hash/version/owner metadata, Mac FTS5 retrieval, source citations, ACL checks before search and prompt assembly, deletion of chunks/index/cache. Evaluate 50 representative questions and tenant isolation before commercial claims. Commercial readiness also requires asset licensing, export/delete, billing/cancellation/refund, backup restoration, audit/support and capacity measurements. Site docs/COMPANION_KNOWLEDGE_BUSINESS_02.md contains the Korean plan.

## Validation and deployment

Focused runtime/bridge suite: 35 passed. Site: 57 tests and TypeScript. Activate as immutable releases with exact plist backups, launchd unload settling, health and streaming/non-streaming smoke checks, and rollback on failure. Record source commit and controlled latency measurements under runtime deployment records. No credentials or private user records are test inputs.
