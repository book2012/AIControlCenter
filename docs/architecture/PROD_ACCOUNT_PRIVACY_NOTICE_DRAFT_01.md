# PROD customer signup privacy notice draft 01

Status: working product/privacy draft for review; not approved legal advice and not published. Prepared 2026-10-16 against Korean law and public examples. Production signup remains disabled.

## Draft signup screen

### Required terms

[필수] Agachichi 이용약관에 동의합니다. (이용약관 보기)

This is acceptance of the service contract and is separate from privacy consent.

### Required privacy processing consent

[필수] 회원가입을 위한 개인정보 수집·이용에 동의합니다. (내용 보기)

Show the items, purpose, retention period, right to refuse and effect of refusal
before the user accepts. The signup choice covers only the account fields listed
below; it does not cover marketing, third-party provision, or overseas transfer.
Marketing stays outside signup and unchecked. Keep this choice independent from
terms acceptance.

Requested UX behavior: do not start phone/email verification until the current
privacy-notice version has been shown and affirmatively accepted in the same
session. Record the notice-version digest and acceptance time; never store raw
contact details, OTP or password in the consent record. A refusal stops signup
without calling a verification provider.

This requested checkbox is not a conclusion that consent is the only available
legal basis. Before PROD, a Korean privacy reviewer must confirm the basis for
each field and whether a required consent choice is appropriate versus notice of
processing necessary to form/perform the account contract.

### Account information notice

회원가입과 계정 이용을 위해 아래 정보를 처리합니다.

| 구분 | 항목 | 목적 | 법적 근거(초안) | 보유·이용 기간 |
| --- | --- | --- | --- | --- |
| 필수 | 아이디, 이메일 주소, 휴대전화번호, 비밀번호 | 계정 생성·로그인·계정 보안 및 복구, 가입 시 이메일/휴대전화 확인, 계정 관련 안내 | 회원가입 및 이용계약의 체결 전 조치와 계약 이행에 필요한 범위: 개인정보 보호법 제15조 제1항 제4호. 실제로 필요한 항목에만 적용 | 회원 탈퇴 또는 처리 목적 달성 시 지체 없이 삭제. 다른 법령상 보존 대상 거래기록은 필요한 항목만 별도 분리 보관 |
| 필수 처리 기록 | 약관 버전 및 동의 시각, 고지 버전·표시 시각, 인증 결과/시각 및 만료 상태 | 계약 이력, 인증·보안 및 분쟁 대응 | 각 처리 목적별 적법 근거를 확정하고 최소한으로 처리 | 목적 달성 시 삭제. 법적 보존이 실제 적용되는 기록만 별도 분리 보관 |

비밀번호는 WooCommerce에 필요한 방식으로 안전하게 저장하며, 가입 API·로그·분석 도구에는 평문을 저장하거나 남기지 않습니다. AIControlCenter는 비밀번호를 영속 저장하지 않습니다.

회원가입 단계에서는 법적 이름, 생년월일, 주소, 배송지, 결제정보, 마케팅 프로필을 요구하지 않습니다. 배송 수령인 이름·연락처·주소는 주문 또는 배송지 등록 시점에 별도 목적과 고지로 수집합니다. 법적 이름이 계정 생성에 꼭 필요하다는 구체적 사유가 확인될 때만 최소수집 재검토를 합니다.

개인정보 처리방침은 처리를 설명하는 고지입니다. 제15조 제1항 제4호 등 동의 외의 근거로 처리하는 항목을 포괄적인 “개인정보 처리 동의” 체크박스에 묶지 않습니다. 제15조 제1항 제1호의 동의를 실제 근거로 쓰는 항목이 생기면 목적·항목·기간·거부권과 불이익을 알리고 해당 선택을 별도로 받습니다. 광고·마케팅 동의는 가입 필수 항목과 분리하고 기본값을 미동의로 둡니다.

휴대전화와 이메일의 OTP 인증은 Agachichi가 선택한 계정 보안 정책이며, 법이 일반적으로 SMS OTP 가입을 요구한다고 표시하지 않습니다. 두 연락처 모두를 필수로 둘 사업상 필요성과 대체수단은 최소수집 관점에서 출시 전에 확정해야 합니다.

## Provider and overseas processing notice

Twilio Verify와 SendGrid는 검토 중인 공급자 후보일 뿐, 설정·계약·발송이 완료된 사실이 아닙니다. 공급자 법인명, 연락처, 처리 국가, 재수탁자, 전송 시점·방식, 항목, 목적, 보유기간은 계약 및 실제 계정/서비스 리전을 확인한 뒤 채웁니다. 확인 전에는 아래 문구를 공개하거나 가입 화면에 표시하지 않습니다.

운영 시 개인정보처리방침의 국외 이전 항목에 서비스별로 다음을 공개할 초안입니다.

| 고지 필드 | 출시 전 확정할 내용 |
| --- | --- |
| 이전받는 자 | 계약 상대방의 정확한 법인명과 연락처 |
| 이전 국가 | 실제 데이터 처리·저장 국가 및 재이전 국가 |
| 시기·방법 | OTP 요청 때 TLS API 전송 등 실제 방식과 시점 |
| 이전 항목 | SMS: 휴대전화번호 및 필요한 인증 메타데이터 / 이메일: 이메일 주소 및 필요한 인증 메타데이터 |
| 목적 | 회원가입 연락처 확인 메시지 발송 및 인증 처리 |
| 보유·이용 기간 | 공급자 약관·계약과 실제 서비스 보존 설정에서 확인한 기간 |
| 이전 근거·고지 경로 | 개인정보 보호법 제28조의8 제1항 제3호 적용 가능성, 계약 필요성 확인, 제2항 각 호 정보를 처리방침에 공개하거나 법령상 허용된 방식으로 안내 |
| 거부 방법·효과 | 적용 근거와 제공 방식을 확정한 뒤 가입 전 안내. 거부 시 가입/연락처 인증이 제한되는지 정확히 설명 |

국외 이전 동의를 근거로 선택하는 경우에는 제28조의8 제1항 제1호 및 제2항에 따라 별도 동의를 받고, 이전 항목·국가·시기·방법·수령자·목적·보유기간·거부 방법과 효과를 미리 안내합니다. 계약 체결·이행에 필요한 위탁/보관 근거를 적용할 수 있는 경우에도 국외 이전 요건을 건너뛰지 않습니다. 해당 근거가 이 가입·공급자 구성에 실제 적용되는지와 제2항 정보의 공개 방식을 개인정보 담당자 또는 국내 법률전문가가 검토해야 합니다.

공급자가 개인정보 처리 수탁자인지, 별도 제3자인지, 수탁자의 재수탁자가 있는지는 각 계약관계로 판정합니다. 개인정보 보호법 제26조상 위탁 계약, 공개, 수탁자 감독 및 재위탁 통제도 확인하고 개인정보 처리방침에 역할과 업무를 정확히 반영합니다. 이를 단순히 “제3자 제공”으로 뭉뚱그리지 않습니다.

## Retention and withdrawal

- 가입 후보, OTP, 인증 티켓, 미완성 폼 값은 Core에 프로필로 보관하지 않습니다. OTP와 비밀번호는 로그·분석·영속 저장에서 제외합니다.
- 인증 challenge/ticket의 5분 유효기간과 rate-limit 데이터의 24시간 초기 제안은 기술 설계값이며 법정 보유기간이 아닙니다. 목적이 끝나면 만료·파기하며, 최소한의 보안 이벤트 보존 근거와 기간은 별도로 정합니다.
- 탈퇴 시 일반 계정 프로필은 지체 없이 파기하되, 법정 거래기록이 실제 발생한 경우 해당 거래기록과 필요한 식별정보만 다른 데이터와 분리해 법정 기간 보관합니다. 계정 전체 또는 비밀번호를 법정 보존이라는 이유로 유지하지 않습니다.
- 전자상거래법 시행령 제6조의 현재 기간은 표시·광고 6개월, 계약/청약철회 5년, 결제/공급 5년, 소비자 불만/분쟁처리 3년입니다. 각각의 적용 대상 기록에만 기간을 적용합니다. 단순 회원가입 정보가 자동으로 5년 보관되는 것은 아닙니다.
- 거래 전 회원 탈퇴/동의 철회 때 보존할 기록이 있다면 전자상거래법 제6조와 시행령 제6조에 따라 별도 분리 저장하고, 열람 방법과 처리 근거를 알립니다.
- 서비스 이용자는 법률상 권리 행사 및 탈퇴/정정/삭제 요청 창구를 처리방침에서 확인할 수 있어야 합니다. 책임자 이름·연락처·처리 부서는 실제 사업자 정보를 넣어야 합니다.

## Public site pattern used

Coupang public privacy policy is used only as a format example: it groups information by collection moment, purpose, item and retention period, separates required signup data, optional marketing, and service/order-specific later data. Its fields, retention decisions, and legal interpretation are not copied. Agachichi's required fields and periods must be justified independently.

## Implementation alignment and remaining mismatch

The side-effect-free candidate and unmounted synthetic DEV TestClient flow require separate terms and privacy-processing acceptance. The DEV flow serves a versioned signup notice, records a keyed digest and timestamp before either contact challenge, blocks challenge/confirmation without that same-session record, and rechecks it at final claim. The notice version is selected by the server. Only synthetic providers are composed; no real email/SMS is sent. The consent store contains no raw contact, password or OTP. This is a test-flow contract, not legal approval or evidence that phone/email are necessary in PROD.

Before adding a real API/runtime route:
1. decide whether both phone and email are necessary; record the necessity and available alternative;
2. derive the notice version on the server from the notice actually rendered, rather than trusting the browser's version string;
3. add a separate consent control only for processing whose legal basis actually is consent;
4. populate provider, processor, transfer, retention and business-identity facts from executed contracts and configured service regions;
5. review the final notice, terms, retention schedule and age policy with a qualified Korean privacy/legal reviewer.

This draft is not published or legally approved. No production route, provider, contract or PROD behavior was changed.

## Research basis

Reviewed 2026-10-16. The Privacy Act version used was the current text effective 2026-09-11 (Act No. 21445, promulgated 2026-03-10).

- [Personal Information Protection Act, consolidated text](https://www.law.go.kr/lsInfoP.do?efYd=20260911&lsiSeq=283839) — Articles 15, 16, 21, 22, 26, 28-8 and 30.
- [PIPC 2026 Privacy Policy Writing Guideline](https://www.privacy.go.kr/front/bbs/bbsView.do?bbsNo=BBSMSTR_000000000049&bbscttNo=20885) — current regulator guidance for the structure and disclosure of a privacy policy.
- [E-Commerce Consumer Protection Act, Article 6](https://www.law.go.kr/lsInfoP.do?ancYnChk=0&lsId=009318) and [Enforcement Decree, Article 6](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lspttninfSeq=63460) — transaction-record retention categories and periods.
- [Coupang Privacy Policy, public version 9.98](https://privacy.coupang.com/ko/center/coupang/coupang-v9-98/) — public disclosure layout reference only.

## Launch decisions still open

- Confirm the responsible legal entity, business/commerce disclosures, privacy officer/contact and user-rights channel.
- Confirm whether both phone and email are necessary for signup and whether phone OTP remains mandatory.
- Confirm service provider legal entities, processing/transfer locations, subprocessors, retention and contracts before publishing overseas-transfer/entrustment disclosures.
- Confirm applicable legal basis for every required field; separate transaction records from ordinary account data.
- Confirm age policy; if the service processes under-14 users' data on a consent basis, implement guardian consent and verification under Article 22-2.
- Review the final privacy policy, terms and signup screen text with a qualified Korean privacy/legal reviewer before PROD activation.
