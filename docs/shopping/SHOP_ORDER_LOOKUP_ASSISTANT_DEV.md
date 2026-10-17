# DEV 주문조회와 주문 도우미

## 참고 쇼핑몰에서 가져온 패턴
- Shopify 주문 상태 페이지는 한 화면에서 주문 진행과 배송 업데이트를 이어 보여주고, 배송 추적 정보를 주문 상태·이메일·앱 경로에서 접근할 수 있게 합니다.
- 패션플러스 비회원 주문조회는 주문 조회 진입을 별도로 두고 휴대폰 번호를 확인합니다.
- SSF SHOP은 마이페이지 주문 상세에서 배송 조회를 연결하고, 배송 지연 시 주문/교환/반품 내역을 다시 확인하도록 안내합니다.

이 패턴을 DEV agachichi에 적용해 상태 요약, 4단계 진행 표시, 배송 정보, 기존 환불·사이즈교환 동작을 주문조회 화면에 모았습니다.

## 주문 도우미 동작
- 첫 화면에는 주문번호와 휴대폰 번호 조회 폼을 보입니다. 미인증 사용자는 상세 주문조회 전에 휴대폰 인증을 진행합니다.
- 주문 결과가 성공적으로 표시된 뒤에만 주문 도우미를 엽니다. 조회가 새로 시작되면 이전 결과와 대화 내용을 바로 지웁니다.
- 현재 표시된 API 주문 응답에서만 배송, 운송장, 입금, 환불·교환 가능 여부를 설명합니다. 다른 주문 번호를 챗봇이 임의로 조회하지 않습니다.
- 답변은 상태 기반 규칙 안내이며 LLM 자유 생성이 아닙니다. 조회된 응답이 가진 범위만 설명하고, 그 외에는 고객 문의를 안내합니다.
- 출력은 textContent를 사용합니다. 새 API, SMS 발송, 주문 생성, PROD 변경은 포함하지 않습니다.
- 주문 페이지 응답은 no-store 및 noindex로 제공합니다.

## 인터페이스
모바일에서는 주문번호와 휴대폰 입력을 한 열로 쌓고, 주문 카드는 상태 배지·단계선·상품/배송·요청 버튼 순으로 읽힙니다. 상태 단계와 빠른 질문은 키보드·스크린리더 접근성을 위해 문서 구조와 aria 레이블로 표시합니다.

## 검증
- 기존 주문 조회·취소·반품·채팅/스토어프런트 테스트 83개 통과.
- 격리된 Chrome 브라우저에서 화면 내비게이션, 주문 조회, 결제/배송/주소 및 상품 정보, 상태 기반 챗봇 답변, 실패 후 상세 정보/대화 제거, 모바일 가로 넘침 여부를 확인했습니다.
- 테스트는 합성 주문과 가짜 API만 사용하며 외부 서비스 요청과 PROD 변경은 없습니다.

## 출시 상태
현재 DEV active commit `78ac5c570039a6e0cbb0c04a3a722fce2371ecdd`에서 분기한 별도 작업 브랜치의 후보입니다. 아직 DEV 런타임에 배포하지 않았습니다. 다음 단계는 후보를 깨끗한 immutable release로 만들고 현재 DEV에서 읽기 전용 smoke test를 수행하는 것입니다.

## 참고
- [Shopify 주문 상태 페이지](https://help.shopify.com/ko/manual/fulfillment/setup/order-status-page)
- [Shopify 주문 추적](https://help.shopify.com/ko/manual/fulfillment/setup/order-status-page/order-tracking)
- [패션플러스 비회원 주문조회](https://www.fashionplus.co.kr/auth/guest-login)
- [SSF SHOP 배송 조회 안내](https://www.ssfshop.com/public/helpdesk/faqList?searchAllCd=FAQ_DLV&searchCd=DLV_CNFIRM_INQ)
