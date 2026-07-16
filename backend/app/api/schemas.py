from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class QuoteResponse(BaseModel):
    symbol: str
    name: str | None
    price: Decimal
    change: Decimal | None
    change_percent: Decimal | None
    volume: int | None
    as_of: datetime | None
    provider: str


class CandleResponse(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class OrderbookLevelResponse(BaseModel):
    price: Decimal
    quantity: int


class OrderbookResponse(BaseModel):
    symbol: str
    asks: list[OrderbookLevelResponse]
    bids: list[OrderbookLevelResponse]
    provider: str


class ApiEnvelope(BaseModel):
    success: bool = True
    request_id: str
    data: dict
    data_as_of: datetime
    disclaimer: str
    is_investment_advice: bool = False


class CandleQuery(BaseModel):
    limit: int = Field(default=30, ge=1, le=365)


class BacktestRequest(BaseModel):
    symbol: str = Field(pattern=r"^[0-9A-Z]{1,16}$")
    strategy: str = Field(
        default="ma_cross",
        pattern=r"^(ma_cross|buy_and_hold|pattern_reference)$",
    )
    engine: Literal["vectorized", "event_driven"] = "vectorized"
    limit: int = Field(default=240, ge=30, le=365)
    fast_period: int = Field(default=5, ge=2, le=60)
    slow_period: int = Field(default=20, ge=3, le=200)
    initial_capital: float = Field(default=10_000_000, gt=0)
    commission_rate: float = Field(default=0.00015, ge=0, lt=1)
    tax_rate: float = Field(default=0.0018, ge=0, lt=1)
    slippage_rate: float = Field(default=0.0005, ge=0, lt=1)
    max_volume_participation: float = Field(default=1.0, gt=0, le=1)


class BacktestValidationRequest(BacktestRequest):
    n_splits: int = Field(default=3, ge=2, le=6)
    warmup_candles: int = Field(default=60, ge=21, le=120)


class BacktestComparisonRequest(BaseModel):
    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")
    strategy: str = Field(
        default="ma_cross",
        pattern=r"^(ma_cross|buy_and_hold|pattern_reference)$",
    )
    limit: int = Field(default=240, ge=30, le=365)
    fast_period: int = Field(default=5, ge=2, le=60)
    slow_period: int = Field(default=20, ge=3, le=200)
    initial_capital: float = Field(default=10_000_000, gt=0)
    commission_rate: float = Field(default=0.00015, ge=0, lt=1)
    tax_rate: float = Field(default=0.0018, ge=0, lt=1)
    slippage_rate: float = Field(default=0.0005, ge=0, lt=1)
    max_volume_participation: float = Field(default=0.1, gt=0, le=1)


class BacktestStrategyComparisonRequest(BaseModel):
    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")
    engine: Literal["vectorized", "event_driven"] = "event_driven"
    limit: int = Field(default=240, ge=30, le=365)
    fast_period: int = Field(default=5, ge=2, le=60)
    slow_period: int = Field(default=20, ge=3, le=200)
    initial_capital: float = Field(default=10_000_000, gt=0)
    commission_rate: float = Field(default=0.00015, ge=0, lt=1)
    tax_rate: float = Field(default=0.0018, ge=0, lt=1)
    slippage_rate: float = Field(default=0.0005, ge=0, lt=1)
    max_volume_participation: float = Field(default=0.1, gt=0, le=1)


class WatchlistCreateRequest(BaseModel):
    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")


class PriceAlertCreateRequest(BaseModel):
    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")
    condition: Literal["above", "below"]
    target_price: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
