# AI Home Datacenter platform plugins

AIControlCenter owns the common control plane. Business-facing capabilities are
catalogued as three platform plugins, each with its own manifest and component
readiness. The platform plugin identity matches the existing module lifecycle ID.

| Plugin | Folder | Responsibility |
| --- | --- | --- |
| Agachichi Commerce | shopping | Shopping adapters and links to the separate Atelier theme |
| Creative Notes | creative-notes | Independent notes service reference and future authenticated adapter |
| Personal Assistant | personal-assistant | Replaceable assistant provider/status interface |

These manifests are source-controlled descriptive records, not ChatGPT marketplace
plugin packages, WordPress plugins, automatic installation requests or grants of
production authority. They never supply import paths to execute. Metadata changes
neither attach a module nor authorize it. Existing configuration and lifecycle gates
remain authoritative. API overview: GET /platform/plugins in the separate modular
preview/validation shell. The current production app is unchanged.

## Runnable adapter packages

Each plugin now owns `src/aicc_plugin_*` and `distribution.json`. Build with `python -m scripts.build_plugin_wheels`. See [installation, compatibility and validation](../docs/architecture/PLATFORM_PLUGIN_PACKAGES.md). These installable host adapters are not full standalone services; existing domain/API/authentication dependencies remain explicit.
