import logging
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.sanitization import public_provider_error_message
from app.providers.errors import ProviderError
from app.realtime.contracts import RealtimeHub
from app.realtime.hub import (
    InvalidRealtimeSymbolError,
    RealtimeCapacityError,
    RealtimeDisabledError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _close_with_error(
    websocket: WebSocket,
    *,
    code: int,
    error_code: str,
    message: str,
) -> None:
    if websocket.client_state == WebSocketState.CONNECTED:
        with suppress(Exception):
            await websocket.send_json(
                {
                    "type": "error",
                    "error": {"code": error_code, "message": message},
                    "is_investment_advice": False,
                }
            )
            await websocket.close(code=code)


@router.websocket("/ws/v1/quotes/{symbol}")
async def quote_stream(websocket: WebSocket, symbol: str) -> None:
    realtime_quote_hub: RealtimeHub = websocket.scope["app"].state.realtime_quote_hub
    origin = websocket.headers.get("origin")
    allowed_origins = getattr(websocket.scope["app"].state, "allowed_origins", frozenset())
    if origin and allowed_origins and origin.rstrip("/") not in allowed_origins:
        await websocket.close(code=4403, reason="Origin is not allowed")
        return
    await websocket.accept()
    try:
        async for message in realtime_quote_hub.stream(symbol):
            await websocket.send_json(message)
    except WebSocketDisconnect:
        return
    except RealtimeDisabledError as exc:
        await _close_with_error(
            websocket,
            code=4403,
            error_code="REALTIME_DISABLED",
            message=str(exc),
        )
    except InvalidRealtimeSymbolError as exc:
        await _close_with_error(
            websocket,
            code=4400,
            error_code="INVALID_SYMBOL",
            message=str(exc),
        )
    except RealtimeCapacityError as exc:
        await _close_with_error(
            websocket,
            code=1013,
            error_code="REALTIME_CAPACITY_REACHED",
            message=str(exc),
        )
    except ProviderError as exc:
        await _close_with_error(
            websocket,
            code=4404 if exc.status_code == 404 else 1013,
            error_code=exc.code,
            message=public_provider_error_message(exc),
        )
    except Exception:
        logger.exception("Unhandled realtime WebSocket failure symbol=%s", symbol)
        if websocket.client_state == WebSocketState.CONNECTED:
            with suppress(Exception):
                await websocket.close(code=1011)
