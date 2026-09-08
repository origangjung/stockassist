"""sec_event_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from datetime import date, datetime
import math
import re


SEC_EVENT_FEATURES = (
    "event_results",
    "event_guidance_or_disclosure",
    "event_material_agreement",
    "event_acquisition",
    "event_leadership",
    "event_other",
    "event_item_count_log",
    "event_after_hours",
    "event_days_since_previous_log",
)


def extract_8k_events(submissions: dict) -> list[dict]:
    """`extract_8k_events`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    recent = ((submissions.get("filings") or {}).get("recent") or {})
    forms = recent.get("form") or []
    accessions = recent.get("accessionNumber") or []
    filing_dates = recent.get("filingDate") or []
    accepted = recent.get("acceptanceDateTime") or []
    raw_items = recent.get("items") or []
    count = min(len(forms), len(accessions), len(filing_dates))
    events = []
    for index in range(count):
        if str(forms[index]).upper() not in {"8-K", "8-K/A"}:
            continue
        try:
            filed = date.fromisoformat(str(filing_dates[index])[:10])
        except ValueError:
            continue
        accession = str(accessions[index]).strip()
        if not accession:
            continue
        acceptance = _acceptance_datetime(
            str(accepted[index]) if index < len(accepted) else "",
            filed,
        )
        items = _items(str(raw_items[index]) if index < len(raw_items) else "")
        events.append(
            {
                "timestamp": acceptance.isoformat(),
                "accession": accession,
                "_filed": filed,
                "_items": items,
            }
        )
    events.sort(key=lambda row: (str(row["timestamp"]), str(row["accession"])))
    previous_date: date | None = None
    result = []
    for event in events:
        filed = event["_filed"]
        items = event["_items"]
        gap = (filed - previous_date).days if previous_date is not None else 365
        accepted_at = datetime.fromisoformat(str(event["timestamp"]))
        result.append(
            {
                "timestamp": event["timestamp"],
                "accession": event["accession"],
                "event_results": float("2.02" in items),
                "event_guidance_or_disclosure": float("7.01" in items),
                "event_material_agreement": float("1.01" in items),
                "event_acquisition": float("2.01" in items),
                "event_leadership": float("5.02" in items),
                "event_other": float("8.01" in items),
                "event_item_count_log": math.log1p(len(items)),
                "event_after_hours": float(
                    accepted_at.hour >= 16 or accepted_at.hour < 9
                ),
                "event_days_since_previous_log": math.log1p(max(gap, 0)),
            }
        )
        previous_date = filed
    return result


def _items(value: str) -> set[str]:
    """`_items`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return set(re.findall(r"\b\d\.\d{2}\b", value))


def _acceptance_datetime(value: str, filed: date) -> datetime:
    """`_acceptance_datetime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    compact = re.sub(r"\D", "", value)
    if len(compact) >= 14:
        try:
            return datetime.strptime(compact[:14], "%Y%m%d%H%M%S")
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.combine(filed, datetime.min.time())
