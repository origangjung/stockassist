# 자금운용 제안 계층

## 목적

이 계층은 여러 종목의 목표 비중과 모의 리밸런싱 후보를 계산한다. 실제 계좌 주문은 실행하지
않으며 기존 모의투자 원장도 자동으로 변경하지 않는다. 사용자가 결과를 검토한 뒤 모의 주문을
별도로 입력해야 한다.

## 선택한 오픈소스

- `PyPortfolioOpt 1.6.x` (MIT): 기대수익, 공분산, 최소변동성, 최대 샤프 최적화에 사용한다.
- QuantConnect LEAN의 `Alpha -> Portfolio Construction -> Risk -> Execution` 분리 방식은 경계
  설계에 참고했다. C# 기반 전체 엔진은 현재 Python 서비스에 비해 범위가 지나치게 커서 포함하지
  않았다.
- Riskfolio-Lib과 Microsoft Qlib은 연구 기능이 넓지만 의존성과 운영 범위가 커서 첫 단계에서는
  포함하지 않았다.

## 처리 흐름

1. 동일 통화의 2~12개 종목과 60~365개 가격 관측치를 받는다.
2. PyPortfolioOpt가 최소변동성 또는 최대 샤프 목적의 투자자산 내부 비중을 계산한다.
3. 중앙 위험정책이 투자비중 95%, 종목당 40% 상한을 강제한다.
4. 현재 모의 계좌 평가액과 목표 평가액의 차이를 매수·매도 후보로 변환한다.
5. API는 `execution_enabled=false`와 함께 제안만 반환한다.

## 설치와 실행

```powershell
uv pip install --python .venv\Scripts\python.exe -e ".[portfolio,dev]"
.venv\Scripts\pytest.exe backend/tests/test_fund_management.py
```

`POST /api/v1/paper-portfolios/{account_id}/allocation-proposals`에 아래처럼 요청한다.

```json
{
  "symbols": ["AAPL", "MSFT", "NVDA"],
  "objective": "min_volatility",
  "invest_ratio": "0.90",
  "max_asset_weight": "0.40",
  "lookback_days": 180
}
```

## 안전 경계

- 실계좌 접근, 주문 생성, 자동 체결 기능은 없다.
- 서로 다른 통화는 환율과 환전 비용을 숨기지 않기 위해 한 제안에서 섞지 않는다.
- 수정주가 여부가 검증되지 않은 데이터는 경고한다.
- 과거 데이터 최적화 결과는 미래 성과나 원금 보전을 보장하지 않는다.
