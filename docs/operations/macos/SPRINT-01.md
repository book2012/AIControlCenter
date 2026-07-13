# Sprint 01 — Mac mini Production Control Plane Foundation

## Goal

Establish the Mac mini as the production-ready AIControlCenter
Control Plane.

## Architecture

- Mac mini owns the Control Plane.
- AIControlCenter owns orchestration and business logic.
- Ubuntu remains a stateless infrastructure worker.
- Infrastructure is consumed through JSON APIs.
- Secrets remain outside Git.
- Monitoring and validation precede write operations.

## Scope

- macOS security baseline
- Developer toolchain
- GitHub SSH authentication
- AIControlCenter repository clone
- JSON system inventory
- Python runtime assessment
- Secret directory foundation
- Health API planning
- launchd service planning

## Non-Goals

- No AI workload migration to Ubuntu
- No business logic deployment to Ubuntu
- No production secret migration before inventory validation
- No launchd write operations before health validation
- No Docker runtime decision before the Mac baseline is complete

## Production Gates

- macOS updated
- FileVault enabled
- Firewall enabled
- GitHub SSH authentication working
- AIControlCenter repository cloned
- RC tag visible
- JSON baseline generated
- Git working tree clean
- Documentation updated

## Next Milestone

AIControlCenter native runtime and launchd health-checked service.
