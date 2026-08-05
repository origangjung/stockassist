# StockPilot AI — 남은 작업 정리

> 확인일: 2026-08-05
> 기준 설계: StockPilot AI Master Project Blueprint v2.1
> 데스크톱 인계 상세: [desktop.md](desktop.md)

## 결론

현재 계획된 **노트북 가능 범위의 구현 작업은 완료 상태**입니다.

완료한 노트북 범위에는 프론트 UI/UX, 종목 검색·유사 종목 자동완성, 관심 종목·최근 검색,
Mock API 통합 확인, 접근성·보안 보완, 문서화, 프론트 단위 테스트와 타입 검사가 포함됩니다.

다만 실제 브라우저에서의 최종 사용성 확인과 사용자 피드백에 따른 작은 수정은 노트북에서도
계속 할 수 있습니다. 이는 새 기능 개발이 아니라 최종 QA 성격의 작업입니다.

## 노트북에서 남은 가벼운 작업

| 우선순위 | 작업 | 완료 조건 |
| --- | --- | --- |
| 높음 | 실제 Chrome/Edge에서 검색 화면 수동 확인 | 데스크톱·모바일 폭에서 자동완성 드롭다운, 검색 버튼, 가로 스크롤, 텍스트 잘림이 없음 |
| 높음 | 키보드 흐름 확인 | `Ctrl/Cmd + K`, `↑/↓`, `Enter`, `Esc`와 결과 포커스 이동이 정상 동작 |
| 중간 | 사용자 피드백 기반 미세 수정 | 색상·간격·문구·애니메이션을 실제 사용 의견에 맞춰 조정 |
| 중간 | Mock 환경 회귀 확인 | 국내 `005930`, 미국 `AAPL` 검색과 차트·지표·AI 리포트 경로가 정상 |
| 낮음 | 새 요청에 따른 작은 기능 추가 | 기존 Provider·Compliance 경계를 깨지 않는 범위에서만 구현 |

위 항목은 무거운 설치나 Docker 재빌드 없이 수행 가능하다. 현재 사용자 피드백이 없다면,
노트북에서 선행해야 할 필수 구현 작업은 없다.

## 데스크톱에서 남은 무거운 작업

### 1. UI 실제 브라우저 QA

- 360px, 390px, 768px, 1440px 화면 폭에서 최종 확인
- 종목 자동완성, 최근 검색, 관심 종목, 결과 공유 주소 확인
- 스크린리더·reduced-motion·키보드 흐름 확인

### 2. 인프라 통합 검증

- Docker Compose 전체 기동 및 이미지 재빌드
- PostgreSQL Alembic `head → base → head` 왕복
- PostgreSQL 백업과 격리 복구 리허설
- Redis 재시작·Pub/Sub·분산 Rate Limit·WebSocket 복구 시험

### 3. 실제 증권사 Provider 검증

- Toss 허용 IP, 토큰 재발급, 401/403/429/5xx, `Retry-After` 확인
- 장 운영 시간의 Toss 폴링 soak test
- KIS 국내·미국 WebSocket 구독·해제·재연결·REST fallback 확인
- 실제 자격증명·계좌번호·응답 원문을 로그나 fixture에 보관하지 않음

### 4. 데이터·모델 신뢰도 검증

- 상장폐지 종목을 포함한 장기 백테스트 유니버스
- 수수료·세금·슬리피지·기업행동 기준시점 보정 검증
- 여러 시장 국면의 Walk-Forward 비교
- XGBoost artifact 생성, checksum 검증, 활성화·롤백 리허설

### 5. 배포와 운영 준비

- HTTPS, 고정 Egress IP, Secret Manager, 모니터링·경보 구성
- KRX 시세 재배포 계약과 데이터 보존·개인정보 정책 검토
- KRX·Nasdaq·NYSE 기업행동 실제 Provider 계약 및 명세 확보

## 보류 항목

- Toss SINGLE/OCO/OTO 조건주문과 자동 손절·익절
- 타인 계좌 거래 또는 투자 판단을 대신하는 기능
- 투자일임업·자동매매 규제 검토 전 주문 실행
- 근거가 없는 캔들 `price_basis`의 일괄 재분류

## 작업 원칙

1. `.env`, API 키, client secret, 계좌번호는 Git·로그·문서·테스트 fixture에 넣지 않는다.
2. 자동 commit/push는 하지 않고, 사용자가 요청한 시점에만 변경을 검토해 올린다.
3. Docker 재빌드·의존성 재설치·대형 ML 설치 전에는 데스크톱 디스크 여유 공간을 확인한다.
4. AI 결과는 계속 참고 정보이며 `is_investment_advice=false` 원칙을 유지한다.

## 다음 권장 순서

1. 데스크톱에서 실제 브라우저 UI/UX QA
2. Docker·PostgreSQL·Redis 통합 검증
3. Toss·KIS 실데이터 장시간 검증
4. 장기 백테스트·ML artifact 검증
5. 배포 전 보안·운영 점검
