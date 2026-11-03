# Optional platform plugin distributions

Date: 2026-11-03 (Asia/Seoul)
Status: adapter source extraction, wheel builds and isolated installation verified.
No production entry point, shared Python environment, public service, database,
credential, WordPress install, Site or Ubuntu worker was modified.

## Package layout

| Plugin | Import package | Extracted runnable implementation |
| --- | --- | --- |
| Shopping | aicc_plugin_shopping | preview.py, bindings.py |
| Creative Notes | aicc_plugin_creative_notes | adapter.py |
| Personal Assistant | aicc_plugin_personal_assistant | adapter.py |

Each plugin owns its `plugins/<id>/src/<package>` source, descriptive manifest,
distribution metadata and README. The wheel version is 0.1.0, a development adapter
release. It is separate from Atelier theme 0.4.0 and the existing Creative Notes
Site/plugin versions. No marketplace package or public release was published.

## Host contract and compatibility
The common loader has an explicit reviewed package allowlist and imports only
selected packages inside their lifecycle factories. Manifests never supply executable
entry points. PLATFORM_PLUGIN_API must be the integer 1; missing, invalid or
incompatible packages become UNAVAILABLE for that plugin only. Other plugins and
core health continue to work. All-detached startup needs none of these packages.

core/modules/shopping.py and service_adapters.py are lazy compatibility facades.
core/modules/shopping_bindings.py re-exports the same binding class object, preserving
existing isinstance/type identity semantics. New composition calls plugin packages
through the optional loader rather than importing their implementation from core.
The old legacy application and governance/deployment entry points are unchanged.

These are host plugins, not standalone servers. Shopping still depends on the
existing core.shopping domain contracts/services and authenticated runtime bindings.
The assistant uses common capability-status contracts and an externally injected
provider. Notes packages its independent service reference, without private-account
API credentials. Full legacy-domain package extraction and real service connectivity
remain open; moving adapters does not imply those tasks are complete.

## Reproducible build and safe verification
Run from this worktree using its compatible host Python environment:

    python -m scripts.build_plugin_wheels

Output: dist/plugins/aicc_plugin_<name>-0.1.0-py3-none-any.whl.
The stdlib-only builder reads a reviewed allowlist of source files/metadata, executes
no plugin/build hooks, and downloads nothing. It emits deterministic ZIP metadata,
METADATA, WHEEL and SHA-256 RECORD rows according to the wheel specification:
https://packaging.python.org/en/latest/specifications/binary-distribution-format/
Only package Python sources and the plugin manifest enter wheels; no host core,
DBs, environment files, credentials, tests, customer records or media are bundled.
No third-party build tool or shared-environment installation was needed.

For isolated validation only (not the production interpreter), install into a new
empty target directory:

    python -m pip --isolated --disable-pip-version-check install --no-index --no-deps --target .plugin-packages dist/plugins/*.whl

The compatible host dependencies must already be present. --no-deps deliberately
prevents dependency changes. The .plugin-packages target and generated dist/plugins
files are ignored by Git. Existing launchd/production PYTHONPATH was not changed.
Run the plugin suites with the target explicitly on the test process path:

    PYTHONPATH="$PWD/.plugin-packages" python -m pytest -q tests/test_plugin_packages.py tests/test_plugin_catalog.py tests/test_module_attach_detach.py tests/test_module_lifecycle.py tests/test_module_shopping_bindings.py

For a fresh rebuild verification, use a new empty install target instead of layering
versions onto an existing one. Rebuilds must run relevant plugin tests before any
reviewed service-generation switch. Runtime detach preserves module data; removing
an installed wheel is a separate packaging operation and does not replace drain.

## Evidence
- 101 tests passed with all wheels installed in an isolated target; no skips.
- Each wheel was also pip-installed alone into its own temporary target, offline
  with no dependency installation. Only that plugin attached; the two missing
  packages reported UNAVAILABLE while core health returned 200.
- A fresh interpreter with no plugin packages verified all-detached startup and
  selected-but-missing plugin behavior. No domain runtime/DB/network access occurred.
- Package API-version rejection, compatibility class identity, deterministic wheel
  bytes, every RECORD hash/size, artifact file boundaries, authentication, drain,
  failure/recovery and reattach are covered.
- Without optional packages the core test run passed 85 tests and skipped 5
  optional dependency groups/cases. Installed-plugin coverage above is required
  for plugin release validation; optional skips are not release evidence.
- Python 3.14 host environment tested. Other Python versions/hosting environments
  were not validated. One existing TestClient deprecation warning remains.

See MODULE_ATTACH_DETACH_02.md for the real-connection and production migration gates.
