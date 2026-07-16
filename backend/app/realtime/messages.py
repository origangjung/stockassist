from datetime import UTC, datetime

from app.providers.contracts import Quote
from app.realtime.contracts import QuoteMessage


def quote_message(quote: Quote, provider: str) -> QuoteMessage:
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
