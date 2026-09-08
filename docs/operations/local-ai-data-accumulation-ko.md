# 로컬 AI 실제 데이터 누적 운영

## 왜 수개월이 필요한가

모델의 한 학습 행에는 `특징 공개 시점`, 당시 알 수 있었던 뉴스·공시·시장 값, 그리고 **그 뒤
5거래일의 종목 수익률과 SPY 수익률**이 모두 필요하다. 오늘 수집한 행은 미래 결과가 없으므로 즉시
학습하지 않는다.

1. 매일 시장 조정주가와 뉴스 원문 메타데이터를 수집한다.
2. SEC 재무 공시는 일주일마다 원래 제출 시각을 보존해 누적한다.
3. `(공개일, 종목)` 중복을 제거하고 원천 파일을 병합한다.
4. 5거래일 뒤 시장 결과가 생긴 행만 SPY 대비 초과수익 정답으로 확정한다.
5. 확정된 `labeled/` 데이터만 시간순 walk-forward 검증에 사용한다.
6. 새 후보가 모든 품질 게이트를 통과할 때만 운영 모델과 교체한다.

이 방식은 무료 API 범위에서 자동화할 수 있다. 다만 과거 뉴스 전문, 애널리스트 예상치, ETF 과거
보유 내역처럼 무료 공급자가 제공하지 않는 PIT 데이터는 추측해 채우지 않고 `unavailable`로 남긴다.

## 매일 실행

`.env`에서 `STOCK_PROVIDER=toss`와 Toss, NewsAPI, SEC 값을 설정한 뒤 하루 한 번 실행한다. API
키는 명령행이나 결과 파일에 기록되지 않는다.

```powershell
docker compose --profile collection run --rm collector --mode all --market-limit 500
```

결과는 `datasets/local-ai-incremental/`에 저장된다.

- `market/`: 5거래일 결과가 확정된 기술·위험 시장 행
- `raw/`: 원본 뉴스 집계
- `news.csv`, `financial.csv`: 공개 시점 기준 전문 AI 특징
- `labeled/`: 공통 5거래일 SPY 상대 정답이 확인된 학습 가능 행
- `collection-state.json`: 마지막 성공 일자와 NewsAPI 일일 사용량
- `dataset-readiness.json`: 중복, 시계열, 검증 표본 수 감사 결과

Windows 작업 스케줄러에는 위 명령을 장 마감 이후 한 번만 등록한다. 수집기가 6시간 이내에 이미
실행 중이면 잠금 파일로 중복 실행을 거절한다. 실패한 작업은 성공 일자를 갱신하지 않아 다음 실행에서
재시도된다.

## 재학습 판단

매월 `dataset-readiness.json`을 확인한다. 최소 조건을 충족한 후보도 다수 클래스 기준 개선,
balanced accuracy, ROC AUC, Brier score, calibration error, 모든 시간 구간의 최소 성능을 함께
통과해야 한다. 이전 모델 선택에 사용하지 않은 최신 기간에서도 개선이 재현되어야 한다.

정확도가 오르지 않으면 알고리즘만 반복 교체하지 않는다. 종목·섹터·시장 국면의 범위를 늘리고,
뉴스·실적 예상치·공매도·ETF 보유 및 자금 흐름처럼 현재 데이터와 다른 정보가 실제로 추가될 때 다시
후보를 검증한다.

새 피처 묶음은 최종 검증 기간을 보고 선택하지 않는다. 아래처럼 후보 묶음을 넘기면 각 외부 fold의
과거 구간 안에서만 기본 피처, ROE 추가, 밸류에이션 전체 추가 중 하나를 선택한다.

```powershell
.venv\Scripts\python.exe scripts/ai/training/nested_walk_forward_local_agent.py `
  --data-dir datasets/local-ai-incremental/labeled `
  --agent financial `
  --candidate-extra-feature-set pit_roe_signed_log `
  --candidate-extra-feature-set pit_roe_signed_log,pit_per_signed_log,pit_pbr_signed_log,pit_psr_signed_log `
  --output artifacts/local-ai-candidates/financial/nested-feature-selection.json
```
