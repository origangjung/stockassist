# StockPilot 직접 학습 AI 설명서

이 문서는 외부 LLM API 없이 StockPilot이 보유한 전문 AI를 어떤 데이터로 만들고, 사용자가 직접 어떻게 다시 학습하는지 설명합니다. 모델 출력은 투자 권유가 아니라 검증 품질을 함께 표시하는 참고 신호입니다.

## 1. 전체 구조

종목 하나를 분석할 때 전문 모델 5개가 각자 특성을 계산합니다.

| AI | 보는 데이터 | 현재 목표 |
|---|---|---|
| 기술 AI | 가격·거래량, 수익률, 이동평균 괴리, 변동성, 시장 대비 성과 | 이후 수익률 방향 |
| 재무 AI | DART·SEC 시점 기준 실적, 성장성, 수익성, PER·PBR·PSR·ROE | 미래 재무 개선 가능성 |
| 뉴스 AI | 공개 시각이 확인된 뉴스·SEC 이벤트, 감성·빈도, FRED 거시 환경 | 이후 뉴스 톤 개선 |
| 수급 AI | KIS 투자자 수급, FINRA 공매도, 거래량·가격 문맥 | 공매도 압력 증가 여부 |
| 위험 AI | 변동성, 낙폭, 시장·섹터·VIX·금리·환율 | 이후 하방 사건 발생 여부 |

주식 최종 결과는 품질 게이트를 통과한 전문 AI만 신뢰도 가중 규칙으로 합칩니다. 기존 학습형 `synthesis`의 검증 성능이 베이스라인을 넘지 못해 운영 최종 판정에는 사용하지 않습니다. ETF는 ETF 기술·위험 모델과 자산군 특성을 별도로 사용합니다.

## 2. 데이터 출처

- Toss Open API: 국내·미국 종목 마스터, 조정 시세, 캔들, 체결, 호가, 시장 지표
- KIS Open API: 국내외 가격과 국내 투자자별 수급
- DART: 한국 기업 공시와 시점 기준 재무제표
- SEC EDGAR: 미국 기업 제출 문서와 제출 시각
- FRED: 금리, 장단기 금리차, 달러·거시 시계열
- FINRA: 미국 공매도 거래량과 관련 수급 지표
- NewsAPI 등 허용된 뉴스 공급자: 공개 시각과 출처가 있는 기사 메타데이터
- Alpha Vantage EARNINGS: 분기별 실제 EPS, 애널리스트 예상 EPS와 서프라이즈
- 파생 데이터: SPY·섹터 ETF 대비 수익률, 변동성, 이동평균, 최대 낙폭, ETF 자산군

API 키는 `.env`에서만 읽으며 CSV와 모델 JSON에는 저장하지 않습니다. 데이터 결합은 각 행의 `timestamp` 시점에 이미 공개된 값만 사용해 미래 정보 누출을 막습니다.

## 3. 저장 위치

- `datasets/local-ai-incremental/`: 예약 수집 원본과 라벨 데이터
- `datasets/local-ai-*`: 실험별 고정 데이터 스냅샷
- `artifacts/local-ai/`: 현재 서비스가 읽는 운영 모델
- `artifacts/local-ai-candidates/`: 검증 중인 후보 모델
- `artifacts/local-ai-history/`: 교체 전 운영 모델 이력

이 디렉터리는 용량과 개인정보·라이선스 문제 때문에 Git에 올리지 않습니다.

## 4. 학습 방식

1. 숫자 특성을 CSV로 만들고 `timestamp`, `symbol`, `label`을 검증합니다.
2. 중복 종목·시각, 결측, 무한대, 시간 역전과 미래 공개 데이터 혼입을 거부합니다.
3. 랜덤 셔플 없이 시간순 앞 80%를 학습, 뒤 20%를 검증에 사용합니다.
4. 로지스틱 회귀를 기본 모델로 학습하고 표준화 값·계수·검증 지표를 JSON으로 저장합니다.
5. 후보는 purge 구간이 있는 중첩 워크포워드 검증을 거칩니다.
6. 정확도뿐 아니라 다수 클래스 베이스라인, balanced accuracy, ROC-AUC, Brier score, calibration error와 검증 표본 수를 확인합니다.
7. 모든 품질 기준을 통과한 후보만 명시적으로 운영 폴더에 승격합니다. 자동 승격은 하지 않습니다.

## 5. 현재 운영 artifact 참고 수치

2026-08-13 저장 artifact의 단순 검증 정확도는 기술 55.21%, 재무 71.64%, 뉴스 77.55%, 수급 74.66%, 위험 65.74%, 기존 학습형 종합 51.54%입니다. ETF 기술은 58.11%, ETF 위험은 81.83%입니다.

재무 327건, 뉴스 190건처럼 표본이 작은 모델의 높은 정확도는 신뢰하면 안 됩니다. 기술 모델은 22,869건이지만 정확도가 당시 다수 클래스 베이스라인과 같고, 기존 종합 모델도 베이스라인보다 낮습니다. 따라서 화면과 런타임은 품질 게이트를 통과하지 못한 모델을 제외하고 `experimental` 또는 데이터 부족 상태를 표시합니다.

## 6. 직접 실행하기

프로젝트 루트 `C:\insat`에서 실행합니다.

### 6.1 Docker 상태 확인

```powershell
docker compose up -d
docker compose ps
```

### 6.2 데이터 수집 미리보기

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\operations\run_local_ai_collection.ps1 -DryRun
```

### 6.3 실제 증분 수집

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\operations\run_local_ai_collection.ps1
```

수집기는 뉴스 호출량을 제한하고 상태 파일을 사용해 이미 처리한 구간을 다시 요청하지 않습니다.

### 6.4 실적 예상치 데이터 준비

Alpha Vantage 공식 무료 키를 발급한 뒤 `.env`의 `ALPHA_VANTAGE_API_KEY`에만 입력합니다.
무료 한도는 하루 25회이므로 수집기는 한 번에 최대 25종목만 처리하며, 키와 원시 응답은
CSV에 저장하지 않습니다.

```powershell
.venv\Scripts\python.exe scripts\ai\data\collect_earnings_expectations.py --dry-run
.venv\Scripts\python.exe scripts\ai\data\collect_earnings_expectations.py
```

전체 종목이 쌓인 뒤 재무 후보와 시점 기준으로 결합합니다.

```powershell
.venv\Scripts\python.exe scripts\ai\data\enrich_financial_earnings_expectations.py `
  --financial datasets\local-ai-incremental\labeled\financial.csv `
  --earnings datasets\local-ai-incremental\earnings\earnings.csv `
  --output datasets\local-ai-financial-expectations\financial.csv
```

같은 실적 기록을 기술 AI의 일별 10거래일 후보에 결합할 때는 아래 명령을 사용합니다.
각 행에는 그 날짜에 이미 공개된 가장 최근 실적만 들어가며, 발표 전 행은 제외됩니다.

```powershell
.venv\Scripts\python.exe scripts\ai\data\enrich_technical_earnings_expectations.py `
  --technical datasets\local-ai-incremental\market\technical.csv `
  --earnings datasets\local-ai-incremental\earnings\earnings.csv `
  --output datasets\local-ai-technical-earnings\technical.csv
```

장 마감 후 발표된 실적은 다음 영업일부터만 사용합니다. 예상치 특성도 기존 품질 게이트와
중첩 시간 검증을 통과하기 전에는 운영 재무 모델에 반영하지 않습니다.

### 6.5 데이터 감사

```powershell
.venv\Scripts\python.exe scripts\ai\training\audit_local_ai_datasets.py `
  --data-dir datasets\local-ai-incremental\labeled `
  --output datasets\local-ai-incremental\labeled\audit-report.json
```

감사 결과가 `ready`가 아니면 학습하지 말고 결측 특성, 표본 수, 시점 순서를 먼저 해결합니다.

### 6.6 후보 학습과 중첩 검증

```powershell
.venv\Scripts\python.exe scripts\ai\training\validate_local_ai_candidates.py `
  --data-dir datasets\local-ai-incremental\labeled `
  --output-dir artifacts\local-ai-candidates\manual
```

이 명령은 운영 모델을 바꾸지 않습니다. `validation-summary.json`에서 각 모델의 `promotion_ready`와 베이스라인 대비 개선폭을 확인합니다.

### 6.7 후보 수동 승격

검증 보고서에 기록된 정확한 모델 버전을 사용합니다.

```powershell
.venv\Scripts\python.exe scripts\ai\training\approve_local_ai_candidate.py `
  --candidate-dir artifacts\local-ai-candidates\manual `
  --agent technical `
  --approve-version "검증보고서의-model_version"
```

승격 전 운영 모델은 `artifacts/local-ai-history/`에 보관됩니다. `promotion_ready=false`인 후보는 명령이 거부합니다.

### 6.8 결과 확인

```powershell
.venv\Scripts\python.exe scripts\ai\training\report_local_ai_accuracy.py --include-etf
.venv\Scripts\python.exe -m pytest -q
```

## 7. GPU 사용

기본 로지스틱 모델은 CPU로도 빠르게 학습됩니다. XGBoost GPU 실험은 다음 명령으로 가능하지만 검증을 통과하지 않으면 운영 모델을 교체하지 않습니다.

```powershell
docker compose --profile training run --rm trainer `
  python scripts/ai/training/benchmark_gpu_xgboost_local_ai.py --help
```

GPU 사용 여부보다 시간 누출 방지, 더 긴 시장 국면, 충분한 이벤트 표본과 베이스라인 대비 개선이 정확도에 더 중요합니다.

## 8. 정확도를 높일 때 지킬 순서

1. 재무·뉴스의 검증 표본을 최소 수천 건까지 늘립니다.
2. 상승장·하락장·고금리·저금리처럼 서로 다른 국면을 포함합니다.
3. 정답 기간과 기준을 전문 AI 사이에서 일관되게 정의합니다.
4. 특성의 실제 공개 시각과 수정 이력을 보존합니다.
5. 종목·섹터 편중을 점검하고 워크포워드 fold별 성능을 확인합니다.
6. 새 알고리즘은 동일 데이터·동일 fold에서 현재 champion과 비교합니다.
7. 단순 정확도 하나가 아니라 calibration과 거래 비용 반영 결과까지 확인합니다.

데이터를 많이 넣는 것만으로 정확도가 오르지는 않습니다. 품질이 낮거나 미래 정보가 섞인 데이터는 숫자를 높여 보여도 실제 서비스 성능을 악화시킵니다.
