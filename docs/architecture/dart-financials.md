# DART Financial Analysis (Phase 9)

`FinancialProvider`는 재무 데이터 출처를 서비스 계층에서 분리한다. 기본값은 재현 가능한 MockProvider이며, `FINANCIAL_PROVIDER=dart`와 `DART_API_KEY`를 설정하면 Open DART를 사용한다.

## 데이터 흐름

```text
symbol → DART corpCode ZIP → corp_code → fnlttSinglAcntAll → normalized FinancialSnapshot → financials table
```

연결재무제표(`CFS`)를 우선 조회하고 없을 때만 별도재무제표(`OFS`)를 사용한다. 매출, 영업이익, 당기순이익, 자산·부채·자본총계를 XBRL 계정 ID 우선으로 정규화한다. 원천에 없는 항목은 0으로 추정하지 않고 null로 보존한다.

## 실행 설정

```dotenv
FINANCIAL_PROVIDER=dart
DART_API_KEY=발급받은_40자리_인증키
```

Open DART 인증키는 서버 환경에만 보관한다. 재무제표는 보고서 정정으로 변경될 수 있으므로, 조회 시점(`data_as_of`)과 보고서 코드(`11011` 사업보고서 등)를 함께 저장한다.
