"""schemas 파일은 HTTP 요청·응답과 접근 제어 기능을 담당한다."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QuoteResponse(BaseModel):
    """API 응답으로 전달하는 필드 계약을 정의합니다."""

    symbol: str
    name: str | None
    price: Decimal
    change: Decimal | None
    change_percent: Decimal | None
    volume: int | None
    as_of: datetime | None
    provider: str


class CandleResponse(BaseModel):
    """API 응답으로 전달하는 필드 계약을 정의합니다."""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class OrderbookLevelResponse(BaseModel):
    """API 응답으로 전달하는 필드 계약을 정의합니다."""

    price: Decimal
    quantity: int


class OrderbookResponse(BaseModel):
    """API 응답으로 전달하는 필드 계약을 정의합니다."""

    symbol: str
    asks: list[OrderbookLevelResponse]
    bids: list[OrderbookLevelResponse]
    provider: str


class ApiEnvelope(BaseModel):
    """`ApiEnvelope` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    success: bool = True
    request_id: str
    data: dict
    data_as_of: datetime
    disclaimer: str
    is_investment_advice: bool = False


class CandleQuery(BaseModel):
    """`CandleQuery` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    limit: int = Field(default=30, ge=1, le=365)


class BacktestRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

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
    corporate_action_mode: Literal["none", "forward_point_in_time"] = "none"


class BacktestValidationRequest(BacktestRequest):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

    n_splits: int = Field(default=3, ge=2, le=6)
    warmup_candles: int = Field(default=60, ge=21, le=120)


class BacktestComparisonRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

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
    corporate_action_mode: Literal["none", "forward_point_in_time"] = "none"


class BacktestStrategyComparisonRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

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
    corporate_action_mode: Literal["none", "forward_point_in_time"] = "none"


class WatchlistCreateRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")


class PaperOrderRequest(BaseModel):
    """모의 시장가 주문 입력값이며 실제 주문 옵션은 의도적으로 제공하지 않는다."""

    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0, le=1_000_000, max_digits=24, decimal_places=6)
    idempotency_key: str = Field(pattern=r"^[0-9a-f-]{36}$")


class FundAllocationProposalRequest(BaseModel):
    """실제 주문 없이 모의 계좌의 목표 비중과 리밸런싱 후보를 계산하는 입력값이다."""

    symbols: list[str] = Field(min_length=2, max_length=12)
    objective: Literal["min_volatility", "max_sharpe"] = "min_volatility"
    invest_ratio: Decimal = Field(default=Decimal("0.90"), gt=0, le=Decimal("0.95"))
    min_asset_weight: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("0.40"))
    max_asset_weight: Decimal = Field(default=Decimal("0.40"), gt=0, le=Decimal("0.40"))
    lookback_days: int = Field(default=180, ge=60, le=365)


class PriceAlertCreateRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")
    condition: Literal["above", "below"]
    target_price: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


class CorporateActionApprovalRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

    start: date
    end: date
    group_hint: str = Field(pattern=r"^candidate:[0-9a-f]{20}$")
    receipt_no: str = Field(pattern=r"^[0-9]{14}$")
    effective_at: datetime
    exchange_evidence_url: str = Field(min_length=12, max_length=2048)
    confirmation: Literal["CONFIRM_CORPORATE_ACTION"]


class TossOrderCreateRequest(BaseModel):
    """토스 실제 주문 생성값과 사용자의 명시적 확인 문구다."""

    symbol: str = Field(pattern=r"^[0-9A-Z.-]{1,16}$")
    side: Literal["BUY", "SELL"]
    order_type: Literal["LIMIT", "MARKET"] = Field(alias="orderType")
    time_in_force: Literal["DAY", "CLS"] = Field(default="DAY", alias="timeInForce")
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=30, decimal_places=6)
    order_amount: Decimal | None = Field(
        default=None, alias="orderAmount", gt=0, max_digits=30, decimal_places=6
    )
    price: Decimal | None = Field(default=None, gt=0, max_digits=30, decimal_places=6)
    client_order_id: str = Field(alias="clientOrderId", pattern=r"^[a-zA-Z0-9_-]{8,36}$")
    confirm_high_value_order: bool = Field(default=False, alias="confirmHighValueOrder")
    confirmation: Literal["실제 주문 실행"]

    @model_validator(mode="after")
    def validate_order_shape(self) -> "TossOrderCreateRequest":
        """`validate_order_shape`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

        if (self.quantity is None) == (self.order_amount is None):
            raise ValueError("quantity와 orderAmount 중 하나만 입력해야 합니다")
        if self.order_type == "LIMIT" and self.price is None:
            raise ValueError("지정가 주문에는 price가 필요합니다")
        if self.order_type == "MARKET" and self.price is not None:
            raise ValueError("시장가 주문에는 price를 입력할 수 없습니다")
        return self


class TossOrderModifyRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

    order_type: Literal["LIMIT", "MARKET"] = Field(alias="orderType")
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=30, decimal_places=6)
    price: Decimal | None = Field(default=None, gt=0, max_digits=30, decimal_places=6)
    confirm_high_value_order: bool = Field(default=False, alias="confirmHighValueOrder")
    confirmation: Literal["실제 주문 실행"]


class TossMutationConfirmation(BaseModel):
    """`TossMutationConfirmation` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    confirmation: Literal["실제 주문 실행"]


class TossConditionRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

    order_side: Literal["BUY", "SELL"] = Field(alias="orderSide")
    trigger_price: Decimal = Field(alias="triggerPrice", gt=0, max_digits=30, decimal_places=6)
    order_price: Decimal | None = Field(
        default=None, alias="orderPrice", gt=0, max_digits=30, decimal_places=6
    )


class TossConditionalOrderRequest(BaseModel):
    """API 요청 본문의 필드와 검증 규칙을 정의합니다."""

    symbol: str | None = Field(default=None, pattern=r"^[0-9A-Z.-]{1,16}$")
    type: Literal["SINGLE", "OCO", "OTO"]
    quantity: Decimal = Field(gt=0, max_digits=30, decimal_places=6)
    order_type: Literal["LIMIT", "MARKET"] = Field(alias="orderType")
    expire_date: date = Field(alias="expireDate")
    first: TossConditionRequest
    second: TossConditionRequest | None = None
    client_order_id: str | None = Field(
        default=None, alias="clientOrderId", pattern=r"^[a-zA-Z0-9_-]{8,36}$"
    )
    confirm_high_value_order: bool = Field(default=False, alias="confirmHighValueOrder")
    confirmation: Literal["실제 주문 실행"]

    @model_validator(mode="after")
    def validate_conditions(self) -> "TossConditionalOrderRequest":
        """`validate_conditions`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

        if self.type == "SINGLE" and self.second is not None:
            raise ValueError("SINGLE 조건주문에는 second를 입력할 수 없습니다")
        if self.type in {"OCO", "OTO"} and self.second is None:
            raise ValueError("OCO/OTO 조건주문에는 second가 필요합니다")
        if self.type in {"OCO", "OTO"} and self.order_type != "LIMIT":
            raise ValueError("OCO/OTO 조건주문은 지정가만 지원합니다")
        return self
