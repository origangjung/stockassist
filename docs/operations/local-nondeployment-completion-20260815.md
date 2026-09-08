# 배포 제외 잔여 작업 완료 기록

## KIS 실시간 검증

- KIS 승인 키 발급과 WebSocket 연결을 실제로 확인했다.
- 삼성전자와 Apple을 15초 구독했고 연결 1회 성공, 재연결 0회, 오류 0회였다.
- 토요일이라 체결 시세는 없었으며 보고서는 `artifacts/realtime-validation/`에 저장했다.
- 평일 국내장 09:10과 미국장 23:35에 각각 10분 검증하는 Windows 작업을 등록했다.
- 검증기는 수신 건수, 최대 지연, 재연결 횟수, 메모리 최고값만 기록하며 키와 원문 인증 응답은 저장하지 않는다.

## 후보 모델 자동 검증

- 매주 토요일 19:30에 네트워크가 차단된 Docker trainer에서 후보를 검증한다.
- 준비되지 않은 데이터셋은 자동 제외하고 운영 모델은 자동 교체하지 않는다.
- 모든 품질 관문을 통과한 기본 스키마 후보만 실행 가능한 JSON 모델로 생성한다.
- 활성화는 `approve_local_ai_candidate.py`에 검증된 `model_version`을 정확히 입력해야 하며,
  기존 모델은 `artifacts/local-ai-history/`에 백업한 뒤 원자적으로 교체한다.
- KIS처럼 운영 피처와 다른 지역 전용 데이터셋도 안전한 CSV 피처를 자동 인식한다.
- 재무 1,263행 후보는 AUC 0.4942, 최소 폴드 균형 정확도 0.4848로 승격을 차단했다.
- FINRA 수급 19,380행 후보는 AUC 0.4454, 최소 폴드 균형 정확도 0.4493으로 승격을 차단했다.
- KIS 수급 445행은 검증 날짜와 표본 부족으로 학습 전 단계에서 제외했다.

```powershell
.venv\Scripts\python.exe scripts\ai\training\approve_local_ai_candidate.py `
  --candidate-dir artifacts\local-ai-candidates\incremental `
  --agent financial `
  --approve-version local-financial-검증된버전
```

## 프론트와 장애 대응

- 검색 자동완성, 분석, 모의투자, 반응형 레이아웃의 기존 Playwright 시나리오를 유지한다.
- 분석 API 연결 실패 후 같은 화면에서 재시도해 복구되는 브라우저 시나리오를 추가했다.
- 프론트 단위 테스트와 TypeScript 검사를 통과했다.
- Next.js 빌드는 컴파일, 타입 검사, 28개 정적 페이지 생성을 통과했다. 마지막 standalone 복사는 실행 환경의 Windows 심볼릭 링크 권한 제한으로 완료하지 못했다.
- Playwright 재실행은 도구 승인 사용 한도로 실행하지 못했으며 다음 로컬 검증에서 우선 실행한다.

## 보안과 운영

- API 키는 `.env`에서만 읽고 명령줄, 보고서, 예약 작업 정의에 값을 넣지 않는다.
- KIS 수집 실패는 다른 데이터 수집 결과와 상태를 보존하면서 실패 코드로 알린다.
- 저장소 위생, 환경변수 계약, 운영 환경 검사, 비밀 교체, 복구, 모니터링 테스트를 통과했다.
- 실제 주문 API는 호출하지 않았다.

## 등록된 작업

- `StockPilot-LocalAI-Collection`: 매일 18:30 데이터 수집
- `StockPilot-KIS-Realtime-KR`: 평일 09:10 국내 실시간 검증
- `StockPilot-KIS-Realtime-US`: 평일 23:35 미국 실시간 검증
- `StockPilot-LocalAI-Candidate-Validation`: 토요일 19:30 후보 모델 검증
