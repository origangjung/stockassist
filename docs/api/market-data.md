# Market Data API — Phase 2 / Phase 8

모든 응답은 `success`, `request_id`, `data_as_of`, `disclaimer`, `is_investment_advice: false`를 포함한다.

| Endpoint | 설명 |
| --- | --- |
| `GET /api/v1/stocks/{symbol}` | 종목 기본 정보 |
| `GET /api/v1/stocks/{symbol}/quote` | 현재가 |
| `GET /api/v1/stocks/{symbol}/candles?limit=30` | 일봉 캔들 |
| `GET /api/v1/stocks/{symbol}/candles/processed?interval=1w` | 검증·집계된 캔들 |
| `GET /api/v1/stocks/{symbol}/orderbook` | 5단계 호가 |
| `GET /api/v1/stocks/{symbol}/trades?limit=20` | 최근 체결 |
| `GET /api/v1/stocks/{symbol}/warnings` | 투자유의 신호 |
| `GET /api/v1/stocks/{symbol}/patterns?limit=180` | 실험 차트·캔들 패턴 분석 |
| `GET /api/v1/stocks/{symbol}/financials?fiscal_year=2025` | 정규화된 재무제표 |

지원 Mock 종목: `005930`, `000660`, `035420`, `AAPL`, `MSFT`, `NVDA`, `TSLA`, `JPM`.
Mock 데이터는 계약 및 파이프라인 개발 전용이다.

웹 시장 화면의 종목 조회는 기본 정보와 현재가 endpoint를 병렬 호출한다. 조회에 성공한
종목은 동적 탭에 추가되고 차트, REST 현재가 폴링, WebSocket 및 AI 분석의 활성 symbol이
함께 전환된다. 현재가 폴링은 선택된 한 종목에만 적용한다.

`processed` endpoint는 raw count, aggregation version, quality logs를 함께 반환한다. `1d`, `1w`, `1M` interval을 지원한다.

TossProvider 사용 시 현재가의 `change`, `change_percent`, `volume`과 체결의 `side`는 공식 원본 응답에 없는 값이므로 `null`일 수 있다.
