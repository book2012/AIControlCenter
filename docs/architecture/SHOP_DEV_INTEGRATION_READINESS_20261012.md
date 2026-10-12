# SHOP_ORDER_001B DEV 통합 점검 — 2026-10-12

## 확인 범위

- DEV API release `024c123683c1c4de5c8ec0d661036eb53acbe88f`
- DEV 홈페이지 release `96ef201d6d2e0e44e5a1bf59e85e4e8e6c76d133`
- DEV 전용 Telegram consumer `papachichi` release `1eb15cf21861fc0bcfcc6f63cce47dd975b9f363`
- 원본 `/Users/kyouhan/AIControlCenter` dirty work는 별도 보존

## 결과

- Manual refund record와 주문조회 상태 표시의 focused regression: **71 passed**
- 실제 Chrome 기반 주문조회 refund 상태 smoke: **passed**
- DEV API launchd: **running**, immutable working directory가 `024c123...` release를 가리킴
- DEV `papachichi` consumer: **running**, 독립 cursor/data 경로 사용
- DEV 홈페이지: manifest가 `96ef201...`를 가리킴
- 외부 SMS, Telegram 송신, WooCommerce 쓰기, PROD mutation은 이 점검에서 실행하지 않음

## 운영 이관 전 남은 게이트

1. PROD에 manual refund record를 적용할 때는 PROD 전용 actor/권한/feature gate를 별도로 검토한다. DEV Qwen/operator private config를 PROD에 복사하지 않는다.
2. PROD 주문 데이터에서 고객 이름·전화번호·상품명·주문일자가 모두 존재하는지 read-only 표본을 확인한 뒤 운영 고객조회 UI를 승인한다.
3. 실제 Telegram 운영 명령 round-trip과 실제 고객 브라우저 주문은 운영 승인 후 별도 acceptance로 진행한다.
4. SOLAPI는 현재 자동 발송을 비활성화한다. 마지막 DEV 재시도는 provider status `3113`으로 실패했으며, 번호도용 차단 해제 후 새 발신번호/통신사 전파를 확인해야 한다.
5. 운영 반영 시에는 PROD business lineage와 DEV Qwen/papachichi lineage를 섞지 않고, 작은 변경 단위로 release manifest와 rollback pin을 함께 남긴다.

## 판정

DEV 통합 점검은 통과했다. PROD 이관은 위 운영 acceptance와 provider/SMS 게이트가 남아 있어 자동 진행하지 않는다.
