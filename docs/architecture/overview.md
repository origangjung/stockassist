# StockPilot AI Architecture

```text
Next.js client → FastAPI router → Application service → Broker adapter
                                                    ↓
                              Provider capability routing (Mock → Toss/KIS)
                                                    ↓
                                              External APIs
```

현재 구현은 Mock, Toss REST, KIS 수급·WebSocket Provider를 capability에 따라 선택한다. 서비스는 provider 이름이나 구현에 의존하지 않고, `BrokerAdapter`가 요청 capability에 맞는 provider를 선택한다.

모든 시장 데이터 API에는 request ID와 `is_investment_advice: false`가 포함된다. AI 리포트는 계산된 Score·예측·위험 데이터를 설명하며 Compliance Validator를 통과한 뒤에만 저장·반환된다.
