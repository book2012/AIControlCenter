# 상품 등록 빠른 시작

상태: 상품 접수 기준과 범용 단일 상품 DEV 등록기가 준비됐습니다. 신규 상품의 화면 노출은 별도 DEV 릴리스 단계입니다.

## 다음 등록부터 보내는 내용

상품 사진을 함께 올리고 아래 블록을 채워 주세요. 모르는 항목은 비워두거나 `확인 필요`라고 적으면 됩니다. 사진은 여러 장을 한 번에 첨부하고 같은 상품 사진은 한 상품으로 묶습니다.

```text
상품명/브랜드: (모르면 사진으로 확인)
판매가: (원화 금액 또는 조사 요청)
색상:
사이즈:
옵션별 실제 재고: (색상·사이즈별 수량, 모르면 확인 필요)
상품 상태: (새상품/중고 및 사용감)
포함 구성품:
상품 설명에서 강조할 점:
이미지 요청: (누끼 / 정면 참고 / 디테일 / 착용 참고, 기본은 상품 특징 보존)
기타:
```

최소 접수 조건은 상품 사진과 판매가입니다. 옵션·재고를 모르면 0개 및 판매 대기로 둡니다. 가격이나 재고를 이미지·검색으로 추정하지 않습니다. 조사 가격은 사용자가 확정하기 전까지 제안값입니다.

## 표준 처리 순서

1. **접수 묶기** — 첨부 사진을 상품별로 모으고 중복·다른 상품이 섞였는지 확인합니다.
2. **정보 보완** — 요청이 있으면 공식 브랜드/판매처 자료를 우선 확인합니다. 검색 사실과 사진에서 관찰한 특징을 나눠 씁니다. 품번, 소재 혼용률, 치수, 정품 여부는 근거가 없으면 확인 필요로 둡니다.
3. **이미지 준비** — 원본은 보존합니다. 상품 색상·실루엣·디테일은 임의로 바꾸지 않습니다. 정면/착용 참고 이미지는 AI 생성 이미지로 표시합니다. DEV 페이지 구성에 필요한 원본, 정면 참고, 누끼, 추가 착용 이미지를 준비하고 SHA-256 manifest를 검증합니다.
4. **한 번에 검토** — 상품명·분류, 판매가, 색상/사이즈별 수량, 확인된 사실/확인 필요 항목, 이미지 목록과 AI 표시를 한 번에 제시합니다. 수정할 항목만 되돌려 받아 등록 자료에 반영합니다.
5. **기본 검증(읽기 전용)** — catalog ID, 가격 승인 표시, 옵션별 재고, 대표/갤러리 이미지 해시, SKU 중복, DEV 격리를 확인합니다.
6. **명시적 DEV 등록** — 등록 요청이 확인된 뒤에만 `--apply-dev`를 실행합니다. WooCommerce 상품/변형/이미지를 만들고 읽어서 재검증하며 비공개 runtime 후보를 만듭니다.
7. **화면 반영** — catalog와 이미지 manifest를 feature 브랜치에 반영하고 기존 immutable Homepage DEV 릴리스 절차로 새 화면을 검증합니다. 등록기가 runtime 후보를 활성화하거나 Homepage를 배포하지는 않습니다.

## 범용 DEV 등록 명령

먼저 상품이 agachichi DEV catalog와 media manifest에 반영된 상태에서 계획만 확인합니다.

```bash
cd /Users/kyouhan/aicontrolcenter-shop-dev-model-front-cutout
python3 ops/macos/shopping/dev_upload_product_register.py --catalog-id ag-upload-outer-0007
```

계획 JSON에서 환경이 `DEV`, 가격/옵션/이미지 개수가 맞고 `mutation=false`인지 확인합니다. 검토 후 DEV WooCommerce에 등록할 때만 명시적으로 적용합니다.

```bash
python3 ops/macos/shopping/dev_upload_product_register.py --catalog-id ag-upload-outer-0007 --apply-dev
```

실행 결과는 WooCommerce 상품 ID, `candidate_staged`, 재고 대기 여부, 주문 수 불변, `prod_mutation=false`, `activation=false`를 반환합니다. 후보 파일은 사용자 전용 DEV runtime 경로에 저장되며 live 설정을 직접 바꾸지 않습니다. 적용 명령은 현재 Mac의 격리 DEV Docker context와 private runtime 파일을 확인하므로 다른 컴퓨터나 PROD에서 실행하면 안 됩니다.

## 등록 전 필수 확인

- 판매가는 사용자가 지정했거나 조사·제안 가격을 명시적으로 확정해야 합니다.
- 주문 가능 상태에는 확인된 실제 옵션과 재고가 필요합니다. 미확인 재고는 0이고 구매할 수 없습니다.
- 소재, 품번, 정품 여부, 치수를 사진만으로 사실처럼 작성하지 않습니다.
- 가격, 옵션 조합, 수량, 대표 이미지, 상세 이미지가 서로 일치하는지 확인합니다.
- 이미지 생성/보정으로 바뀐 요소와 실제 상품 차이가 있을 수 있음을 표시합니다.
- 상품이 기존 SKU 또는 catalog ID와 겹치면 자동 등록하지 않고 충돌로 차단합니다. 부분 실패가 의심되면 재전송하지 말고 상태를 먼저 확인합니다.

## 현재 범위와 다음 단계

- `dev_product_operator.py`는 등록된 상품의 가격·재고·공개 상태 변경과 조회용입니다.
- `dev_upload_product_stage.py`와 `dev_upload_product_promote.py`는 특정 기존 상품에 고정된 도구입니다. 새 상품에 재사용하지 않습니다.
- `dev_upload_batch_register.py`는 기존 검토 배치만 처리합니다.
- 범용 `dev_upload_product_register.py`는 catalog/manifest 검증, read-only plan, 격리 DEV WooCommerce 등록, 결과 readback, idempotent SKU 확인, private mapping/projection 후보 생성까지 지원합니다.
- 이 도구는 ProductDraft API와 연결되지 않았고 후보 활성화나 홈페이지 배포도 하지 않습니다. 다음 과제는 후보 검토/승격을 기존 immutable DEV 릴리스와 연결하고, 이후 새 상품 1건으로 전체 흐름을 검증하는 것입니다.
- PROD와 Ubuntu에는 접근하거나 변경하지 않습니다.


## PROD 운영자 상품 등록과 고객 회원가입은 별도 기능

PROD 고객 회원가입은 현재 정책상 꺼져 있습니다. WooCommerce 로그인과 운영자 상품 등록은 별개라서, 가입 링크가 없어도 운영자는 새 상품을 독립된 PROD WooCommerce 상품/SKU로 등록할 수 있습니다.

새 업로드 상품이 검토된 뒤 먼저 읽기 전용 계획을 실행합니다.

```bash
cd /Users/kyouhan/AIControlCenterRuntime/prod-commerce/build/prod-current
/Users/kyouhan/AIControlCenter/.venv/bin/python ops/macos/shopping/prod_upload_product_register.py --catalog-id <catalog-id>
```

계획 결과에서 `environment=PROD`, `mutation=false`, 가격·옵션·이미지·SKU 상태를 확인합니다. 검토한 정확한 상품만 PROD에 등록할 때 `--apply-prod`를 붙입니다. 이 쓰기 단계는 PROD WooCommerce에 별도 상품과 옵션을 만들고, 미확인 재고는 0으로 두며, private binding/projection 후보를 기록합니다. 주문 수를 전후 비교하고 후보를 활성 공개하지는 않습니다. 상품이 실제 화면에 나오려면 별도의 승인된 immutable release 활성화 단계가 필요합니다.

2026-10-16 read-only PROD plan 확인: `ag-upload-bottom-0002`와 `ag-upload-outer-0006`은 각각 `aicc-prod-` SKU로 이미 PROD에 등록되어 `ALREADY_REGISTERED`를 반환했고, 둘 다 `mutation=false`였습니다. CLI는 기본 macOS Python 대신 위 프로젝트 가상환경으로 실행해야 합니다.
