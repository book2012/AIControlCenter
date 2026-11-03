# Creative Notes

창작노트와 개인 글쓰기 서비스

This is a platform plugin boundary record, not a ChatGPT plugin ZIP or WordPress plugin.
The manifest is descriptive data, never executable configuration or authorization.

## Components

- 독립 사이트 연결 정보 — `REFERENCE_ONLY`
- 글·사진·공개 범위 관리 — `EXTERNAL_SERVICE`
- 계정별 인증 API — `NOT_CONNECTED`

## Source ownership

- `core/modules/service_adapters.py`

## Detach

AIControlCenter 연결만 해제; 독립 사이트·글·사진·공개 범위 유지

The runnable adapter source now lives under `src/aicc_plugin_creative_notes`. Build its installable wheel with `python -m scripts.build_plugin_wheels`. It requires the compatible AIControlCenter host; it is not a standalone application or a complete legacy-domain extraction. See docs/architecture/PLATFORM_PLUGIN_PACKAGES.md.
