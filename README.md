# StockPilot AI

AI 기반 투자 의사결정 지원 플랫폼입니다. Blueprint v2.1에 따라 시장 데이터, 분석·백테스트, AI 참고 리포트, 본인 계좌 포트폴리오, 참고 알림, 준실시간·KIS 스트리밍 골격을 단계적으로 구현하고 있습니다.

기능 소개는 [프로젝트 소개](docs/architecture/project-introduction.md), 폴더 책임은 [프로젝트 구조](docs/maintenance/project-structure-ko.md)에서 확인할 수 있습니다.

## 실행

```powershell
python -m pip install uv==0.11.28
uv sync --locked --extra dev
uv run python -m uvicorn app.main:app --app-dir backend --reload
```

기본 개발 구성은 디스크 사용량을 줄이기 위해 `PREDICTION_ENGINE=lightweight`를 사용한다.
XGBoost 모델 개발과 관련 테스트가 필요할 때만 `uv sync --locked --extra dev --extra ml`로
ML 의존성을 추가하고 `PREDICTION_ENGINE=xgboost`를 설정한다. Docker에서도 같은 경우에만
`INSTALL_ML=true`로 빌드한다.

검증된 XGBoost artifact의 런타임 재사용은 기본적으로 꺼져 있다. DB와 관리자 키를 구성한
연구 환경에서만 `MODEL_ARTIFACT_ACTIVATION_ENABLED=true`로 켠다. 이때 artifact는
`MODEL_ARTIFACT_DIR`에 체크섬과 함께 저장되며 Git에는 포함되지 않는다. Champion 승격은
artifact의 종목·기간·알고리즘·SHA-256을 검증한 뒤 활성 포인터를 원자적으로 교체한다.

API 문서: `http://127.0.0.1:8000/docs`

프론트엔드는 별도 터미널에서 실행한다. 이미 의존성이 설치된 노트북에서는 재설치하지 않고
아래 명령만 실행하면 된다.

```powershell
pnpm --filter @stockpilot/web dev
```

웹 화면: `http://127.0.0.1:3000`
`http://127.0.0.1:3000/?symbol=005930`으로 검색 후 결과 화면을 바로 확인할 수 있다.

기본값인 `STOCK_PROVIDER=mock`, `AI_REPORT_PROVIDER=mock`에서는 Toss·OpenAI API 키나
외부 호출 비용 없이 검색·차트·참고 시그널 UI를 확인할 수 있다.

## 직접 학습 로컬 분석 AI

외부 LLM API 없이 직접 학습한 5개 전문 모델을 선택적으로 실행할 수 있다. 전문 모델은
기술, 재무, 뉴스·공시, 수급, 위험 분석별로 분리된다. 최종 진단은 품질 승인을 통과한
전문 모델만 신뢰도 가중 규칙으로 조합하며, 검증 성능이 부족한 기존 학습형 종합 모델은
운영 판정에서 제외한다.
모든 모델은 JSON 아티팩트만 로드하며 Pickle이나 원격 모델 코드는 실행하지 않는다. 모델
파일이 없거나 입력 특성이 부족하면 해당 모델만 제외되고 기존 규칙 기반 분석은 계속된다.

학습 CSV는 시간순으로 정렬하고 파일명을 `technical.csv`, `financial.csv`, `news.csv`,
`investor_flow.csv`, `risk.csv`, `synthesis.csv`로 만든다. 각 파일에는 아래 특성과 이진
`label` 열이 필요하다.
마지막 20% 행은 시간순 검증 구간으로 자동 분리되며 파일당 최소 50개 라벨 행이 필요하다.

| 모델      | 특성 열                                                                           | `label=1` 의미                 |
| --------- | --------------------------------------------------------------------------------- | ------------------------------ |
| 기술      | `technical_score,rise_probability,pattern_count,range_width`                      | 설정 기간 뒤 양의 수익률       |
| 재무      | `financial_score,score_coverage,rise_probability`                                 | 다음 관측 시점의 펀더멘털 개선 |
| 뉴스·공시 | `news_score,disclosure_score,warning_count`                                       | 사건 뒤 양의 초과수익          |
| 수급      | `net_quantity,rise_probability,score_coverage`                                    | 다음 관측 시점의 순유입        |
| 위험      | `warning_count,rise_probability,score_coverage,range_width`                       | 설정 기간 안의 하락 위험 사건  |
| 최종 종합 | 각 전문 모델의 `{agent}_probability,{agent}_confidence,{agent}_available` 15개 열 | 설정 기간 뒤 양의 수익률       |

`synthesis.csv`의 전문 모델 확률은 반드시 각 행보다 과거 데이터로만 학습한 모델의
out-of-time 또는 out-of-fold 예측이어야 한다. 전문 모델이 이미 학습한 행을 다시 예측한
in-sample 값은 종합 모델의 성능을 부풀리므로 사용할 수 없다. 라벨 기간이 겹치는 행은
학습·검증 경계에서 제거해야 한다.

```powershell
.venv\Scripts\python.exe scripts/ai/training/train_local_agents.py --data-dir .\datasets\local-ai
$env:LOCAL_AI_ENABLED="true"
$env:LOCAL_AI_ARTIFACT_DIR=".\artifacts\local-ai"
uv run python -m uvicorn app.main:app --app-dir backend --reload
```

학습 결과에는 모델 버전, 시간순 검증 정확도와 Brier score가 저장된다. 데이터 출처,
수집·학습·중첩 검증·수동 승격의 전체 절차는 [직접 학습 AI 설명서](docs/AI_TRAINING_GUIDE_KO.md)를 따른다.
전문 AI마다 다른 정답 기간과 마이그레이션 규칙은 [전문 AI별 예측 기간 정책](docs/architecture/local-ai-horizon-policy-ko.md)에 정리되어 있다.

뉴스·SEC 재무 학습 데이터는 별도 Docker 프로필에서 운영 모델과 분리해 증분 수집한다.
먼저 `docker compose --profile collection run --rm collector --dry-run`으로 예정 작업을 확인한 뒤
`docker compose --profile collection run --rm collector`를 실행한다. 수집기는 일일 호출 상한,
중복 실행 잠금, 시점 기준 결합을 적용하며 모델 artifact에는 접근하지 않는다. 매 실행 후
`datasets/local-ai-incremental/dataset-readiness.json`에 구조 품질과 후보 재학습 준비도를
분리해 기록한다. 자세한 정책은
[로컬 AI 증분 데이터 수집](docs/operations/local-ai-incremental-collection.md)을 참고한다.

Docker Compose 전체 스택은 Nginx를 통해 `http://localhost:8080`에서 접근한다.
서비스 포트는 기본적으로 로컬 호스트에만 바인딩되고, 웹 컨테이너는 Next.js 프로덕션 빌드로 실행된다. 외부 배포 시 `PUBLIC_API_URL`, HTTPS, 강력한 비밀번호와 시크릿 매니저를 별도로 설정해야 한다. 보안 기준은 [보안 설계](docs/architecture/security.md)를 참고한다.

브라우저의 일반 시장 조회는 같은 출처의 읽기 전용 `/api/market/*` BFF를 사용한다. 운영
환경에서는 32자 이상의 `ANALYSIS_API_KEY`를 FastAPI와 Next.js 서버에 동일하게 설정한다.
브라우저 번들에는 이 키가 포함되지 않으며, 임의 URL·주문·계좌·관리자 경로는 시장 BFF가
프록시하지 않는다. 이 공유 키는 사용자 로그인을 대신하지 않으므로 외부 다중 사용자
서비스 전에는 별도 JWT/OAuth와 사용자별 한도가 필요하다.

## 데이터베이스와 스케줄러

```powershell
uv run alembic upgrade head
$env:SCHEDULER_ENABLED="true"
uv run python -m uvicorn app.main:app --app-dir backend --reload
```

스케줄러는 기본적으로 비활성화되어 있다. 활성화하면 `SCHEDULER_SYMBOLS`의 국내·미국
종목 일봉을 raw/cleaned 단계로 주기적으로 적재한다. 기본값은
`005930,000660,035420,AAPL,MSFT`이며 최대 50종목까지 허용한다. 종목당 조회 개수는
`SCHEDULER_INGESTION_LIMIT`으로 30~365 범위에서 설정한다.

Docker PostgreSQL 구성은 `PARTITION_MAINTENANCE_ENABLED=true`를 기본으로 사용해 다음
3개월의 `stock_candles` 월별 파티션을 서버 시작 시점과 매월 20일에 미리 생성한다. 로컬
SQLite에서는 이 작업을 실행하지 않는다.

관리자 운영 화면은 `PARTITION_ARCHIVE_AFTER_MONTHS`(기본 120개월)보다 오래된 완결 월
파티션을 아카이브 검토 대상으로 표시한다. 이는 비파괴 미리보기이며 자동 이동·분리·삭제를
수행하지 않는다. 실제 작업 전에는 [캔들 파티션 아카이브 정책](docs/architecture/candle-partition-archive.md)을 따른다.

`PERSISTENCE_ENABLED=true`이면 백테스트 결과와 활성 Score 가중치를 DB에 연결한다. 이 옵션을 켜기 전에 `alembic upgrade head`를 실행해야 한다. Docker Compose에서는 마이그레이션 후 자동으로 활성화된다.

관리자 화면 `/admin`에서는 백테스트 이력, 데이터 품질 로그, 캔들 수집·보정 기준 현황, 관심 종목,
가격 참고 알림을 관리할 수 있다. 수동 수집은 선택한 종목의 raw/cleaned 캔들과 품질 로그만
DB에 저장하며 주문이나 계좌 변경을 실행하지 않는다. `ADMIN_UI_USERNAME`과
`ADMIN_UI_PASSWORD`를 설정하면 관리자 화면과 BFF가 HTTP Basic 인증으로 보호된다.
운영 환경에서는 두 값이 필수이며 반드시 HTTPS 뒤에서 사용해야 한다. 자동 가격 평가는
`REFERENCE_ALERTS_ENABLED=true`로 켜며 DB 저장이 필수다. 참고 알림은 조건 도달만 기록하고
주문은 실행하지 않는다. 자세한 내용은 [참고 알림 설계](docs/architecture/reference-alerts.md)를 확인한다.

기업행동 이력 화면은 액면분할·배당락 등의 revision, 효력일과 알려진 시각을 읽기 전용으로
표시한다. 보정 엔진은 명시적인 `unadjusted` 캔들에만 point-in-time 뷰를 만들며 raw/cleaned
행을 수정하지 않는다. 수집 계층은 `verified` 공급자만 허용하고 revision 배치를 원자적·멱등으로
저장하며, 실제 공급자가 등록되기 전에는 비활성화된다. DART와 SEC EDGAR는 현재 실험 후보로
표시되며 자동 보정에는 사용되지 않는다. 자세한 기준은
[기업행동 보정 설계](docs/architecture/corporate-action-adjustments.md)를 확인한다.
`DART_API_KEY`가 설정된 서버에서는 관리자가 최근 1년의 무상증자·감자 공시 후보를 읽기
전용으로 조회할 수 있지만, 후보는 자동 저장·확정·분석 반영되지 않는다.
DART 원본·정정 접수는 별도 revision 그룹 후보로 표시되지만, 공식 API에 직접 연결 필드가
없으므로 수동 원문 확인 전에는 동일 사건으로 저장되지 않는다.
`CORPORATE_ACTION_APPROVAL_ENABLED=true`를 명시하면 관리자 API에서 DART 후보 하나를
재조회하고 KRX 근거 URL과 함께 confirmed revision으로 승인할 수 있다. 이 기능은 DB,
`ADMIN_API_KEY`, `DART_API_KEY`가 모두 필요하며 기본적으로 꺼져 있다. 승인 시각이
`known_at`이 되며 승인 근거와 revision은 원자적으로 저장된다. 자동 주문이나 기존 캔들
수정은 수행하지 않는다.
KRX 공개 OPEN API에는 기업행사 효력일 전용 서비스가 확인되지 않아 자동 대조는 꺼져
있다. 계약형 EOD 종목이벤트 참조정보는 별도 Provider 후보로 분리했으며, 실제 명세와
이용 조건을 검증하기 전에는 승인 근거로 자동 사용하지 않는다.
미국은 Nasdaq Daily List와 NYSE Market Event Feed를 상장 거래소별 기본 후보로 두고,
SEC EDGAR는 공시 교차검증 용도로만 사용한다. 두 거래소 데이터와 DTCC 후보는 계약 및
재배포 조건이 확인되기 전까지 `experimental`이며 자동 보정에 연결되지 않는다.
백테스트는 기본적으로 기업행동 보정을 사용하지 않는다. DB에 검증된 revision이 있을 때만
`corporate_action_mode=forward_point_in_time`을 명시할 수 있으며, 과거 신호를 미래 사건으로
재작성하지 않는 전방 보정을 사용한다. 정정·취소 이력이 복잡하거나 캔들 기준이 명확하지
않으면 실행을 거부한다.
신규 캔들 적재는 Provider 출처를 함께 저장한다. 기존 행은 임의 추정하지 않고
`legacy_unknown`으로 보존하며, 관리자용 읽기 전용 inventory API에서 `price_basis`와 출처별
현황만 확인할 수 있다. 신규 데이터는 Provider의 버전화된 보정 기준과 반환값이 일치해야
모든 분석 경로로 전달되며, 해당 규칙 버전도 함께 저장된다. 자세한 내용은
[캔들 보정 기준 provenance와 inventory](docs/architecture/candle-price-basis-inventory.md)를 확인한다.

`ACCOUNT_SYNC_ENABLED=true`이면 `/admin`에서 마스킹된 본인 계좌를 수동 동기화하고 통화별 포트폴리오 집중도와 손실 노출을 확인할 수 있다. 계좌 API는 관리자 키로 보호된다. 실제 주문 API는 별도 `TOSS_TRADING_ENABLED`와 정확한 확인 문구가 모두 있어야 실행되며 기본값은 잠금이다.

## 현재 범위

- Provider Capability 선언 및 기능 기반 Broker Adapter 라우팅
- 시드 기반 Mock 시세·호가·캔들 데이터
- 표준 API 응답 envelope 및 request ID
- 투자 자문이 아님을 명시하는 compliance 메타데이터

`STOCK_PROVIDER=toss`와 Toss OAuth 자격증명을 설정하면 현재가·캔들·호가·체결·종목·수급·시장 지표를 Toss Open API에서 조회합니다. 본인 계좌 동기화와 실제 주문은 각각 별도 기능 플래그로 보호됩니다. `REALTIME_SOURCE=toss` 또는 `kis`를 설정하면 해당 공급자의 WebSocket 시세를 사용할 수 있습니다.

## 노트북 검증

기본 노트북 환경에서는 ML 추가 의존성 없이 다음 검증을 실행한다. XGBoost 전용 테스트는
자동으로 제외된다.

```powershell
.venv\Scripts\pytest.exe -q -m "not ml"
& .venv\Scripts\ruff.exe check backend
frontend\node_modules\.bin\tsc.CMD -p frontend/tsconfig.json --noEmit --incremental false
```

XGBoost 장기 학습·artifact 검증은 `uv sync --locked --extra dev --extra ml`를 사용한 데스크톱
또는 CI에서 `pytest -q -m ml`로 별도 실행한다.
