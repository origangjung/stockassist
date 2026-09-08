from datetime import date, datetime, timedelta
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

import pytest

from app.config import Settings
from scripts.ai.data.build_flow_local_ai_dataset import (
    _load_compatible_rows as load_compatible_flow_rows,
)
from scripts.ai.data.build_financial_local_ai_dataset import merge_rows
from scripts.ai.data.build_news_local_ai_dataset import (
    _load_compatible_rows as load_compatible_news_rows,
)
from scripts.ai.data.collect_local_ai_incremental import (
    collection_lock,
    active_news_request_limit,
    command_for,
    dataset_audit_command,
    due_jobs,
    earnings_enrichment_commands,
    earnings_candidate_audit_command,
    finalized_label_command,
    kis_dataset_audit_command,
    news_enrichment_command,
    publish_dataset_audit,
    normalized_symbols,
    preserve_role_labels,
    requested_symbols,
    rotating_news_symbols,
    reserve_news_requests,
    run_collection_job,
    safe_output_dir,
    save_state,
)


def test_news_request_limit_follows_the_active_provider():
    """증분 수집 회전 크기가 실제 활성 공급자의 예산을 사용한다."""

    gdelt = Settings(_env_file=None, news_training_source="gdelt", gdelt_daily_request_limit=40)
    both = Settings(
        _env_file=None,
        news_training_source="both",
        news_api_key="test-key",
        news_api_daily_request_limit=90,
        gdelt_daily_request_limit=40,
    )

    assert active_news_request_limit(gdelt) == 40
    assert active_news_request_limit(both) == 40


def test_news_rotation_covers_different_bounded_batches():
    symbols = [f"S{index}" for index in range(85)]
    first = rotating_news_symbols(
        symbols,
        date(2026, 8, 21),
        windows=4,
        daily_request_limit=90,
    )
    second = rotating_news_symbols(
        symbols,
        date(2026, 8, 22),
        windows=4,
        daily_request_limit=90,
    )

    assert len(first) == 22
    assert len(second) == 22
    assert first != second
    assert len(first) * 4 <= 90


def test_financial_collection_merges_without_losing_history():
    existing = [
        {"timestamp": "2025-01-01", "symbol": "AAPL", "value": "old"},
        {"timestamp": "2025-01-01", "symbol": "MSFT", "value": "keep"},
    ]
    incoming = [
        {"timestamp": "2025-01-01", "symbol": "AAPL", "value": "new"},
        {"timestamp": "2026-01-01", "symbol": "AAPL", "value": "append"},
    ]

    result = merge_rows(existing, incoming)

    assert len(result) == 3
    assert result[0]["value"] == "new"
    assert result[-1]["value"] == "append"


def test_incremental_schedule_runs_news_daily_and_financial_weekly():
    state = {"news": "2026-08-12", "financial": "2026-08-07"}

    assert due_jobs(
        "all", state, date(2026, 8, 13), financial_interval_days=7, force=False
    ) == ["market", "news", "flow", "kis_flow", "earnings"]
    assert due_jobs(
        "all", state, date(2026, 8, 14), financial_interval_days=7, force=False
    ) == ["market", "news", "financial", "flow", "kis_flow", "earnings"]


def test_incremental_news_budget_accumulates_across_forced_runs():
    state = {}
    today = date(2026, 8, 13)

    reserve_news_requests(state, today, projected=30, limit=90)
    reserve_news_requests(state, today, projected=45, limit=90)

    assert state["news_requests_used"] == 75
    with pytest.raises(ValueError, match="daily news request limit"):
        reserve_news_requests(state, today, projected=16, limit=90)


def test_incremental_commands_do_not_put_credentials_on_the_command_line(tmp_path):
    command = command_for(
        "news",
        ["AAPL", "MSFT"],
        tmp_path,
        news_window_days=7,
        news_windows=1,
    )

    assert "AAPL" in command
    assert str(tmp_path / "raw") in command
    assert not any("KEY" in value or "SECRET" in value for value in command)
    enrichment = news_enrichment_command(tmp_path)
    assert enrichment[-1] == "news"
    assert Path(enrichment[1]).is_file()
    assert str(tmp_path / "raw") in enrichment
    assert str(tmp_path) in enrichment
    assert not any("KEY" in value or "SECRET" in value for value in enrichment)
    audit_command = dataset_audit_command(tmp_path)
    assert audit_command[audit_command.index("--data-dir") + 1] == str(
        tmp_path / "labeled"
    )
    assert audit_command[-1] == str(
        tmp_path / "labeled" / "dataset-readiness.json"
    )
    assert not any("KEY" in value or "SECRET" in value for value in audit_command)
    financial = command_for(
        "financial", ["AAPL"], tmp_path, news_window_days=7, news_windows=1
    )
    assert financial[-2:] == ["--max-rows-per-symbol", "40"]
    flow = command_for(
        "flow", ["AAPL"], tmp_path, news_window_days=7, news_windows=1
    )
    assert "--include-market-context" in flow
    assert "2600" in flow
    assert "0.005" in flow
    assert flow[flow.index("--horizon-days") + 1] == "10"
    assert command[command.index("--horizon-days") + 1] == "3"
    kis = command_for(
        "kis_flow", ["005930"], tmp_path, news_window_days=7, news_windows=1
    )
    assert str(tmp_path / "kis-flow") in kis
    assert "--resume" in kis
    assert kis[kis.index("--horizon-days") + 1] == "10"
    assert not any("KEY" in value or "SECRET" in value for value in kis)
    earnings = command_for(
        "earnings",
        ["AAPL", "MSFT"],
        tmp_path,
        news_window_days=7,
        news_windows=1,
        earnings_max_symbols=20,
    )
    assert "collect_earnings_expectations.py" in earnings[1]
    assert earnings[earnings.index("--max-symbols") + 1] == "20"
    assert not any("KEY" in value or "SECRET" in value for value in earnings)


def test_candidate_audit_is_published_to_the_compatibility_path(tmp_path):
    labeled = tmp_path / "labeled"
    labeled.mkdir()
    report = labeled / "dataset-readiness.json"
    report.write_text('{"financial":{"rows":1265}}\n', encoding="utf-8")

    publish_dataset_audit(tmp_path)

    assert (tmp_path / "dataset-readiness.json").read_text(encoding="utf-8") == (
        report.read_text(encoding="utf-8")
    )


def test_earnings_candidates_use_the_incremental_canonical_path(tmp_path):
    assert earnings_enrichment_commands(tmp_path) == []
    earnings = tmp_path / "earnings" / "earnings.csv"
    technical = tmp_path / "market" / "technical.csv"
    financial = tmp_path / "labeled" / "financial.csv"
    for path in (earnings, technical, financial):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    commands = earnings_enrichment_commands(tmp_path)

    assert len(commands) == 2
    assert all(str(earnings) in command for command in commands)
    assert str(tmp_path / "earnings-candidates" / "technical.csv") in commands[0]
    assert str(tmp_path / "earnings-candidates" / "financial.csv") in commands[1]
    assert not any(
        "KEY" in value or "SECRET" in value
        for command in commands
        for value in command
    )

    assert earnings_candidate_audit_command(tmp_path) is None
    candidate = tmp_path / "earnings-candidates" / "technical.csv"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.touch()
    audit_command = earnings_candidate_audit_command(tmp_path)
    assert audit_command is not None
    assert str(candidate) in audit_command
    assert str(tmp_path / "earnings-candidates" / "readiness.json") in audit_command


def test_market_collection_and_label_finalization_commands_are_bounded(tmp_path):
    market = command_for(
        "market", ["AAPL"], tmp_path, news_window_days=7, news_windows=1, market_limit=500
    )
    assert "500" in market
    assert str(tmp_path / "market") in market
    assert market[market.index("--technical-horizon-days") + 1] == "10"
    assert market[market.index("--risk-horizon-days") + 1] == "5"
    assert market[market.index("--outcome-horizon-days") + 1] == "20"
    assert not any("KEY" in value or "SECRET" in value for value in market)

    (tmp_path / "market").mkdir()
    (tmp_path / "market" / "outcomes-20.csv").touch()
    (tmp_path / "financial.csv").touch()
    command = finalized_label_command(tmp_path)
    assert command is not None
    assert Path(command[1]).is_file()
    assert command[-2:] == ["--agent", "financial"]
    assert str(tmp_path / "market" / "outcomes-20.csv") in command


def test_role_specific_labels_are_copied_without_relabeling(tmp_path):
    news = tmp_path / "news.csv"
    flow = tmp_path / "investor_flow.csv"
    news.write_text("timestamp,symbol,horizon_days,label\n2026-01-01,AAPL,3,1\n")
    flow.write_text("timestamp,symbol,horizon_days,label\n2026-01-01,AAPL,10,0\n")

    preserve_role_labels(tmp_path)

    assert (tmp_path / "labeled" / "news.csv").read_text() == news.read_text()
    assert (tmp_path / "labeled" / "investor_flow.csv").read_text() == flow.read_text()


def test_legacy_news_is_archived_outside_active_candidate_inputs(tmp_path):
    news = tmp_path / "news.csv"
    labeled = tmp_path / "labeled"
    labeled.mkdir()
    old_candidate = labeled / "news.csv"
    legacy = "timestamp,symbol,label\n2026-01-01,AAPL,1\n"
    news.write_text(legacy, encoding="utf-8")
    old_candidate.write_text(legacy, encoding="utf-8")

    preserve_role_labels(tmp_path)

    assert not old_candidate.exists()
    assert (labeled / "news-legacy-5d.csv").read_text() == legacy


def test_legacy_news_horizon_is_archived_instead_of_reinterpreted(tmp_path):
    target = tmp_path / "news.csv"
    target.write_text(
        "timestamp,symbol,label\n2026-01-01,AAPL,1\n",
        encoding="utf-8",
    )

    rows = load_compatible_news_rows(target, horizon_days=3)

    assert rows == []
    assert (tmp_path / "news-legacy-5d.csv").read_bytes() == target.read_bytes()


def test_legacy_flow_horizon_is_archived_instead_of_reinterpreted(tmp_path):
    target = tmp_path / "investor_flow.csv"
    target.write_text(
        "timestamp,symbol,label\n2026-01-01,AAPL,0\n",
        encoding="utf-8",
    )

    rows = load_compatible_flow_rows(
        target,
        horizon_days=10,
        include_market_context=False,
        resume=True,
    )

    assert rows == []
    assert (tmp_path / "investor_flow-legacy-5d.csv").read_bytes() == target.read_bytes()


def test_incremental_collection_rejects_unsafe_inputs():
    with pytest.raises(ValueError):
        normalized_symbols(["AAPL; whoami"])
    with pytest.raises(ValueError):
        safe_output_dir(Path.home())


def test_incremental_collection_accepts_compose_csv_symbols():
    assert requested_symbols(["aapl", "MSFT"], "MSFT,nvda") == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]


def test_incremental_collection_lock_rejects_concurrent_runs(tmp_path):
    lock_path = tmp_path / ".collection.lock"

    with collection_lock(lock_path):
        assert lock_path.is_file()
        with pytest.raises(RuntimeError, match="already running"):
            with collection_lock(lock_path):
                pass

    assert not lock_path.exists()


def test_incremental_collection_reclaims_stale_lock(tmp_path):
    lock_path = tmp_path / ".collection.lock"
    lock_path.write_text("stale", encoding="utf-8")
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    stale_timestamp = (now - timedelta(hours=7)).timestamp()
    lock_path.touch()
    os.utime(lock_path, (stale_timestamp, stale_timestamp))

    with collection_lock(lock_path, now=now):
        assert "started_at=" in lock_path.read_text(encoding="utf-8")


def test_incremental_state_save_is_atomic_and_leaves_no_temporary_file(tmp_path):
    state_path = tmp_path / "collection-state.json"

    save_state(state_path, {"news": "2026-08-14", "news_requests_used": 15})

    assert '"news_requests_used": 15' in state_path.read_text(encoding="utf-8")
    assert list(tmp_path.glob(".*.tmp")) == []


def test_kis_audit_is_separate_from_finra_dataset(tmp_path):
    assert kis_dataset_audit_command(tmp_path) is None
    data_dir = tmp_path / "kis-flow"
    data_dir.mkdir()
    (data_dir / "investor_flow.csv").touch()

    command = kis_dataset_audit_command(tmp_path)

    assert command is not None
    assert str(data_dir) in command
    assert str(data_dir / "dataset-readiness.json") in command


def test_optional_provider_failures_are_isolated_but_market_failure_is_raised(
    monkeypatch,
):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr("scripts.ai.data.collect_local_ai_incremental.subprocess.run", fail)

    assert run_collection_job("kis_flow", ["python", "collector.py"]) is False
    assert run_collection_job("news", ["python", "collector.py"]) is False
    with pytest.raises(subprocess.CalledProcessError):
        run_collection_job("market", ["python", "collector.py"])
