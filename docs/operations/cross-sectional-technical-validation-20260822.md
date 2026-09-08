# 기술 AI 횡단면 순위 타깃 검증 (2026-08-22)

## 목적

AraAI와 Qlib의 공개 설계를 참고해 절대 상승 여부 대신 같은 거래일의 종목 간
5거래일 미래 초과수익 순위를 예측하는 후보를 검증했다. 외부 저장소 코드는
복사하지 않았으며, 현재 데이터 계약과 보안 규칙에 맞게 독립 구현했다.

## 데이터 생성

- 원본: `datasets/local-ai-github-20260822/technical.csv`
- 후보: `datasets/local-ai-cross-sectional-20260822/technical.csv`
- 비교 가능한 종목이 20개 이상인 거래일만 사용
- 각 거래일의 미래 초과수익 상위 25%를 1, 하위 25%를 0으로 라벨링
- 중간 50%는 작은 무작위 움직임의 영향을 줄이기 위해 제외
- 결과: 2,323개 거래일, 98,616건, 양성 비율 50.53%

```powershell
.venv\Scripts\python.exe scripts/ai/data/relabel_cross_sectional_outcomes.py `
  --input datasets/local-ai-github-20260822/technical.csv `
  --output datasets/local-ai-cross-sectional-20260822/technical.csv `
  --tail-fraction 0.25 --minimum-symbols 20
```

순위와 미래수익 열은 평가 전용 열로 지정되어 학습 입력에 포함되지 않는다.

## 중첩 워크포워드 결과

5개 외부 구간과 각 3개 내부 구간에서 기본, 시장 상대, 장기 추세, 횡단면 피처
묶음을 선택했다.

| 지표 | 결과 |
|---|---:|
| 정확도 | 51.02% |
| 다수 클래스 기준선 | 50.80% |
| 기준선 대비 개선 | +0.22%p |
| 균형 정확도 | 51.12% |
| ROC-AUC | 0.5120 |
| Brier score | 0.2499 |
| 최악 구간 기준선 대비 개선 | -1.10%p |

최근 두 구간에서는 횡단면 피처가 선택되어 각각 +1.12%p, +0.88%p 개선됐지만,
세 번째 구간에서 -1.10%p를 기록했다. 하이퍼파라미터와 피처 묶음 선택도 구간별로
불안정했다.

## 판정

`promotion_ready=false`다. 횡단면 타깃은 최근 구간에서 가능성을 보였지만 모든
시간 구간에서 기준선을 이기지 못했으므로 운영 기술 AI를 교체하지 않았다.

- 검증 보고서: `artifacts/local-ai-candidates/cross-sectional-20260822/technical-feature-selection-nested.json`
- 운영 모델: 변경 없음
- 다음 검증: 월별 데이터가 추가된 뒤 동일 설정으로 재실행하고 최악 구간 개선이
  양수가 되는지 확인
