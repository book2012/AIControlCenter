# Assistant priority and on-demand Shopping — 2026-11-03

## Authorization and observed operations
The user explicitly requested pausing Shopping, keeping its functionality for
later plugin activation, and prioritizing the Mac for the personal assistant.
The user selected **Mac-local Qwen** and an independent web app. This is a narrow
authorization for the observed Shopping pause and loopback assistant service;
it grants no future commerce writes, unrelated production changes or public
Ollama exposure.

Shopping was actually paused: six launchd jobs disabled/booted out, six running
Shopping DEV/PROD/Atelier-QA containers stopped, and the dedicated
aicontrolcenter-commerce Colima VM stopped. The VM was configured with 4 CPUs
and 6 GiB. Existing container IDs and mount identities were preserved. Docker
mount ordering changed in one response; identity was verified by destination
rather than array order. No containers, volumes, images, release files or
customer records were removed. This is not a claim of exactly 6 GiB measured
physical-RAM savings or a new database backup/integrity assessment.

Caddy and its configuration, DNS, Ubuntu, the original main working tree,
existing launchd plist bytes and the common control plane were preserved.
Only the explicitly selected Shopping jobs were disabled; automatic boot-time
restart stays off until explicit activation.

## On-demand Shopping execution
The operator-local controller is ops/macos/modules/shopping_runtime.py.
Its inventory is private runtime state, not executable configuration:
AIControlCenterRuntime/modules/shopping/runtime.json under the trusted Mac home.
It validates known resource names, current container IDs/mount identities,
launchd plist hashes, user identity and the dedicated profile.

- status: observe saved state and current VM status.
- attach: print the bounded JSON execution plan; no mutation.
- attach --apply: start the existing VM, validate identities, start the existing
  production DB then WordPress, wait for container health, then load the two
  production services and check their loopback listeners.
- detach --apply: disable the known Shopping jobs, request graceful container
  stops and stop the VM only if no other workloads are running.

DEV and QA are not started by attach. No docker compose up/down, recreation,
migration, data deletion, generic remote shell or Ubuntu operation exists.
Interrupted transitions persist TRANSITION_INCOMPLETE and do not retry by
themselves. This does not implement transactional rollback.

integrations.module_composition.create_shopping_on_demand_instance provides
explicit async lifecycle hooks. It is not selected by default manifests or
the public loader. A trusted operator must opt into this controller and supply
the authenticated application. Managed leases drain before close; legacy
processes outside those leases use their existing OS/server shutdown behavior.
There is no claim that all legacy work has been enrolled in module leases.

The captured generation was paused live. Re-activation is plan/simulation tested
and deliberately **not performed live**, so Shopping remains off.

## Local assistant
Personal Assistant package 0.2.0 adds a pure bounded ConversationService.
The outer Ollama composition runs only at 127.0.0.1:58090 and talks only to
127.0.0.1:11434. Qwen3 8B was already installed; no model was downloaded.
Fixed policy: num_ctx=4096, num_predict=512, think=false, keep_alive=30m.
One model call per service instance runs at a time; concurrent calls fail busy.
Conversation history is bounded and kept only in browser memory. No tools,
filesystem execution, mail sending, calendar mutation or external app authority.

Requests require the fixed local Host and same-origin JSON POST. Input/output
sizes are bounded, transport proxies and redirects disabled, errors sanitized,
and Uvicorn access logging disabled. This is a local single-user service, not a
public or multi-tenant API. Existing Ollama/global control-plane config is unchanged.
A dedicated user launchd job is prepared for the immutable feature-commit release;
it must not replace the legacy production entry point.

Synthetic checks: Qwen loaded at about 5.92 GB reported model memory. Initial
short response took 6.89 s; a warm local HTTP conversation took 2.85 s. These are
two observations, not a general speed/quality benchmark. Foreign Origin was
denied, no-store headers verified, and tool usage remained empty.

## Web companion
Site: appgprj_6ae9581912908191a980fb514434c34e
URL: https://bok-personal-assistant.kyouhan.chatgpt.site
Source commit: 89048be942a12bdc79bdb64420eedadeadaf4f50
Published saved version: 2, owner-private access retained.

Following the user's final design request, the main screen contains only an
animated Mongle cloud character and one chat window. The previous dashboard is
retained at /workspace behind an explicit menu link. Blinking, breathing, waving
and success reactions are CSS/SVG; OS and per-device reduced-motion are supported.
Deliberate note/task commands and message-to-note actions use account-scoped D1
records. Task balloons appear as task items inside the chat, not extra permanent
panels. User content is rendered as text.

The Site is **not connected to the Mac model**. Free-form AI conversation is
visibly unavailable, and replies are not simulated. Gmail, Calendar and Creative
Notes private APIs remain unconnected. Connector eligibility discovery is not
available in this environment, so no connector IDs or grants were invented.
There is no billing, public customer release, voice recognition or app mutation.

Browser QA verified the new anonymous preview, Korean/English navigation and the
two-element interface. Hosted publication succeeded. The cloud browser reached
the expected sign-in gate; authenticated hosted CRUD/two-account checks are not
claimed. Both the Site workspace and Mac conversation remain distinct services.

## Validation and storage
- 2,435 related Python checks passed across seven isolated processes, zero failures
  or skips; 20 cover the assistant/resource controller. Existing deprecations remain.
- Current loopback UI/system-name follow-up: 20 focused checks passed.
- Web: 21 SQLite/policy/command checks, TypeScript and Worker build passed.
- All 26 original dirty files, original HEAD and index must match their baseline.
- Source and documentation live in the task feature branch. Runtime state/audits
  stay outside the repo; generated wheel installs use isolated targets.

## Next production milestone
Verify a private authenticated visitor-to-Mac gateway, then read-only per-account
app integrations and hosted end-to-end isolation. Only after those gates should
the assistant be offered as a paid multi-user service. Never expose raw Ollama
or use one owner's connected apps as customer-wide credentials.
