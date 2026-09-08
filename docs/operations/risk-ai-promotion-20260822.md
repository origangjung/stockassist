# 위험 AI 승격 기록 (2026-08-22)

## 결과

- 승격 버전: `local-risk-1fb586e522e2`
- 이전 버전: `local-risk-58e5aa3bd7d0`
- 운영 아티팩트: `artifacts/local-ai/risk.json`
- 이전 버전 백업: `artifacts/local-ai-history/risk-local-risk-58e5aa3bd7d0.json`
- 후보 및 검증 보고서: `artifacts/local-ai-candidates/risk-promotion-20260822`

## 승격 설정

- 데이터: `datasets/local-ai-backfill-20260815/risk.csv`
- 입력: 가격 위험 지표 7개와 FRED 거시 지표 5개
- 시간 창: 최근 378거래일
- 모델: 로지스틱 회귀, `C=0.002`, 기본 클래스 가중치
- 판단 임계값: `0.5`
- 검증: 외부 5구간, 내부 3구간의 중첩 시계열 검증과 5거래일 purge
- 최종 학습: 홀드아웃 지표를 먼저 고정한 뒤 최근 창 전체로 계수를 재학습

## 중첩 시계열 검증

| 지표 | 결과 |
|---|---:|
| 정확도 | 64.26% |
| 다수 클래스 기준 | 63.36% |
| 기준 대비 개선 | +0.91%p |
| 균형 정확도 | 53.49% |
| ROC-AUC | 55.78% |
| Brier score | 0.2402 |
| 최저 구간 기준 개선 | +0.22%p |
| 최저 구간 균형 정확도 | 50.34% |

모든 외부 구간에서 기준 정확도와 50% 균형 정확도를 넘었으므로 승격 게이트를 통과했다.

## 최종 후보 홀드아웃

| 지표 | 결과 |
|---|---:|
| 정확도 | 59.63% |
| 다수 클래스 기준 | 59.18% |
| 기준 대비 개선 | +0.45%p |
| 균형 정확도 | 56.85% |
| ROC-AUC | 60.45% |
| Brier score | 0.2358 |
| ECE | 0.0711 |
| 검증 표본 | 6,460건 |

## 재현 명령

```powershell
.venv\Scripts\python.exe scripts\ai\training\validate_local_ai_candidates.py `
  --data-dir datasets\local-ai-backfill-20260815 `
  --output-dir artifacts\local-ai-candidates\risk-promotion-20260822 `
  --agent risk --c-grid 0.002 `
  --max-training-timestamps 378 `
  --fixed-decision-threshold 0.5
```

후보가 다시 게이트를 통과한 경우에만 `approve_local_ai_candidate.py`로 승인한다. 승인 도구는 현재 버전을 이력 폴더에 먼저 복사하고 새 파일을 원자적으로 교체한다.

