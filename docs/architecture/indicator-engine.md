# Indicator Engine

The market dashboard renders MA5 and MA20 over the currently selected candle interval and places
volume on an independent lower price scale. A separate experimental snapshot loads the canonical
daily Indicator Engine output and the Pattern Engine result, showing the latest RSI, MACD
histogram, ADX, MFI, ATR, SuperTrend direction and recent detected patterns. These labels describe
calculated state only and do not create an order or investment recommendation.

`IndicatorEngine`은 외부 데이터 소스와 분리된 순수 계산 모듈이다. 입력은 정제된 OHLCV 캔들이며 출력은 시점별 지표 값이다.

지원 지표: RSI(14), MACD(12/26/9), Bollinger Band(20, 2σ), MA(5/20), ATR(14), ADX/DMI(14), MFI(14), 누적 VWAP, OBV, SuperTrend(10, 3).

Wilder 계열 지표는 최초 단순평균으로 RMA를 초기화한다. 표준 warm-up 이전 값은 `null`이며 미래 데이터로 채우지 않는다. 엔진 버전은 `technical-2026.1`, 검증 상태는 `experimental`이다.
