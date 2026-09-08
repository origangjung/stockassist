# 기술 AI 실적 이벤트 후보 준비 기록: 2026-08-30

## 현재 상태

- `ALPHA_VANTAGE_API_KEY`: 미설정
- 수집된 실적 예상 데이터: 없음
- 수집 대상: 미국 주식 85종목
- 무료 한도 적용: 하루 최대 25종목
- 드라이런: 첫 실행 25종목 선택, 나머지 60종목 순환 대기

키가 없으므로 네트워크 호출과 실제 데이터 생성은 수행하지 않았다. 임의 데이터로
학습하거나 예상 EPS를 다른 값으로 대체하지 않는다.

## 이번 보완

`enrich_technical_earnings_expectations.py`를 추가했다. 실적 데이터가 수집되면 기술
AI의 각 날짜에 그날 이미 공개된 가장 최근 분기 실적만 과거 방향으로 결합한다.

생성 피처는 EPS 서프라이즈 방향·크기, 전년 대비 EPS 성장, 연속 어닝 비트,
발표 후 경과일, 발표 후 3일·10일 이벤트 구간이다. 발표 전 행과 미래 실적은
사용하지 않으며 잘못된 날짜·빈 종목은 조용히 제외하지 않고 실패 처리한다.

출력은 `datasets` 아래 별도 후보 CSV에 원자적으로 저장한다. 원본 기술 데이터와
운영 모델은 수정하지 않으며 API 키, 원본 응답도 저장하지 않는다.

수동 수집과 예약 수집의 표준 원천 경로를
`datasets/local-ai-incremental/earnings/earnings.csv`로 통일했다. 자동 수집기는
실적 원천과 대상 CSV가 모두 존재할 때만 아래 후보를 재생성한다.

- `datasets/local-ai-incremental/earnings-candidates/technical.csv`
- `datasets/local-ai-incremental/earnings-candidates/financial.csv`

후보 생성은 학습이나 운영 승격을 실행하지 않는다. 키가 없는 현재 드라이런에서는
`earnings:no_api_key`로 안전하게 건너뛰는 것을 확인했다.

기술 후보가 생성되면 `earnings-candidates/readiness.json` 감사 보고서도 자동으로
갱신한다. 다음 조건을 모두 만족해야만 `ready_for_validation`이 된다.

- 후보 10,000행 이상
- 고유 시점 500개 이상
- 종목 20개 이상
- 발표 후 10일 이벤트 행 200개 이상
- 원본 기술 데이터 대비 커버리지 20% 이상
- 중복·비정상 숫자·5일 타깃·미래 실적 결합이 한 건도 없음

조건 미달은 수집 작업 실패가 아니라 `collect_more_data`와 구체적인 사유로 기록한다.
감사 통과는 검증을 허용할 뿐 운영 모델 승격을 의미하지 않는다.

주간 후보 검증 작업은 안전한 `readiness.json`의 상태가
`ready_for_validation`일 때만 ML 전용 trainer에서 실적 회귀를 실행한다. 준비 파일이
없거나, 심볼릭 링크이거나, 1MB를 초과하거나, JSON이 손상됐거나, 상태가 기준 미달이면
실적 검증 타깃 자체를 추가하지 않는다.

검증에서는 기본 기술 피처와 기본+실적 이벤트 피처를 각 외부 학습 기간 안에서만
선택하고, 10개 시점 purge와 BLAS 1스레드 제한을 적용한다. 결과는 아래 후보 경로에
원자적으로 저장하며 자동 승격은 계속 비활성화한다.

`artifacts/local-ai-candidates/technical-earnings/nested-validation.json`

주간 작업은 같은 검증 행과 외부 fold로 아래 세 단계를 순서대로 수행한다.

1. 기본 기술 피처만 사용한 `base-validation.json`
2. 내부 시간 검증에서 기본과 기본+실적 피처를 선택한 `nested-validation.json`
3. 두 보고서를 비교한 `promotion-assessment.json`

승격 가능 판정에는 전체 MAE 개선, 수익률 상관 유지, 모든 외부 구간의 MAE 개선,
발표 후 10일 표본 200개 이상, 같은 이벤트 표본의 MAE·방향 적중률 개선, 실적 피처가
외부 fold 절반 이상에서 선택되는 조건이 모두 필요하다. 이벤트 방향 적중률은 최소
55% 이상이어야 한다. 조건을 통과해도 `automatic_promotion=false`이며 실제 운영 모델
교체는 별도의 수동 승인 없이는 수행하지 않는다.

## 키 설정 후 순서

```powershell
.venv\Scripts\python.exe scripts\ai\data\collect_earnings_expectations.py

.venv\Scripts\python.exe scripts\ai\data\enrich_technical_earnings_expectations.py `
  --technical datasets\local-ai-incremental\market\technical.csv `
  --earnings datasets\local-ai-incremental\earnings\earnings.csv `
  --output datasets\local-ai-technical-earnings\technical.csv
```

85종목은 무료 한도 때문에 최소 4일에 걸쳐 한 차례 수집한다. 이후 데이터 커버리지
감사와 시간순 중첩 검증을 통과하기 전에는 운영 모델에 반영하지 않는다.
