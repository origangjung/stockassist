from app.local_ai.sec import SecCompanyFactsClient


def test_sec_client_releases_large_symbol_payloads_after_batch_processing():
    client = object.__new__(SecCompanyFactsClient)
    client._ticker_map = {"AAPL": "0000320193"}
    client._facts = {"0000320193": ({"large": "payload"}, 999.0)}
    client._submissions = {"0000320193": ({"recent": []}, 999.0)}

    client.release_cached_symbol("AAPL")

    assert client._facts == {}
    assert client._submissions == {}
    assert client._ticker_map == {"AAPL": "0000320193"}
