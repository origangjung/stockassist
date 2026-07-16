# Error envelope

모든 API 오류는 성공 응답과 동일한 request ID 및 compliance 메타데이터를 사용한다. 클라이언트가 보낸 `X-Request-ID`는 안전한 문자와 128자 제한을 통과할 때만 유지된다.

```json
{
  "success": false,
  "request_id": "request-id",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청 값이 유효하지 않습니다.",
    "data": []
  },
  "data_as_of": "2026-07-13T00:00:00+00:00",
  "disclaimer": "...",
  "is_investment_advice": false
}
```

백테스트 응답의 `persistence_status`는 DB 연결 여부를 나타낸다. `PERSISTENCE_ENABLED=true`일 때 `run_id`가 발급되고, Score API는 `score_weights`의 활성 버전을 읽는다.
