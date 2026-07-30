from dataclasses import replace

import pytest

from app.adapters.broker import BrokerAdapter
from app.providers.contracts import CandlePriceBasisPolicy
from app.providers.errors import ProviderValidationError
from app.providers.mock import MockProvider
from app.providers.toss import TossProvider


class _MismatchedMockProvider(MockProvider):
    name = "mismatched"

    def get_candles(self, symbol: str, limit: int = 30):
        return [
            replace(candle, price_basis="provider_adjusted")
            for candle in super().get_candles(symbol, limit)
        ]


def test_builtin_providers_declare_versioned_price_basis_policies():
    mock = MockProvider.candle_price_basis_policy
    toss = TossProvider.candle_price_basis_policy

    assert (mock.expected_basis, mock.verification_status, mock.rule_version) == (
        "unadjusted",
        "synthetic",
        "mock-candles-v1",
    )
    assert (toss.expected_basis, toss.verification_status, toss.rule_version) == (
        "provider_adjusted",
        "verified",
        "toss-adjusted-v1",
    )


def test_unverified_provider_cannot_claim_a_known_price_basis():
    with pytest.raises(ValueError, match="must use the unknown"):
        CandlePriceBasisPolicy(
            expected_basis="unadjusted",
            verification_status="unverified",
            rule_version="unsafe-v1",
            evidence="Unverified claim",
        )


def test_broker_rejects_provider_output_that_breaks_declared_policy():
    with pytest.raises(ProviderValidationError) as captured:
        BrokerAdapter([_MismatchedMockProvider()]).candles("005930", 3)

    assert captured.value.code == "candle-price-basis-contract-mismatch"
    assert captured.value.data == {
        "provider": "mismatched",
        "expected": "unadjusted",
        "observed": ["provider_adjusted"],
        "rule_version": "mock-candles-v1",
    }


def test_broker_returns_validated_policy_with_candles():
    batch = BrokerAdapter([MockProvider()]).candles("AAPL", 3)

    assert len(batch.candles) == 3
    assert batch.provider.name == "mock"
    assert batch.policy.rule_version == "mock-candles-v1"
    assert {candle.price_basis for candle in batch.candles} == {"unadjusted"}
