# DEV Qwen 모델 선택 정책

## 현재 적용

- primary: `qwen3:8b`
- fallback: `qwen3:4b`
- 적용 범위: DEV operator conversation 및 DEV 상품 문의 분류
- API release: `e6568763018f52a89c09b0b59c24772727645da9`

모델은 한국어 의도·슬롯을 추출하는 데만 사용한다. 주문 확정, 재고 차감, 입금·배송·환불 상태는 결정론적 handler와 WooCommerce/주문 ledger가 최종 권한을 가진다. 모델 응답은 JSON schema와 명시 슬롯 검증을 통과해야 하며, primary 호출 실패 시 fallback을 한 번 사용한다.

## 운영 규칙

- 모델 private config는 DEV에만 둔다.
- PROD bot과 PROD business lineage에는 이 설정을 복사하지 않는다.
- 4B는 fallback으로 유지해 8B 로드 실패가 주문 상태 변경으로 이어지지 않게 한다.
- 자연어 상태 변경은 기존 확인 단계와 actor binding을 거친다.
- 이미지 상품 태깅은 별도 Qwen3-VL worker로 검토하며, 주문 handler와 같은 모델 경로에 섞지 않는다.

## 검증

- Qwen3 8B 실제 호출에서 안전한 작업 목록 분류 확인
- primary 실패 후 4B fallback 호출 단위 테스트 통과
- DEV 주문·환불·브리지·고객조회 회귀 통과
- PROD mutation과 외부 SMS 송신 없음
