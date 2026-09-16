from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

from axq.mt5 import GoldSymbolConfiguration, resolve_gold_instrument
from axq.orchestration.shadow_report import latest_shadow_records
from axq.runtime.journal import SQLiteRuntimeJournal
from axq.runtime.shadow import LiveMarketStatus, ShadowMarketAvailability


def test_shadow_boundary_contains_no_broker_mutation_calls() -> None:
    root = Path("src/axq")
    files = (
        root / "orchestration/shadow.py",
        root / "orchestration/shadow_runtime.py",
        root / "runtime/shadow_sink.py",
        root / "mt5/live_source.py",
    )
    forbidden = {"order_send", "order_check", "symbol_select", "positions_close"}
    found: set[str] = set()
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found.update(
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden
        )
    assert found == set()


def test_shadow_report_requires_an_explicit_journal_path(tmp_path: Path) -> None:
    # A non-existent explicit source is not discovered or replaced with another file.
    try:
        latest_shadow_records(tmp_path / "missing.sqlite3")
    except Exception as error:
        assert "unable to open" in str(error).lower() or "no such" in str(error).lower()
    else:
        raise AssertionError("missing explicit journal must fail closed")


def test_shadow_report_includes_instrument_resolution_and_market_availability(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)

    class Gateway:
        def symbol_info(self, symbol: str) -> dict[str, object]:
            return {"name": symbol, "point": 0.01}

    resolution = resolve_gold_instrument(
        Gateway(), GoldSymbolConfiguration.single("XAUUSD.sc"), resolved_at=now
    )
    availability = ShadowMarketAvailability(
        resolved_broker_symbol=resolution.resolved_broker_symbol,
        instrument_resolution_id=resolution.resolution_id,
        observed_at=now,
        available_at=now,
        broker_tick_at=now,
        status=LiveMarketStatus.WAITING_FOR_NEXT_M5,
        reason_code="WAITING_FOR_NEXT_COMPLETED_M5",
    )
    path = tmp_path / "runtime.sqlite3"
    journal = SQLiteRuntimeJournal(path)
    journal.append_semantic(resolution, event_id=None)
    journal.append_semantic(availability, event_id=None)

    result = latest_shadow_records(path)

    assert result["INSTRUMENT_RESOLUTION"]["resolved_broker_symbol"] == "XAUUSD.sc"  # type: ignore[index]
    assert result["SHADOW_MARKET_AVAILABILITY"]["canonical_instrument"] == "XAUUSD"  # type: ignore[index]
