# 관심 종목과 가격 참고 알림

이 기능은 관리자가 국내·미국 종목을 관심 목록에 저장하고, 현재가가 지정 가격에 도달했는지 확인하는 운영 기능이다. 매수·매도 주문과는 연결하지 않는다.

## 안전 경계

- 모든 엔드포인트는 `X-Admin-Key`가 필요한 `/api/v1/admin` 범위에 있다.
- 브라우저는 관리자 키를 받지 않는다. Next.js 서버 프록시가 백엔드 요청에만 키를 추가한다.
- 알림 결과에는 `execution_enabled=false`, `is_investment_advice=false`가 포함된다.
- 조건 도달 시 상태를 `active`에서 `triggered`로 한 번만 변경하며 주문, 조건주문, 계좌 API를 호출하지 않는다.

## 평가 방식

- `above`: 현재가가 목표 가격 이상이면 도달 처리한다.
- `below`: 현재가가 목표 가격 이하이면 도달 처리한다.
- 한 평가 주기에 같은 종목 알림이 여러 개 있으면 시세는 한 번만 조회한다.
- 특정 종목 조회가 실패해도 다른 종목은 계속 평가하며 실패 종목과 예외 종류만 결과와 로그에 남긴다.

## 설정

DB 마이그레이션을 먼저 적용한다.

```powershell
alembic upgrade head
```

수동 평가는 관리자 화면에서 항상 실행할 수 있다. 자동 평가를 켜려면 다음 환경 변수를 설정한다.

```dotenv
PERSISTENCE_ENABLED=true
REFERENCE_ALERTS_ENABLED=true
REFERENCE_ALERT_INTERVAL_SECONDS=30
```

`REFERENCE_ALERTS_ENABLED=true`인데 DB 저장이 꺼져 있으면 애플리케이션은 설정 오류로 시작을 거부한다.

## API

- `GET /api/v1/admin/watchlist`
- `POST /api/v1/admin/watchlist`
- `DELETE /api/v1/admin/watchlist/{symbol}`
- `GET /api/v1/admin/alerts`
- `POST /api/v1/admin/alerts`
- `POST /api/v1/admin/alerts/evaluate`
- `DELETE /api/v1/admin/alerts/{alert_id}`

관리 화면은 `/admin`에서 제공한다. 사용자별 관심 종목과 외부 알림 채널은 JWT/RBAC 및 사용자 도메인을 추가한 뒤 확장한다.
