# DEV Qwen operator dialogue and Codex website drafts

2026-10-12. User prioritized commerce dialogue over the personal assistant. DEV pilot only; SMS remains held. Shared ingress routing remains on a separately pinned old-PROD-based relay.

## Execution boundary

One authorized Telegram consumer forwards DEV text and verified numeric actor/chat to the private HMAC socket. Qwen3:4b runs locally on Mac via loopback Ollama with an explicit no-thinking ChatML prefill, schema-constrained output, bounded context/output and no network proxy/redirect. Model output contains only allowlisted actions/fields. It never creates shell commands, SQL, credential requests, external recipients or production targets.

Typed validators resolve the current DEV order, phone ownership, exact product/color/size and numeric bounds. Explicit user order/tracking slots override omissions; anaphoric order references use only the authenticated actor's unexpired prior context. Missing/ambiguous slots cause a question. Reads execute immediately. Mutations require a new human confirmation and are revalidated before deterministic native Core/product handlers execute. Cancellation, payment, shipping and physical-return guards stay authoritative.

SQLite per-update claims precede any effect; actor/digest mismatches are denied. Duplicate/restarted completed turns replay one result. Interrupted or unknown claims never implicitly execute again. Provider PENDING/UNKNOWN receipts freeze dialogue execution for inspection. Canceling a pending conversation does not cancel an order or erase an unknown operation. Legacy inquiry/case and slash command protocols remain explicit deterministic paths.

## Conversation and notices

Shared environment memory is scoped by chat and user, lasts 30 minutes and supports explicit DEV/PROD overrides. Plain followups remain in the selected environment. Expired memory prompts for an environment and performs no mutation, avoiding accidental fallback to PROD.

Approval/additional-info reminders are due after 15 minutes and expire with the 30-minute proposal. Pending order review is reminded after 30 minutes, shipping registration after 1 hour and deposit followup after 24 hours from observation. One notice per pending state; completed/changed states suppress pending reminders. Ambiguous execution sends an inspection reminder after 5 minutes. Notices commit CLAIMED before sending and never automatically resend unknown outcomes. Notifications are the existing private DEV operator bot, not customer SMS.

'할일', '대기사항' and natural task-list requests show pending conversation, order followups and website requests. '개선목록' shows actual draft states. Conversation, journals, jobs and logs remain in private DEV storage; no public route, callback or customer account is added.

## Codex handoff

After the operator confirms a WEBSITE_TASK, one worker claims it and creates feature/bot-web-<8hex> in an isolated DEV worktree rooted at the deployed Git revision. The source worktree must be clean. Codex CLI is invoked by argument vector with request data on stdin, workspace-write sandbox, no approval escalation, ignored user runtime config and ephemeral session. No shell interpolation, privileged bypass, generic commerce tools, commit/push or deployment is requested.

Draft scope is core/homepage/, tests/, docs/ and required project documentation. Changed-file scope and whitespace are checked after execution. Success is REVIEW_REQUIRED, not deployment. Failures, interruption and scope errors require inspection and are never automatically requeued. Private logs are 0600. One background job at a time; result goes to the operator notice outbox. A Codex reviewer can then validate, commit/push and promote DEV; PROD publication remains separately controlled. Do not claim automatic production website updates.

## Activation / recovery

Private operator-conversation.private.json uses enabled=true, environment=DEV, model=qwen3:4b, codex_drafts_enabled=true. Receiver requires the existing external-consumer flag and private bridge key; no second Bot API poller. User authorized the necessary shared DEV routing continuation. API health advertises operator_conversation and codex_website_drafts. Existing API LaunchAgent and shared manifest/LaunchAgent are backed up before pin changes.

Do not unlink an unknown live socket. Stop prior DEV API and wait for clean socket closure before bootstrapping the new API. Preserve all conversation and router journals on rollback; do not rewind Telegram offsets. A crashed running Codex job is an inspection item, never an invitation to start another agent over the same worktree.

## Verification

212 targeted dialogue/bridge, native order/payment/stock/return, guest-runtime and isolation tests; 98 tests for the separately based shared relay. Actual local Qwen checks cover payment, anaphoric order, full carrier/tracking extraction, exact option sold-out, website request, task list and partial size reply. Actual Codex read-only response and workspace-write disposable-file probes passed; fixtures cleaned. No live customer order/stock/payment mutation or diagnostic Telegram sends in these probes. Existing original 26 dirty entries remain preserved.

## Activation checkpoint — 2026-10-12 07:29 KST

DEV API bb6f09fea12614758f769dcd5247fbc72efffda2 is active with operator_conversation=QWEN_DEV, operator_bridge=RUNNING, poller=EXTERNAL and codex_website_drafts=ENABLED. Shared relay e18d885770f7b97448bfb850ccda76d65ea577ab preserves PROD business base/frontend and enables actor-scoped environment memory. Live authenticated local Qwen order-list and unprefixed task-list roundtrips passed; neither bot cursor advanced and no diagnostic Telegram message was sent. Local model allocation ~3.86 GB at context 8192. Existing real order/payment/stock data was not changed.

Backups: DEV LaunchAgent com.aicontrolcenter.dev-order-api.plist.backup-20261012-072833; shared prod-commerce/backups/conversation-scope-20261012-072905. Human natural-dialogue/confirmation, timed live reminders and a real requested homepage draft remain acceptance checks. No actual customer order mutation is claimed from the local diagnostic.

## 2026-10-12 stage 1 live validation
Eight Qwen3:4b live intents classified correctly. Isolated dialogue executor verified confirmation-before-write, actor isolation, duplicate execution once and refusal cancellation. Found product slot omission on price request; explicit-slot resolver now recovers only a unique exact registered product name, with ambiguous/unregistered/unsupported-action regression coverage. No live orders or inventory changed.

Order identity presentation: customer_name projected from private shipping recipient; order timestamps rendered Asia/Seoul. Lists/details and dialogue choices/todos/reminders include phone, name, item options and date. Legacy missing names/dates remain explicitly unregistered/unknown. DEV-first, no PROD business changes.

Live DEV follow-up found Qwen carrying a pending deposit intent into explicit order-list text. Deterministic list/phone/detail read routing now precedes model inference, with regression coverage; no actual payment mutation occurred.

## 2026-10-12 Stage 2 DEV fulfillment verification
- New isolated journey test links OperatorConversation approval to GuestOperatorAdapter, durable aftersales state and authenticated customer lookup HTTP route.
- Shipping before payment is denied, every mutation requires confirmation, replay applies once, paid/shipped/delivered states match customer API, receipt survives restart, shipping outbox records one event.
- Live isolated DEV Woo stock probe passed: stock 1/two simultaneous orders produces one confirmation, replay does not reduce twice; cancellation and return restoration concurrency/reconciliation boundaries also passed. Synthetic Woo product/orders and probe journal cleaned.
- Related regression: 142 passed. No external Telegram/SMS messages, no real customer order edits, no PROD mutation. Runtime stays dfe5fd0 because this checkpoint changes tests/docs only.
- Remaining acceptance: human storefront/browser flow and new Telegram message roundtrip; real phone/SOLAPI delivery still blocked by 3113. No claim of complete live browser-to-carrier end-to-end validation.
- Next stage: detailed cancellation/return/refund-record workflow, without automatic money transfers.

## 2026-10-12 Stage 3 cancellation and return checkpoint
Isolated dialogue-to-aftersales journeys verify explicit actor-bound approval, one-time unpaid cancellation restoration, receipt-before-inspection, inspection-only return restoration, duplicate command suppression and customer notices without stale bank/deposit instructions. Return restocking preserves PAID and does not claim refund completion or execute payment transfers.
Regression exposed contradictory case decision replies: reversing an approved/rejected case kept its state but reported the requested opposite decision. The durable store now rejects CASE_DECISION_CONFLICT and operator replies state the conflict without claiming success.
146 related tests passed. No real customer orders, provider stock or PROD business data changed in this stage. DEV-only deployment; original dirty work preserved.
Remaining: explicit manual refund-completion record with amount/evidence and customer presentation is not yet implemented; partial refunds and exchange replacement-stock orchestration are also pending. Human browser acceptance and SOLAPI 3113 resolution remain separate.

2026-10-12: DEV manual refund-completion records implemented after verified return restocking; explicit case/full KRW amount/evidence and actor-bound confirmation required. No transfer APIs; customer projection omits proof/actor. Refund order-page UI and operator presentation updated. 160 regression tests + real isolated Chrome passed. SOLAPI retry final3113, auto SMS disabled; processing3000 classifier corrected. See SHOP_MANUAL_REFUND_RECORD_DEV.md.
