"""자격 증명을 노출하지 않고 뉴스와 SEC 데이터를 제한적으로 증분 수집한다."""

import argparse
from contextlib import contextmanager
import csv
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterator
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.collection_universe import (  # noqa: E402
    DEFAULT_COLLECTION_SYMBOLS,
    DEFAULT_KIS_FLOW_SYMBOLS,
)


SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,10}$")
MAX_SYMBOLS = 90
STATE_FIELDS = {
    "news", "financial", "market", "flow", "kis_flow", "earnings", "news_request_date",
    "news_requests_used"
}
LOCK_STALE_AFTER = timedelta(hours=6)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="*", default=[])
    parser.add_argument(
        "--symbols-csv",
        default=os.getenv("LOCAL_AI_COLLECTION_SYMBOLS", "")
        or ",".join(DEFAULT_COLLECTION_SYMBOLS),
        help="Docker Compose처럼 배열 인자를 전달하기 어려운 환경에서 사용할 쉼표 구분 종목 목록",
    )
    parser.add_argument(
        "--kis-symbols-csv",
        default=os.getenv("LOCAL_AI_KIS_SYMBOLS", "")
        or ",".join(DEFAULT_KIS_FLOW_SYMBOLS),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            os.getenv(
                "LOCAL_AI_COLLECTION_OUTPUT_DIR",
                str(DATASET_ROOT / "local-ai-incremental"),
            )
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("all", "news", "financial", "market", "flow", "kis_flow", "earnings"),
        default="all",
    )
    parser.add_argument("--news-window-days", type=int, default=7)
    parser.add_argument("--news-windows", type=int, default=4)
    parser.add_argument("--financial-interval-days", type=int, default=7)
    parser.add_argument("--flow-interval-days", type=int, default=7)
    parser.add_argument("--financial-max-rows-per-symbol", type=int, default=40)
    # 시장 데이터 생성기는 결과 파일을 교체하므로 장기 학습 이력이 줄지 않게
    # 예약 실행과 직접 실행 모두 동일한 전체 백필 범위를 기본값으로 사용한다.
    parser.add_argument("--market-limit", type=int, default=2600)
    parser.add_argument("--flow-market-limit", type=int, default=2600)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def requested_symbols(values: list[str], csv_value: str) -> list[str]:
    """반복 인자와 쉼표 구분 인자를 합쳐 검증된 종목 목록으로 만든다."""

    return normalized_symbols([*values, *csv_value.split(",")])


def normalized_symbols(values: list[str]) -> list[str]:
    """`normalized_symbols`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    symbols = list(dict.fromkeys(value.strip().upper() for value in values))
    if (
        not symbols
        or len(symbols) > MAX_SYMBOLS
        or any(not SYMBOL_PATTERN.fullmatch(symbol) for symbol in symbols)
    ):
        raise ValueError("symbols are empty, invalid, or exceed the collection limit")
    return symbols


def rotating_news_symbols(
    symbols: list[str],
    today: date,
    *,
    windows: int,
    daily_request_limit: int,
) -> list[str]:
    """무료 요청 한도 안에서 종목을 순환하며 여러 과거 뉴스 구간을 수집한다."""

    if windows < 1 or daily_request_limit < windows:
        raise ValueError("news rotation settings exceed the daily request budget")
    batch_size = min(len(symbols), daily_request_limit // windows)
    if batch_size == len(symbols):
        return symbols
    start = (today.toordinal() * batch_size) % len(symbols)
    return [symbols[(start + offset) % len(symbols)] for offset in range(batch_size)]


def active_news_request_limit(settings: Settings) -> int:
    """선택한 뉴스 공급자 조합에서 초과하면 안 되는 일일 호출 한도를 반환한다."""

    if settings.news_training_source == "gdelt":
        return settings.gdelt_daily_request_limit
    if settings.news_training_source == "newsapi":
        return settings.news_api_daily_request_limit
    if settings.news_training_source == "official_rss":
        return MAX_SYMBOLS * 12
    newsapi_key = (
        settings.news_api_key.get_secret_value().strip() if settings.news_api_key else ""
    )
    return min(settings.news_api_daily_request_limit, settings.gdelt_daily_request_limit) if newsapi_key else settings.gdelt_daily_request_limit


def safe_output_dir(value: Path) -> Path:
    """`safe_output_dir`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    path = value.expanduser().resolve()
    if not path.is_relative_to(DATASET_ROOT):
        raise ValueError("output directory must remain inside the project datasets directory")
    return path


def load_state(path: Path) -> dict[str, str | int]:
    """`load_state`은(는) 필요한 데이터를 조회해 반환합니다."""

    if not path.is_file():
        return {}
    if path.stat().st_size > 16 * 1024 or path.is_symlink():
        raise ValueError("collection state file is invalid")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or any(
        key not in STATE_FIELDS
        or (
            not isinstance(value, str)
            if key != "news_requests_used"
            else not isinstance(value, int) or isinstance(value, bool) or value < 0
        )
        for key, value in payload.items()
    ):
        raise ValueError("collection state has an invalid schema")
    return payload


def due_jobs(
    mode: str,
    state: dict[str, str | int],
    today: date,
    *,
    financial_interval_days: int,
    flow_interval_days: int = 7,
    force: bool,
) -> list[str]:
    """`due_jobs`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if not 1 <= financial_interval_days <= 90:
        raise ValueError("financial interval must be between 1 and 90 days")
    selected = (
        ("market", "news", "financial", "flow", "kis_flow", "earnings")
        if mode == "all"
        else (mode,)
    )
    jobs = []
    for job in selected:
        previous = date.fromisoformat(str(state[job])) if job in state else None
        interval = (
            financial_interval_days
            if job == "financial"
            else flow_interval_days
            if job in {"flow", "kis_flow"}
            else 1
        )
        if force or previous is None or (today - previous).days >= interval:
            jobs.append(job)
    return jobs


def command_for(
    job: str,
    symbols: list[str],
    output_dir: Path,
    *,
    news_window_days: int,
    news_windows: int,
    market_limit: int = 500,
    financial_max_rows_per_symbol: int = 40,
    flow_market_limit: int = 2600,
    earnings_max_symbols: int = 25,
) -> list[str]:
    """`command_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다."""

    if job == "earnings":
        if not 1 <= earnings_max_symbols <= 25:
            raise ValueError("earnings batch must remain within the free daily limit")
        return [
            sys.executable,
            str(ROOT / "scripts" / "ai" / "data" / "collect_earnings_expectations.py"),
            "--symbols",
            *symbols,
            "--output",
            str(output_dir / "earnings" / "earnings.csv"),
            "--max-symbols",
            str(earnings_max_symbols),
        ]
    if job == "kis_flow":
        return [
            sys.executable,
            str(ROOT / "scripts" / "ai" / "data" / "build_kis_flow_local_ai_dataset.py"),
            "--symbols",
            *symbols,
            "--history-days",
            "730",
            "--horizon-days",
            "10",
            "--output-dir",
            str(output_dir / "kis-flow"),
            "--resume",
        ]
    if job == "market":
        if not 50 <= market_limit <= 5000:
            raise ValueError("market limit must be between 50 and 5000")
        return [
            sys.executable,
            str(ROOT / "scripts" / "ai" / "data" / "build_market_local_ai_dataset.py"),
            "--symbols",
            *symbols,
            "--limit",
            str(market_limit),
            "--horizon-days",
            "5",
            "--technical-horizon-days",
            "10",
            "--risk-horizon-days",
            "5",
            "--outcome-horizon-days",
            "20",
            "--benchmark-symbol",
            "SPY",
            "--output-dir",
            str(output_dir / "market"),
        ]
    if job == "flow":
        if not 200 <= flow_market_limit <= 5000:
            raise ValueError("flow market limit must be between 200 and 5000")
        return [
            sys.executable,
            str(ROOT / "scripts" / "ai" / "data" / "build_flow_local_ai_dataset.py"),
            "--symbols",
            *symbols,
            "--limit",
            str(flow_market_limit),
            "--horizon-days",
            "10",
            "--output-dir",
            str(output_dir),
            "--include-market-context",
            "--minimum-absolute-excess-return",
            "0.005",
        ]
    script = ROOT / "scripts" / "ai" / "data" / f"build_{job}_local_ai_dataset.py"
    target_dir = output_dir / "raw" if job == "news" else output_dir
    command = [
        sys.executable,
        str(script),
        "--symbols",
        *symbols,
        "--output-dir",
        str(target_dir),
    ]
    if job == "news":
        if not 1 <= news_window_days <= 30 or not 1 <= news_windows <= 12:
            raise ValueError("news window settings are outside the supported range")
        command.extend(
            [
                "--window-days",
                str(news_window_days),
                "--windows",
                str(news_windows),
                "--horizon-days",
                "3",
            ]
        )
    elif job == "financial":
        if not 8 <= financial_max_rows_per_symbol <= 80:
            raise ValueError("financial history must contain between 8 and 80 quarterly rows")
        command.extend(["--max-rows-per-symbol", str(financial_max_rows_per_symbol)])
    return command


def finalized_label_command(output_dir: Path) -> list[str] | None:
    """재무 행만 별도 20거래일 시장 재평가 정답에 맞춘다."""
    if (
        not (output_dir / "financial.csv").is_file()
        or not (output_dir / "market" / "outcomes-20.csv").is_file()
    ):
        return None
    return [
        sys.executable,
        str(
            ROOT
            / "scripts"
            / "ai"
            / "data"
            / "relabel_specialists_with_market_outcomes.py"
        ),
        "--market-data-dir",
        str(output_dir / "market"),
        "--market-outcomes",
        str(output_dir / "market" / "outcomes-20.csv"),
        "--source-data-dir",
        str(output_dir),
        "--output-dir",
        str(output_dir / "labeled"),
        "--agent",
        "financial",
    ]


def preserve_role_labels(output_dir: Path) -> None:
    """뉴스 3일·수급 10일 자체 정답을 후보 디렉터리에 원자 복사한다."""

    labeled = output_dir / "labeled"
    labeled.mkdir(parents=True, exist_ok=True)
    for agent, expected_horizon in (("news", 3), ("investor_flow", 10)):
        source = output_dir / f"{agent}.csv"
        target = labeled / f"{agent}.csv"
        source_horizon = _dataset_horizon(source)
        if source_horizon != expected_horizon:
            target_horizon = _dataset_horizon(target)
            if target_horizon is not None and target_horizon != expected_horizon:
                archive = labeled / f"{agent}-legacy-{target_horizon}d.csv"
                os.replace(target, archive)
            continue
        temporary = labeled / f".{agent}.{os.getpid()}.tmp"
        try:
            shutil.copyfile(source, temporary)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)


def _dataset_horizon(path: Path) -> int | None:
    """CSV의 단일 예측 기간을 읽고, 기간 열이 없는 과거 행은 5일로 해석한다."""

    if not path.is_file() or path.is_symlink():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        if not rows:
            return None
        if "horizon_days" not in (reader.fieldnames or []):
            return 5
    horizons = {int(row["horizon_days"]) for row in rows if row.get("horizon_days")}
    if len(horizons) != 1:
        raise ValueError(f"{path.name} must contain exactly one prediction horizon")
    return horizons.pop()


def news_enrichment_command(output_dir: Path) -> list[str]:
    """`news_enrichment_command`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return [
        sys.executable,
        str(ROOT / "scripts" / "ai" / "data" / "enrich_contextual_specialists.py"),
        "--data-dir",
        str(output_dir / "raw"),
        "--output-dir",
        str(output_dir),
        "--dataset",
        "news",
    ]


def earnings_enrichment_commands(output_dir: Path) -> list[list[str]]:
    """실적 원천과 대상 데이터가 모두 있을 때만 후보 결합 명령을 만든다."""

    earnings = output_dir / "earnings" / "earnings.csv"
    if not earnings.is_file() or earnings.is_symlink():
        return []
    candidates = output_dir / "earnings-candidates"
    commands: list[list[str]] = []
    technical = output_dir / "market" / "technical.csv"
    if technical.is_file() and not technical.is_symlink():
        commands.append(
            [
                sys.executable,
                str(
                    ROOT
                    / "scripts"
                    / "ai"
                    / "data"
                    / "enrich_technical_earnings_expectations.py"
                ),
                "--technical",
                str(technical),
                "--earnings",
                str(earnings),
                "--output",
                str(candidates / "technical.csv"),
            ]
        )
    financial = output_dir / "labeled" / "financial.csv"
    if financial.is_file() and not financial.is_symlink():
        commands.append(
            [
                sys.executable,
                str(
                    ROOT
                    / "scripts"
                    / "ai"
                    / "data"
                    / "enrich_financial_earnings_expectations.py"
                ),
                "--financial",
                str(financial),
                "--earnings",
                str(earnings),
                "--output",
                str(candidates / "financial.csv"),
            ]
        )
    return commands


def earnings_candidate_audit_command(output_dir: Path) -> list[str] | None:
    """기술 실적 후보가 있을 때 커버리지·누수 감사 명령을 만든다."""

    candidate = output_dir / "earnings-candidates" / "technical.csv"
    source = output_dir / "market" / "technical.csv"
    if (
        not candidate.is_file()
        or candidate.is_symlink()
        or not source.is_file()
        or source.is_symlink()
    ):
        return None
    return [
        sys.executable,
        str(
            ROOT
            / "scripts"
            / "ai"
            / "training"
            / "audit_technical_earnings_candidate.py"
        ),
        "--candidate",
        str(candidate),
        "--source",
        str(source),
        "--output",
        str(output_dir / "earnings-candidates" / "readiness.json"),
    ]


def dataset_audit_command(output_dir: Path) -> list[str]:
    """실제 후보 CSV의 무결성과 재학습 준비도를 기록하는 명령을 만든다."""

    candidate_dir = output_dir / "labeled"

    return [
        sys.executable,
        str(ROOT / "scripts" / "ai" / "training" / "audit_local_ai_datasets.py"),
        "--data-dir",
        str(candidate_dir),
        "--all-safe-features",
        "--output",
        str(candidate_dir / "dataset-readiness.json"),
    ]


def publish_dataset_audit(output_dir: Path) -> None:
    """후보 감사 결과를 기존 운영 경로에도 원자적으로 게시한다."""

    source = output_dir / "labeled" / "dataset-readiness.json"
    if not source.is_file() or source.is_symlink():
        raise ValueError("candidate dataset audit is unavailable")
    target = output_dir / "dataset-readiness.json"
    temporary = output_dir / f".dataset-readiness.{os.getpid()}.tmp"
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def kis_dataset_audit_command(output_dir: Path) -> list[str] | None:
    """KIS 후보 데이터가 존재할 때만 FINRA와 분리된 품질 보고서를 만든다."""

    data_dir = output_dir / "kis-flow"
    if not (data_dir / "investor_flow.csv").is_file():
        return None
    return [
        sys.executable,
        str(ROOT / "scripts" / "ai" / "training" / "audit_local_ai_datasets.py"),
        "--data-dir",
        str(data_dir),
        "--agent",
        "investor_flow",
        "--all-safe-features",
        "--output",
        str(data_dir / "dataset-readiness.json"),
    ]


def run_collection_job(job: str, command: list[str]) -> bool:
    """일반 작업은 즉시 실패시키고 KIS 장애만 다음 작업과 감사 단계에서 격리한다."""

    try:
        subprocess.run(command, cwd=ROOT, check=True)
        return True
    except subprocess.CalledProcessError:
        if job in {"news", "kis_flow"}:
            return False
        raise


def reserve_news_requests(
    state: dict[str, str | int], today: date, *, projected: int, limit: int
) -> None:
    """`reserve_news_requests`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if projected < 1 or limit < 1:
        raise ValueError("news request budget must be positive")
    used = (
        int(state.get("news_requests_used", 0))
        if state.get("news_request_date") == today.isoformat()
        else 0
    )
    if used + projected > limit:
        raise ValueError("incremental collection would exceed the daily news request limit")
    state["news_request_date"] = today.isoformat()
    state["news_requests_used"] = used + projected


def save_state(path: Path, state: dict[str, str | int]) -> None:
    """호출 예산 상태를 배타적 임시 파일에 쓴 뒤 원자적으로 교체한다."""

    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            json.dump(state, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


@contextmanager
def collection_lock(path: Path, *, now: datetime | None = None) -> Iterator[None]:
    """동시에 실행된 수집기가 일일 호출 예산과 상태 파일을 중복 갱신하지 못하게 한다."""

    current = now or datetime.now(ZoneInfo("Asia/Seoul"))
    if path.is_symlink():
        raise ValueError("collection lock path must not be a symbolic link")
    if path.exists():
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=ZoneInfo("Asia/Seoul"))
        if current - modified <= LOCK_STALE_AFTER:
            raise RuntimeError("another incremental collector is already running")
        path.unlink()

    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(descriptor, f"pid={os.getpid()}\nstarted_at={current.isoformat()}\n".encode())
        yield
    except FileExistsError as exc:
        raise RuntimeError("another incremental collector is already running") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
            path.unlink(missing_ok=True)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    settings = Settings()
    symbols = requested_symbols(args.symbols, args.symbols_csv)
    kis_symbols = normalized_symbols(args.kis_symbols_csv.split(","))
    output_dir = safe_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with collection_lock(output_dir / ".collection.lock"):
        state_path = output_dir / "collection-state.json"
        state = load_state(state_path)
        today = datetime.now(ZoneInfo("Asia/Seoul")).date()
        jobs = due_jobs(
            args.mode,
            state,
            today,
            financial_interval_days=args.financial_interval_days,
            flow_interval_days=args.flow_interval_days,
            force=args.force,
        )
        alpha_vantage_enabled = bool(
            settings.alpha_vantage_api_key
            and settings.alpha_vantage_api_key.get_secret_value().strip()
        )
        skipped_jobs: list[str] = []
        if "earnings" in jobs and not alpha_vantage_enabled:
            jobs.remove("earnings")
            skipped_jobs.append("earnings:no_api_key")
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "jobs": jobs,
                        "skipped": skipped_jobs,
                        "symbols": len(symbols),
                        "kis_symbols": len(kis_symbols),
                    },
                    ensure_ascii=True,
                )
            )
            return 0
        failed_jobs: list[str] = []
        for job in jobs:
            job_symbols = kis_symbols if job == "kis_flow" else symbols
            if job == "news":
                job_symbols = rotating_news_symbols(
                    symbols,
                    today,
                    windows=args.news_windows,
                    daily_request_limit=active_news_request_limit(settings),
                )
            command = command_for(
                job,
                job_symbols,
                output_dir,
                news_window_days=args.news_window_days,
                news_windows=args.news_windows,
                market_limit=args.market_limit,
                financial_max_rows_per_symbol=args.financial_max_rows_per_symbol,
                flow_market_limit=args.flow_market_limit,
                earnings_max_symbols=settings.alpha_vantage_daily_request_limit,
            )
            if job == "news":
                try:
                    reserve_news_requests(
                        state,
                        today,
                        projected=len(job_symbols) * args.news_windows,
                        limit=active_news_request_limit(settings),
                    )
                except ValueError:
                    failed_jobs.append(job)
                    continue
                save_state(state_path, state)
            if not run_collection_job(job, command):
                failed_jobs.append(job)
                continue
            if job == "news":
                subprocess.run(news_enrichment_command(output_dir), cwd=ROOT, check=True)
            state[job] = today.isoformat()
            save_state(state_path, state)
        label_command = finalized_label_command(output_dir)
        if label_command is not None:
            subprocess.run(label_command, cwd=ROOT, check=True)
        preserve_role_labels(output_dir)
        for enrichment_command in earnings_enrichment_commands(output_dir):
            subprocess.run(enrichment_command, cwd=ROOT, check=True)
        earnings_audit = earnings_candidate_audit_command(output_dir)
        if earnings_audit is not None:
            subprocess.run(earnings_audit, cwd=ROOT, check=True)
        subprocess.run(dataset_audit_command(output_dir), cwd=ROOT, check=True)
        publish_dataset_audit(output_dir)
        kis_audit = kis_dataset_audit_command(output_dir)
        if kis_audit is not None:
            subprocess.run(kis_audit, cwd=ROOT, check=True)
    completed = [job for job in jobs if job not in failed_jobs]
    print(
        json.dumps(
            {
                "completed": completed,
                "failed": failed_jobs,
                "skipped": skipped_jobs,
                "symbols": len(symbols),
            },
            ensure_ascii=True,
        )
    )
    return 1 if failed_jobs else 0


if __name__ == "__main__":
    raise SystemExit(main())
