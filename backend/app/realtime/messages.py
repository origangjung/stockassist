"""messages 파일은 실시간 시세 연결 기능을 담당한다."""

from datetime import UTC, datetime

from app.providers.contracts import Quote
from app.realtime.contracts import QuoteMessage


def quote_message(quote: Quote, provider: str) -> QuoteMessage:
    """`quote_message`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    as_of = quote.as_of or datetime.now(UTC)
    return {
        "type": "quote",
        "symbol": quote.symbol,
        "name": quote.name,
        "price": str(quote.price),
        "change": str(quote.change) if quote.change is not None else None,
        "change_percent": (str(quote.change_percent) if quote.change_percent is not None else None),
        "volume": quote.volume,
        "currency": quote.currency,
        "data_as_of": as_of.isoformat(),
        "provider": provider,
        "is_investment_advice": False,
    }
