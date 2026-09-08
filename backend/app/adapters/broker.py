"""broker 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass
from threading import Lock
from time import monotonic

from app.providers.contracts import Candle, CandlePriceBasisPolicy, Capability, StockProvider
from app.providers.errors import ProviderValidationError


class CapabilityUnavailableError(LookupError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


@dataclass(frozen=True)
class ValidatedCandleBatch:
    """한 번에 처리할 데이터 묶음과 처리 상태를 전달하는 값 객체입니다."""

    candles: list[Candle]
    provider: StockProvider
    policy: CandlePriceBasisPolicy


class BrokerAdapter:
    """Selects an active provider without exposing provider choice to services."""

    def __init__(
        self, providers: list[StockProvider], *, candle_cache_ttl_seconds: float = 15.0
    ):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._providers = providers
        self._candle_cache_ttl_seconds = max(candle_cache_ttl_seconds, 0.0)
        self._candle_cache: dict[
            tuple[int, str, int], tuple[float, tuple[Candle, ...], CandlePriceBasisPolicy]
        ] = {}
        self._candle_cache_lock = Lock()

    def provider_for(self, capability: Capability) -> StockProvider:
        """`provider_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다."""

        for provider in self._providers:
            if provider.capabilities.supports(capability):
                return provider
        raise CapabilityUnavailableError(f"활성 Provider에 {capability.value} 기능이 없습니다.")

    def candles(self, symbol: str, limit: int) -> ValidatedCandleBatch:
        """`candles`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다."""

        provider = self.provider_for(Capability.CANDLES)
        normalized_symbol = symbol.strip().upper()
        cache_key = (id(provider), normalized_symbol, limit)
        if self._candle_cache_ttl_seconds > 0:
            with self._candle_cache_lock:
                cached = self._candle_cache.get(cache_key)
            if cached is not None and cached[0] > monotonic():
                return ValidatedCandleBatch(list(cached[1]), provider, cached[2])
        candles = provider.get_candles(normalized_symbol, limit)
        policy = provider.candle_price_basis_policy
        observed = sorted({candle.price_basis for candle in candles})
        if observed and observed != [policy.expected_basis]:
            raise ProviderValidationError(
                "Provider candle price basis does not match its declared contract",
                code="candle-price-basis-contract-mismatch",
                data={
                    "provider": provider.name,
                    "expected": policy.expected_basis,
                    "observed": observed,
                    "rule_version": policy.rule_version,
                },
            )
        if self._candle_cache_ttl_seconds > 0:
            with self._candle_cache_lock:
                self._candle_cache[cache_key] = (
                    monotonic() + self._candle_cache_ttl_seconds,
                    tuple(candles),
                    policy,
                )
        return ValidatedCandleBatch(list(candles), provider, policy)
