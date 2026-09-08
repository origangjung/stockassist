# 로컬 AI 증분 데이터 수집

`scripts/ai/data/collect_local_ai_incremental.py`는 제공자 자격 증명을 명령행이나 생성 CSV에 넣지 않고
시점 기준 뉴스와 SEC 재무 특성을 누적한다.

## 안전 정책

- 뉴스는 서울 날짜 기준 하루 한 번, SEC 재무는 기본 7일에 한 번만 수집한다.
- NewsAPI 요청 수를 실행 전에 `collection-state.json`에 예약하므로 강제 재실행도
  `NEWS_API_DAILY_REQUEST_LIMIT`을 넘지 못한다.
- 동시 실행 잠금으로 두 수집기가 호출 예산과 상태 파일을 함께 수정하지 못하게 한다.
- 재무 행은 기존 이력을 교체하지 않고 시각과 종목 기준으로 병합한다.
- 뉴스 원본 특성은 `raw/news.csv`에 보존한다. 당시 공개된 FRED 문맥이 완성된 행만 학습용
  `news.csv`에 기록하므로 늦게 공개된 거시 관측치는 기사 본문 재수집 없이 나중에 보완할 수 있다.
- API 키, 인증 헤더, 기사 본문, 제공자 원본 응답은 저장하지 않는다.
- 출력 경로는 Git에서 제외한 프로젝트 `datasets` 디렉터리 내부로 제한한다.
- 수집이 끝날 때 `dataset-readiness.json`을 원자적으로 갱신한다. 이 보고서는 CSV 구조 검사와
  후보 재학습 준비도를 분리하며 원시 특성 값이나 자격 증명을 포함하지 않는다.
- `LOCAL_AI_COLLECTION_SYMBOLS`를 비워 두면 기술, 통신, 소비재, 금융, 헬스케어, 산업재,
  에너지, 유틸리티, 부동산, 소재로 나눈 기본 미국 기업군을 사용한다. SEC 기업 재무와 성격이
  다른 ETF는 이 목록에서 제외한다. 기본 목록은 85개로 NewsAPI 일일 상한 90개 안에 둔다.

## Docker로 실행

먼저 외부 요청 없이 오늘 실행할 작업과 종목 수만 확인한다.

```powershell
docker compose --profile collection run --rm collector --dry-run
```

확인 후 실제 수집을 실행한다. 같은 날 다시 실행하면 완료된 작업은 건너뛴다.

```powershell
docker compose --profile collection run --rm collector
```

## Windows에서 매일 자동 실행

작업 스케줄러에는 API 키를 인자로 넣지 않고, 저장소의 실행 스크립트 경로만 등록한다.
기본 시각은 한국·미국의 직전 정규장 데이터를 함께 확인하기 쉬운 매일 18:30이다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/operations/register_local_ai_collection_task.ps1
```

등록 전에 실제 수집 없이 Docker 연결과 예정 작업만 확인할 수 있다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/operations/run_local_ai_collection.ps1 -DryRun
```

실행 로그는 Git에서 제외된 `datasets/local-ai-incremental/task-logs/`에 저장한다. 로그 필터는
secret, token, API key, Authorization 형태의 값을 기록하지 않는다. Docker Desktop이 꺼져
있으면 해당 실행은 실패로 기록되며, `StartWhenAvailable` 설정에 따라 다음 사용 가능 시점에
다시 시도할 수 있다. 작업을 제거하려면 다음 명령을 사용한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/operations/unregister_local_ai_collection_task.ps1
```

이 컨테이너는 읽기 전용 루트 파일 시스템, 전체 Linux capability 제거, 제한된 CPU·메모리를
사용하며 `datasets`만 쓰기 가능하다. 운영 모델과 artifact에는 접근하지 않는다. NewsAPI 등
외부 제공자의 실제 무료 한도와 이용 조건은 계정 요금제를 따르며 프로젝트는 설정된 일일 상한만
강제한다.

## 재학습 준비도 읽기

`datasets/local-ai-incremental/dataset-readiness.json`의 `status`는 파일 구조가 안전한지를,
`training_readiness`는 후보 재학습에 필요한 검증 표본과 시간 구간이 충분한지를 나타낸다.

- `status=failed`: 결측, 중복, 잘못된 숫자, 미래 시각, 정렬 또는 라벨 문제를 먼저 수정한다.
- `training_readiness=collect_more_data`: 파일은 정상이지만 검증 표본·기간·클래스가 부족하다.
- `training_readiness=ready_for_candidate_training`: 별도 후보 디렉터리에서 재학습과
  purged walk-forward 비교를 실행할 수 있다. 운영 모델 자동 승격을 뜻하지 않는다.

준비된 데이터만 중첩 시간 검증하고 결과를 운영 artifact와 분리하려면 다음 명령을 사용한다.

```powershell
.venv\Scripts\python.exe scripts/ai/training/validate_local_ai_candidates.py `
  --data-dir datasets/local-ai-incremental/labeled `
  --output-dir artifacts/local-ai-candidates/incremental
```

이 명령은 `promotion_ready` 판정까지만 기록하며 `artifacts/local-ai/`의 운영 모델을 복사하거나
교체하지 않는다. `--dry-run`을 추가하면 실제 학습 없이 준비된 AI와 제외 사유만 기록한다.

2026-08-14 SEC 확장 수집 후 재무 데이터는 1,217행·68종목, 검증 244행·119개 시점으로
`ready_for_candidate_training` 상태다. 뉴스 데이터는 3행, 검증 시점 1개라 계속
`collect_more_data` 상태다. 재무 후보 결과는
[재무 AI SEC 확장 후보 검증 기록](local-ai-financial-candidate-20260814.md)에 정리했다.

## 로컬 Python으로 실행

```powershell
.venv\Scripts\python.exe scripts/ai/data/collect_local_ai_incremental.py `
  --symbols AAPL MSFT NVDA TSLA AMZN GOOGL META JPM BAC WMT JNJ XOM KO DIS AMD `
  --output-dir datasets/local-ai-incremental
```

## 장기 데이터 보강 기준

- 시장 데이터는 매일 `--market-limit 2600` 범위로 다시 생성해 약 10년의 학습 이력을 유지한다.
  더 짧은 범위를 지정하면 기존 CSV가 교체되어 장기 이력이 줄어들 수 있으므로 운영 수집에서는 축소하지 않는다.
- 뉴스는 무료 일일 요청 한도 안에서 하루 22개 종목을 순환하며 7일 구간 4개를 조회한다.
  약 4일마다 전체 종목의 최근 한 달을 다시 확인하고 기존 행과 중복 없이 병합한다.
- SEC 재무는 7일마다 확인하고 종목당 최근 40개 분기를 보존한다.
- FINRA 수급은 7일마다 확인하고 `--flow-market-limit 2600` 범위의 주가 문맥과 결합한다.
- 뉴스는 공급자의 무료 과거 검색 범위를 따르며, 5거래일 뒤 결과가 확인되기 전에는 학습하지 않는다.
- 장기 백필 검증 결과는 [2026-08-15 백필 기록](local-ai-backfill-20260815.md)에 남겼다.

`--dry-run`은 제공자 요청 없이 예정 작업을 확인한다. `--force`를 사용해도 상태 파일에 보존된
NewsAPI 일일 요청 한도는 우회할 수 없다.

## 초기 수집 결과

2026-08-13 실행에서는 13개 기업의 재무 234행과 8개 기업의 뉴스 특성 11행을 수집했다.
뉴스 3행은 FRED 문맥까지 완성됐다. 두 학습 파일은 중복, 결측, 유한값, 시각 순서, 미래 날짜
검사를 통과했고 자격 증명 이름을 재귀 검사한 결과 비밀값은 발견되지 않았다.

이 행들은 계속 실험 데이터다. 최소 검증 표본 조건과 새로운 purged walk-forward 비교를
통과하기 전에는 재무·뉴스 운영 모델을 재학습하거나 승격하지 않는다.
