# 실시간 시세 종단 간 검증 기록: 2026-08-27

## 검증 경로

실행 중인 로컬 운영 스택에서 브라우저와 동일한 공개 경로를 사용했다.

`Nginx /ws/v1/quotes/{symbol} -> FastAPI RealtimeHub -> Toss WebSocket -> 공개 응답`

서버 설정은 `REALTIME_ENABLED=true`, `REALTIME_SOURCE=toss`였으며 상태 API는
`enabled=true`, `source=toss`, `transport=streaming`을 반환했다.

## 단일 종목

- 공개 주소 `ws://127.0.0.1:8080/ws/v1/quotes/AAPL`에 연결했다.
- 연결이 열린 뒤 `type=quote`, `symbol=AAPL`인 실제 가격 메시지를 수신했다.

## 다종목 동시 연결

아래 다섯 공개 WebSocket을 동시에 연결했고 제한 시간 안에 모두 해당 종목의 가격을 받았다.

| 요청 종목 | 응답 종목 | 결과 |
| --- | --- | --- |
| `AAPL` | `AAPL` | 통과 |
| `MSFT` | `MSFT` | 통과 |
| `NVDA` | `NVDA` | 통과 |
| `TSLA` | `TSLA` | 통과 |
| `SPY` | `SPY` | 통과 |

검증 로그에는 자격 증명이나 공급자의 원문 인증 응답을 남기지 않았다. 표시 가격은 시간에 따라 바뀌므로
운영 문서에는 저장하지 않는다.

## 판단

현재 프론트가 사용하는 Toss 실시간 경로는 단일·다종목 모두 정상이다. KIS는 대체 공급자로 별도 검증됐으며,
공급자 전환은 `.env`의 `REALTIME_SOURCE`를 명시적으로 변경하고 서비스를 재시작할 때만 수행한다.
