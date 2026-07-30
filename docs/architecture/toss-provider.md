# TossProvider (Phase 8)

## 범위

`STOCK_PROVIDER=toss`로 설정하면 Broker Adapter가 TossProvider를 사용한다. 현재 구현 범위는 다음과 같다.

- OAuth 2.0 Client Credentials 토큰 발급과 캐시
- 현재가, 1일봉, 호가, 체결, 종목 정보, 투자유의 조회
- 1일봉은 Toss 요청의 `adjusted=true` 결과이므로 `price_basis=provider_adjusted`로 표시한다.
  StockPilot 기업행동 엔진은 이 값을 다시 보정하지 않아 이중 보정을 차단한다.
- 이 계약은 `toss-adjusted-v1` 규칙으로 선언된다. Broker Adapter는 모든 캔들 배치가 선언과
  일치하는지 소비자 전달 전에 검사하며, 적재 시 규칙 버전도 함께 보존한다.
- API 그룹별 토큰 버킷과 응답 헤더 기반 동적 한도 반영
- 429 `Retry-After` + 지수 백오프 + jitter
- `expired-token` 1회 자동 재발급
- Toss 오류의 `code`, `requestId`, `data`를 내부 Provider 오류로 변환
- 성공·실패 호출의 외부 `requestId`와 내부 요청 ID를 `provider_audit_logs`에 보존한다.
  감사 이력에는 토큰, 계좌번호, 쿼리/본문, 응답 본문을 저장하지 않으며 관리자 전용
  `GET /api/v1/admin/provider-audits`에서 조회한다.
- `PROVIDER_AUDIT_CLEANUP_ENABLED=true`이면 기본 90일 보존 기간을 지난 감사 행만 매일
  정리한다. 관리자 수동 정리 API도 동일한 외부화된 cutoff만 사용하며 감사 저장·정리
  실패는 시세 호출 결과를 변경하지 않는다.

주문과 조건주문은 규제 검토 전까지 애플리케이션 계약을 구현하거나 활성화하지 않는다.
반면 본인 계좌 동기화는 `ACCOUNT_SYNC_ENABLED=true`일 때만 관리자 경계에서 읽기 전용으로
제공한다. 마스킹된 계좌·보유 종목을 동기화하고 포트폴리오 분석에 사용하지만 주문, 잔고
변경, 타인 계좌 접근은 수행하지 않는다.

## 설정

```dotenv
STOCK_PROVIDER=toss
TOSS_BASE_URL=https://openapi.tossinvest.com
TOSS_CLIENT_ID=...
TOSS_CLIENT_SECRET=...
REDIS_URL=redis://redis:6379/0
```

자격증명은 서버 환경에만 둔다. Toss 허용 IP에 배포 환경의 고정 Egress IP가 등록되어 있어야 한다.

## 토큰과 장애 처리

액세스 토큰은 Redis TTL과 프로세스 메모리에 계층형으로 저장한다. Redis가 일시적으로 응답하지 않으면 메모리 캐시로 계속 동작한다. Toss는 한 client당 유효한 액세스 토큰을 하나만 허용하므로 운영 환경에서는 모든 API 워커가 같은 Redis를 사용해야 한다.

현재가 공식 응답에는 등락, 등락률, 거래량이 없고 체결 응답에는 매수·매도 방향이 없다. 데이터 오염을 막기 위해 해당 필드는 추정하지 않고 `null`로 반환한다.

## 검증

실제 자격증명이나 주문 없이 `httpx2.MockTransport`로 OAuth 캐시, 만료 재발급, 429 재시도, 오류 매핑, 페이지네이션, warnings의 계약을 테스트한다. 실계정 smoke test는 허용 IP와 별도 테스트 자격증명이 준비된 환경에서만 수행한다.
