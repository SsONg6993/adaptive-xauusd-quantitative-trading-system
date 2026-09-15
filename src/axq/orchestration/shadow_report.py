"""Read-only canonical report for the latest persisted live-shadow facts."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from axq.runtime.journal import JournalRecord, JournalRecordType


def latest_shadow_records(path: Path) -> dict[str, object | None]:
    wanted = (
        JournalRecordType.INSTRUMENT_RESOLUTION,
        JournalRecordType.MT5_TIME_OFFSET_RESOLUTION,
        JournalRecordType.MT5_TIMESTAMP_NORMALIZATION,
        JournalRecordType.SHADOW_MARKET_AVAILABILITY,
        JournalRecordType.M15_CONTEXT,
        JournalRecordType.M5_CANDIDATE_SCAN,
        JournalRecordType.SHADOW_RUNTIME_CYCLE,
        JournalRecordType.HYPOTHETICAL_TRADE_PLAN,
        JournalRecordType.SHADOW_EXECUTION,
    )
    latest: dict[JournalRecordType, object] = {}
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute(
            "SELECT record_json FROM runtime_journal ORDER BY journal_sequence"
        )
        for row in rows:
            record = JournalRecord.model_validate_json(str(row["record_json"]))
            if record.record_type in wanted:
                latest[record.record_type] = record.decode().model_dump(mode="json")
    finally:
        connection.close()
    return {kind.value: latest.get(kind) for kind in wanted}


def main() -> None:
    parser = argparse.ArgumentParser(description="Show latest AXQ shadow cycle and plan")
    parser.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            latest_shadow_records(args.journal),
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
