# AI Home Datacenter 상태 점검 — 2026-10-27

## 결론

운영 쇼핑 서비스는 가동 중이다. DEV 주문 API는 프로세스가 살아 있어도 요청을 받지 못하는 장애가 있었고, 같은 릴리스의 DEV API만 재시작하여 HTTP 200으로 복구했다. 파일 핸들 누적 방지 수정은 현재 실행 버전 `76dd8d4`에서 분리했다. SENS 후보 커밋 `6475e2e`와 그 외 최신 기능은 이 수정의 배포에 포함하지 않는다.

## 관찰한 실행 버전

| 서비스 | 점검 당시 버전 | 근거 |
|---|---|---|
| DEV API | `76dd8d4` | launchd + 프로세스 cwd + current.json |
| DEV 홈페이지 | `fc0817b` | 프로세스 cwd + current.json |
| DEV Papachichi | `9f8403d` | launchd 설정, 프로세스 실행 확인 |
| PROD API | `3bf63c0` | launchd + 프로세스 cwd |
| PROD 홈페이지 | `78ac5c5` | launchd + 프로세스 cwd |
| PROD WordPress 플러그인 | `7dda8c9` | Docker 읽기 전용 bind mount |

기본 저장소 HEAD는 `29a40dc`, dirty 항목은 26개다. 이후 작업은 별도 작업 트리에 존재하므로 기본 저장소만으로 최신 개발 상태를 판단하면 안 된다. PROD current.json의 `78ac5c5`를 모든 서비스의 공통 실행 버전으로 해석해서도 안 된다. 서비스별 다른 버전 자체는 장애가 아니며, 계약 호환성과 실행 근거를 별도로 관리해야 한다.

## DEV 장애와 수정

- DEV API `/dev-order/health` 연결이 reset되었고 로그에 `OSError: [Errno 24]`가 반복되었다.
- PID 4400에서 파일 항목 311개, `guest-checkout.sqlite3` 핸들 242개를 관찰했다.
- 주문 생성 12개와 운영자 브리지 119개는 모두 COMPLETED였고 outbox 23개는 SENT였다. 운영자 검토 대기는 진행 중 생성 작업으로 취급하지 않는다.
- 현재 버전 그대로 DEV API만 재시작한 뒤 HTTP 200, poller EXTERNAL, operator bridge RUNNING, product management RUNNING, SMS IDLE을 확인했다.
- SQLite의 connection context manager는 트랜잭션을 종료하지만 연결을 닫지 않는다. Checkout 저장소 7곳과 운영자 폴링 조회 1곳에 `contextlib.closing`을 적용하고 기존 commit/rollback 의미를 유지한다.
- 연결 참조를 유지하여 GC가 누수를 숨기지 못하게 하는 회귀 5개는 수정 전 모두 실패했다. 정상·반복 조회, 읽기 오류, 쓰기 rollback과 close를 검증한다.
- 이전 주문목록 테스트는 공개 주문번호와 5건 페이지 방식으로 보완했다. 27개 전체 주문과 26개 고객 주문을 6페이지 끝까지 확인하여 누락·중복과 고객 혼입을 검증한다.
- 현재 실행 버전 기반 최종 집중 회귀: **92 passed**, 기존 Starlette 경고 1개. 전체 테스트는 실행하지 않았다.

## 백업과 복원

- 과거 백업 중 0바이트 `20261010-112204/database.sql`은 INVALID_EMPTY로 기록했다. 삭제하지 않았다.
- 과거 SQL 백업 2개는 네트워크·포트·운영 볼륨 연결이 없는 임시 MariaDB에서 각각 복원했다. 각각 50개 테이블과 mariadb-check 통과, 임시 컨테이너 제거 완료.
- 과거 SQLite 백업 14개 integrity_check 통과. 과거 미디어 아카이브 8,319개 항목을 읽었고 위험한 member path는 없었다.
- 최신 보관 위치: `/Users/kyouhan/AIControlCenterAudit/20261027/backups`.
- 최신 PROD SQL 1,237,770바이트, wp-content 112,043,845바이트를 생성하고 SHA-256을 기록했다.
- PROD/DEV SQLite 32개를 SQLite backup API로 복제하고 복제본 integrity_check를 통과했다. 이 중 일부는 보조 하위 디렉터리 파일이다.
- 최신 SQL도 격리 MariaDB에서 50개 테이블 복원·검사에 통과했다. 최신 미디어 8,396개 항목을 임시 디렉터리에 복원하고 일반 파일 7,193개를 확인한 뒤 검증용 복사본을 제거했다.
- DB·SQLite·미디어는 서비스를 중지하지 않고 차례로 복사했다. 서로 동일한 시점의 전체 애플리케이션 스냅샷이라는 보장은 없다. 비밀 설정과 키를 포함한 전체 서비스 기동 복구, 외부 보관, 자동 정기 백업은 별도 과제다.
- 원시 DB·미디어·인증 설정은 Git에 포함하지 않는다. 이 문서와 JSON에는 상태·크기·해시만 기록한다.

## 도메인과 문자

- `bokstory.duckdns.org`: HTTP 200, TLS 검증 통과.
- DEV 외부 비인증 요청: HTTP 401. 로그인 후 전체 사용자 흐름 검증은 미실행.
- `agachichi.com`: 로컬 및 공용 DNS에서 NXDOMAIN. 구매 여부를 단정할 수 없다. 등록 계정의 소유권·만료·네임서버 위임 확인이 먼저 필요하다.
- DEV 인증은 Twilio Verify, 주문 안내는 DEV_PREVIEW. 두 설정 파일 권한 0600. SENS 설정 파일은 없다.
- 실제 OTP/SMS, Telegram 메시지, 주문·재고·환불 변경은 이번 작업에서 실행하지 않는다.

## 우선순위 및 남은 일

1. DEV 핸들 수정 릴리스를 적용하고 일정 간격의 health와 핸들 수를 관찰한다. 단기 관찰 성공을 장기 무누수 증명으로 표현하지 않는다.
2. 공식 도메인의 등록·네임서버 권한을 확인하고 DNS/HTTPS 전환 후보를 준비한다. PROD 적용은 별도 승인 대상이다.
3. 인증 제공자와 승인된 발신번호를 확정한다. 현재 런타임에 없는 SENS/MCP 설정을 완료로 표시하지 않는다.
4. 서비스별 버전 기록을 실제 실행 상태와 맞춘다. 기존 runtime/version-matrix.json은 이번에는 수정하지 않는다.
5. 주문·환불·교환의 DEV 실사용 검증과 PROD 반영 후보를 준비한다.
6. 최신 백업의 별도 장치 보관·정기화와 전체 복구 훈련을 진행한다.
7. Ubuntu/스토리지/Immich/Nextcloud/Plex/WOL과 shadow API exit 78은 별도 진단이 필요하다.

운영 변경은 수행하지 않으며, DEV lifecycle 복구와 격리 검증만 수행한다. DEV 수정의 실제 적용 결과는 후속 실행 기록에 남긴다.
