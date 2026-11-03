# Personal Assistant

AI 개인비서 서비스

This is a platform plugin boundary record, not a ChatGPT plugin ZIP or WordPress plugin.
The manifest is descriptive data, never executable configuration or authorization.

## Components

- OpenClaw 상태 계약 — `BINDING_REQUIRED`
- 대화·도구 실행 — `NOT_CONNECTED`
- 기억·일정 서비스 연결 — `NOT_CONNECTED`

## Source ownership

- `core/modules/service_adapters.py`
- `integrations/openclaw`
- `integrations/module_composition.py`

## Detach

AIControlCenter 비서 어댑터만 분리; 독립 실행 환경과 기존 데이터 유지

Domain code remains at the recorded paths; this folder does not claim independent installability or full source extraction. See docs/architecture/PLATFORM_PLUGINS.md.
