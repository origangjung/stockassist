from dataclasses import asdict

from app.adapters.broker import BrokerAdapter
from app.providers.contracts import BrokerAccount, Capability, HoldingsSnapshot
from app.providers.errors import ProviderForbiddenError, ProviderNotFoundError
from app.repositories.contracts import PortfolioRepository
from app.portfolio import analyze_portfolio


class PortfolioService:
    """Read-only own-account portfolio synchronization and neutral exposure analysis."""

    def __init__(
        self,
        broker: BrokerAdapter,
        *,
        sync_enabled: bool,
        repository: PortfolioRepository | None = None,
    ) -> None:
        self._broker = broker
        self._sync_enabled = sync_enabled
        self._repository = repository

    def accounts(self) -> dict:
        self._require_enabled()
        provider = self._broker.provider_for(Capability.ACCOUNT_SYNC)
        return {
            "provider": provider.name,
            "accounts": [self._account_data(account) for account in provider.get_accounts()],
        }

    def sync(self, account_seq: int) -> dict:
        self._require_enabled()
        provider = self._broker.provider_for(Capability.ACCOUNT_SYNC)
        account = self._account(provider.get_accounts(), account_seq)
        snapshot = provider.get_holdings(account_seq)
        if self._repository is not None:
            self._repository.save_snapshot(provider.name, account, snapshot)
        return {
            "provider": provider.name,
            "account": self._account_data(account),
            "summary": self._summary(snapshot),
            "holdings": self._holding_data(snapshot),
            "analysis": analyze_portfolio(snapshot),
            "data_as_of": snapshot.fetched_at,
            "is_read_only": True,
            "is_investment_advice": False,
            "persistence_status": "saved" if self._repository is not None else "disabled",
        }

    @staticmethod
    def _account(accounts: list[BrokerAccount], account_seq: int) -> BrokerAccount:
        for account in accounts:
            if account.account_seq == account_seq:
                return account
        raise ProviderNotFoundError("Broker account was not found", code="account-not-found")

    def _require_enabled(self) -> None:
        if not self._sync_enabled:
            raise ProviderForbiddenError(
                "Account synchronization is disabled. Set ACCOUNT_SYNC_ENABLED=true only on a protected server.",
                code="account-sync-disabled",
                status_code=403,
            )

    @staticmethod
    def _account_data(account: BrokerAccount) -> dict:
        return {
            "account_seq": account.account_seq,
            "account_no_masked": _mask_account_no(account.account_no),
            "account_type": account.account_type,
        }

    @staticmethod
    def _summary(snapshot: HoldingsSnapshot) -> dict:
        return {
            "total_purchase_amount": snapshot.total_purchase_amount,
            "market_value": snapshot.market_value,
            "market_value_after_cost": snapshot.market_value_after_cost,
            "profit_loss": snapshot.profit_loss,
            "profit_loss_after_cost": snapshot.profit_loss_after_cost,
            "profit_rate": snapshot.profit_rate,
            "profit_rate_after_cost": snapshot.profit_rate_after_cost,
            "daily_profit_loss": snapshot.daily_profit_loss,
            "daily_profit_rate": snapshot.daily_profit_rate,
        }

    @staticmethod
    def _holding_data(snapshot: HoldingsSnapshot) -> list[dict]:
        totals = snapshot.market_value
        rows: list[dict] = []
        for holding in snapshot.holdings:
            value = totals.get(holding.currency)
            allocation = holding.market_value / value if value else None
            rows.append({**asdict(holding), "allocation_within_currency": allocation})
        return rows


def _mask_account_no(account_no: str) -> str:
    visible = account_no[-4:]
    return f"{'*' * max(0, len(account_no) - len(visible))}{visible}"
