# Platform plugin catalog

Date: 2026-11-03 (Asia/Seoul)
Status: three plugin boundary folders and read-only catalog implemented in the
separate modular preview/validation shell. No production activation.

AI Home Datacenter is the overall platform. AIControlCenter owns common policy,
authorization, approval, audit, deployment, secret injection, model routing,
scheduling and notification routing. These are shared platform services rather
than separately enabled business plugins. Ubuntu remains an infrastructure worker.

| Platform plugin | Source-controlled definition | Subcomponents |
| --- | --- | --- |
| Agachichi Commerce | plugins/shopping/manifest.json | Catalog, order read, customer sessions, notification readiness, separate Atelier theme, future transaction/SMS/Telegram integration |
| Creative Notes | plugins/creative-notes/manifest.json | External site reference, externally owned notes/images, future per-account API connection |
| Personal Assistant | plugins/personal-assistant/manifest.json | Provider status, future assistant execution, memory/scheduling bindings |

Each folder has README and manifest, describing purpose, source paths, component
readiness, data owner and detach effect. Existing domain code remains at the
recorded paths. This change creates management boundaries; it does not claim full
source/package extraction or independently installable plugin artifacts.

The word plugin here means an AIControlCenter platform capability. A WordPress
plugin, a WordPress theme and a ChatGPT marketplace/plugin package have distinct
formats and release lifecycles. In particular Atelier is a separate WordPress theme,
not the same artifact as the shopping platform plugin. No product was renamed or
republished as part of this change.

## Catalog contract
GET /platform/plugins is available in both the startup-only and managed validation
shells. It returns the three plugin definitions and current attachment state.
It reports operational_readiness=NOT_VERIFIED_BY_CATALOG separately. ATTACHED
means the adapter is mounted; it does not mean real API authentication, payment,
message delivery or assistant execution has been validated.

Only known plugin IDs are read. Manifests contain descriptive data, not executable
import paths. Unknown fields, duplicate JSON keys, mismatched identity, invalid
components or data-deletion-on-detach are rejected. Invalid/missing optional metadata
produces UNAVAILABLE without blocking the platform or changing runtime selection.
HTTP mutation of the catalog is not exposed. Metadata never authorizes activation.
No domain factory, network probe, private data lookup or resource allocation occurs
while loading the catalog. It reads only the three source-controlled manifest files.
Manifests are snapshotted at app construction; metadata edits require a new generation.

Existing module IDs match plugin IDs. Existing ModuleManager attachment/drain/
cleanup behavior remains authoritative; the catalog does not create a second
runtime registry. Components are descriptive groupings, not independently activated
child plugins. Detach preserves owned data and independently hosted services.

Validation: 88 tests passed across plugin catalog, startup selection, managed
lifecycle and explicit shopping bindings; one existing TestClient deprecation
warning. Tests cover manifest errors, no activation authority, missing metadata,
current lifecycle state, retained definitions after detach, disabled import
boundaries and existing drain/recovery/authentication tests. No production, Site,
WordPress, DNS, database or credential changes.

Remaining full service migration and real connection gates are documented in
MODULE_ATTACH_DETACH_02.md; catalog organization does not close those gates.
