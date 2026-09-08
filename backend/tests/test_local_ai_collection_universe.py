from app.local_ai.collection_universe import (
    COLLECTION_SYMBOLS_BY_SECTOR,
    DEFAULT_COLLECTION_SYMBOLS,
)
from scripts.ai.data.collect_local_ai_incremental import MAX_SYMBOLS, normalized_symbols


def test_default_collection_universe_is_diverse_unique_and_within_request_budget():
    assert len(COLLECTION_SYMBOLS_BY_SECTOR) >= 10
    assert 40 <= len(DEFAULT_COLLECTION_SYMBOLS) <= MAX_SYMBOLS
    assert len(DEFAULT_COLLECTION_SYMBOLS) == len(set(DEFAULT_COLLECTION_SYMBOLS))
    assert normalized_symbols(list(DEFAULT_COLLECTION_SYMBOLS)) == list(
        DEFAULT_COLLECTION_SYMBOLS
    )


def test_default_collection_universe_keeps_each_sector_from_dominating():
    largest_sector = max(map(len, COLLECTION_SYMBOLS_BY_SECTOR.values()))

    assert largest_sector / len(DEFAULT_COLLECTION_SYMBOLS) <= 0.2
