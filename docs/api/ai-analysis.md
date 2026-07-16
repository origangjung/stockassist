# AI analysis result API

`GET /api/v1/stocks/{symbol}/ai-report?horizon_days=5&limit=180`

The endpoint coordinates calculated Score Engine, prediction, warning, investor-flow, and
support/resistance facts. The report generator explains those facts but does not calculate or
select the reference signal.

## Reference signals

| Value | UI label | Meaning |
| --- | --- | --- |
| `positive_watch` | 매수 참고 신호 | Positive calculated consensus for monitoring |
| `neutral_watch` | 관망 | Mixed or weak calculated consensus |
| `defensive_watch` | 매도 참고 신호 | Defensive calculated consensus for monitoring |
| `risk_aware` | 위험 우선 관망 | An active provider warning overrides direction |
| `data_insufficient` | 데이터 부족 | Score or prediction output is unavailable |

The experimental consensus normalizes the overall score and rise probability, then combines
them with weights of 55% and 45%. A value at or above `0.12` becomes `positive_watch`, a value
at or below `-0.12` becomes `defensive_watch`, and values in between remain neutral. Provider
warning data always takes priority.

Every response includes the raw `overall_score`, `rise_probability`, `score_coverage`,
`signal_strength`, and `signal_basis` so the displayed label can be audited. Low axis coverage
is shown to the user and all signals remain marked `experimental` until quantitative backtest
validation is complete.

The response always includes `data_as_of`, `model_version`, `disclaimer`, and
`is_investment_advice: false`. It is decision-support information, not a trading instruction.
