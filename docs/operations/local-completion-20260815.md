# 배포 제외 로컬 완성 검증 기록

## 완료한 작업

- 현재 변경 파일과 Git 제외 경계를 점검했다. `.env`, 데이터셋, 모델 artifact, Playwright 결과,
  자동 수집 로그는 Git 대상에서 제외되며 커밋과 푸시는 수행하지 않았다.
- Windows 작업 스케줄러에 `StockPilot-LocalAI-Collection`을 현재 사용자 범위로 등록했다.
  매일 18:30 실행하며 Docker가 늦게 준비되면 `StartWhenAvailable`로 실행한다.
- `scripts/operations/run_local_ai_collection.ps1 -DryRun`으로 Docker collector 연결을 확인했다.
- 준비된 데이터셋만 중첩 시간 검증하는 `scripts/ai/training/validate_local_ai_candidates.py`를 추가했다.
  결과는 후보 artifact에만 저장하며 운영 모델을 자동 승격하지 않는다.
- ETF 기술·위험·종합 후보를 5개 외부 구간과 3개 내부 구간으로 검증했다.
- SEC, FRED, FINRA, NewsAPI, Toss를 AAPL 단일 종목의 제한된 요청으로 확인했다.
- Nginx가 `/api/paper/`를 FastAPI에 직접 전달하던 문제를 수정해 Next.js 보안 BFF를
  반드시 통과하게 했다.
- 360px 화면에서 결과 카드의 최소 콘텐츠 폭이 본문을 493px로 늘리던 문제를 수정했다.
  강화된 E2E는 `documentElement`와 `body`의 실제 내부 폭을 모두 검사한다.

## ETF 후보 결과

| 모델 | 검증 행 | 균형정확도 | ROC AUC | 기준선 개선 | 판정 |
|---|---:|---:|---:|---:|---|
| ETF 기술 | 34,950 | 50.07% | 0.4861 | -2.53%p | 기각 |
| ETF 위험 | 34,950 | 65.68% | 0.7267 | -7.12%p | 기각 |
| ETF 종합 | 6,189 | 48.64% | 0.5022 | -5.12%p | 기각 |

ETF 위험 후보는 구분력은 있었지만 확률 보정 오차 22.03%와 다수 클래스 기준선 조건을
통과하지 못했다. 세 후보 모두 운영 모델로 승격하지 않았다.

## 검증 결과

- 백엔드 전체 테스트: 410개 통과
- Ruff와 프론트 TypeScript 검사 통과
- 프론트 단위 테스트: 18개 통과
- Windows 검증 모드 프로덕션 빌드와 Docker/Linux standalone 프로덕션 빌드 통과
- Playwright: 2560px 데스크톱, 태블릿, 390px, 360px에서 실행된 10개 통과,
  화면별 조건상 6개 제외
- 2560px 화면에서 전체 폭 사용, 차트·분석 좌우 정렬과 분석 패널 내부 가로 넘침 1px 이하 확인
- Nginx 설정 검사와 모의계좌 BFF 조회 통과
- 모의계좌 초기 USD 10,000과 `is_real_order=false` 확인
- 자동 수집 Docker dry-run 통과
- 저장소 위생, 문서 링크·Alembic head, 환경변수 계약 검사 통과
- pnpm 프로덕션 의존성과 Python 가상환경 공개 취약점 검사 결과 알려진 취약점 없음
- PostgreSQL, Redis, API, 웹, Nginx health check와 `/health/ready` HTTP 200 확인

## 외부 조건 때문에 남은 작업

- 뉴스 데이터가 최소 5거래일 결과를 갖도록 매일 누적하고 수백 개 검증 시점 이후 재검증한다.
- KIS 키가 준비되면 국내·미국 WebSocket 구독, 해제, 재연결을 실제 장 시간에 확인한다.
- Toss 장시간 soak와 자연 발생 401·403·429·5xx는 실제 장 운영 시간에만 추가 확인한다.
- KRX, Nasdaq, NYSE 기업행동 효력일과 기관 수급 장기 데이터는 계약 및 재배포 조건 확인 후
  실제 공급자를 구현한다.
- HTTPS, 도메인, Secret Manager, 운영 경보와 오프사이트 백업은 배포를 결정할 때 진행한다.

현재 로컬 서비스는 `http://localhost:3000`, 통합 Nginx 경로는
`http://localhost:8080`에서 실행 중이다.
