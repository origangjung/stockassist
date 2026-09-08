# KIS 국내 투자자 수급 후보 학습 기록

## 목적

KIS의 종목별 투자자매매동향(일별)을 이용해 외국인, 기관, 개인 순매수 흐름이
이후 5거래일의 KODEX 200 대비 초과수익 방향을 설명하는지 검증한다.

## 데이터와 보안

- 원천: KIS 국내주식 시세분석 읽기 전용 API
- 종목: 국내 대형주 28개
- 기간: 2026-06-18 ~ 2026-08-07
- 학습 행: 362개, 고유 거래일 36개
- 피처: 거래량 대비 주체별 순매수, 5일/20일 평균, 20일 z-score, 외국인·기관 방향 일치율
- 라벨: 이후 5거래일 종목 수익률이 KODEX 200보다 낮으면 1
- 비밀값: `KIS_APP_KEY`, `KIS_APP_SECRET`은 `.env`에서만 읽고 산출물에는 저장하지 않음
- 주문 API는 호출하지 않음

## 시계열 검증 결과

4개 워크포워드 폴드와 1거래일 purge를 적용했다. 최적 후보의 정확도는 79.08%였지만
검증 구간 다수 클래스 기준과 같았고, 균형 정확도는 50.00%, AUC는 50.09%였다.
따라서 방향을 구분한 증거가 없으며 운영 모델로 승격하지 않았다.

현재 KIS 응답은 종목별 30~60거래일만 안정적으로 확보되어 시장 국면이 한쪽으로
치우쳐 있다. 일별 누적 수집으로 최소 6개월과 여러 시장 국면을 확보한 뒤 재검증한다.
`--resume`은 기존 날짜를 보존하고 같은 종목의 새 날짜만 병합하므로 아래 수집 명령을
매일 한 번 실행할 수 있다.

## 재현 명령

```powershell
.venv\Scripts\python.exe scripts\ai\data\build_kis_flow_local_ai_dataset.py `
  --history-days 730 `
  --output-dir datasets\kis-flow-candidate-20260815 `
  --resume

.venv\Scripts\python.exe scripts\ai\training\walk_forward_local_agents.py `
  --data-dir datasets\kis-flow-candidate-20260815 `
  --agent investor_flow `
  --splits 4 `
  --purge-timestamps 5 `
  --use-all-safe-features
```

## 매일 자동 누적

기존 로컬 AI 수집 작업의 `all` 모드에 `kis_flow`가 포함된다. KIS 데이터는 FINRA
데이터를 덮어쓰지 않고 `datasets/local-ai-incremental/kis-flow/`에 저장된다. Docker
collector에는 `.env`의 KIS 키만 환경변수로 전달하며 명령줄과 로그에는 넣지 않는다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts/operations/run_local_ai_collection.ps1 -DryRun
```

실제 예약 작업은 매일 18:30에 실행되는 기존 `StockPilot-LocalAI-Collection`을 그대로
사용한다. KIS API만 실패하면 나머지 수집 결과와 상태는 보존하지만 실행 종료 코드는
실패로 반환해 작업 로그에서 확인할 수 있게 한다.

2026-08-15 Docker 실제 수집에서는 25종목 445행을 저장했고 중복, 결측, 비정상 숫자,
미래 시각이 없음을 확인했다. 검증 구간은 4개 날짜 97행이라 아직 수집 단계다. 445행
워크포워드 후보의 정확도 69.87%는 다수 클래스 기준과 같았고, 균형 정확도 50.00%,
AUC 0.5640이므로 운영 모델로 승격하지 않았다.
