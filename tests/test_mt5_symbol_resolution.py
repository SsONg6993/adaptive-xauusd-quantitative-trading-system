from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

import pytest

from axq.mt5.symbols import (
    BrokerSymbolSelectionMode,
    CanonicalInstrument,
    GoldSymbolConfiguration,
    resolve_gold_instrument,
)
from axq.runtime.journal import JournalRecord, JournalRecordType

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)


class ExactSymbolGateway:
    def __init__(self, available: tuple[str, ...]) -> None:
        self.available = set(available)
        self.checked: list[str] = []
        self.mutations = 0

    def symbol_info(self, symbol: str) -> dict[str, object] | None:
        self.checked.append(symbol)
        return {"name": symbol, "point": 0.01} if symbol in self.available else None

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        del symbol, enabled
        self.mutations += 1
        raise AssertionError("symbol resolution must not select symbols")


def test_single_symbol_mode_checks_only_the_exact_configured_name() -> None:
    gateway = ExactSymbolGateway(("XAUUSD", "XAUUSD.sc"))
    config = GoldSymbolConfiguration.single("XAUUSD.sc")

    resolved = resolve_gold_instrument(gateway, config, resolved_at=NOW)  # type: ignore[arg-type]

    assert config.mode is BrokerSymbolSelectionMode.SINGLE
    assert resolved.canonical_instrument is CanonicalInstrument.XAUUSD
    assert resolved.resolved_broker_symbol == "XAUUSD.sc"
    assert resolved.checked_broker_symbols == ("XAUUSD.sc",)
    assert resolved.point_size == 0.01
    assert gateway.checked == ["XAUUSD.sc"]
    assert gateway.mutations == 0


def test_single_symbol_mode_never_falls_back() -> None:
    gateway = ExactSymbolGateway(("XAUUSD",))
    config = GoldSymbolConfiguration.single("XAUUSD.sc")

    with pytest.raises(ValueError, match="none of the explicitly configured"):
        resolve_gold_instrument(gateway, config, resolved_at=NOW)  # type: ignore[arg-type]

    assert gateway.checked == ["XAUUSD.sc"]


def test_alias_mode_uses_configured_priority_and_stops_after_first_exact_match() -> None:
    gateway = ExactSymbolGateway(("XAUUSD.sc", "GOLD", "XAUUSD.crp"))
    config = GoldSymbolConfiguration.aliases(("XAUUSD", "XAUUSD.sc", "GOLD"))

    resolved = resolve_gold_instrument(gateway, config, resolved_at=NOW)  # type: ignore[arg-type]

    assert config.mode is BrokerSymbolSelectionMode.ORDERED_ALLOWLIST
    assert resolved.resolved_broker_symbol == "XAUUSD.sc"
    assert resolved.checked_broker_symbols == ("XAUUSD", "XAUUSD.sc")
    assert gateway.checked == ["XAUUSD", "XAUUSD.sc"]


def test_alias_mode_never_checks_or_accepts_an_unconfigured_variant() -> None:
    gateway = ExactSymbolGateway(("XAUUSD.crp",))
    config = GoldSymbolConfiguration.aliases(("XAUUSD", "XAUUSD.sc", "GOLD"))

    with pytest.raises(ValueError, match="none of the explicitly configured"):
        resolve_gold_instrument(gateway, config, resolved_at=NOW)  # type: ignore[arg-type]

    assert gateway.checked == ["XAUUSD", "XAUUSD.sc", "GOLD"]
    assert "XAUUSD.crp" not in gateway.checked
    assert gateway.mutations == 0


def test_alias_list_rejects_duplicates_and_non_utc_resolution_time() -> None:
    with pytest.raises(ValueError, match="unique"):
        GoldSymbolConfiguration.aliases(("XAUUSD", "XAUUSD"))
    config = GoldSymbolConfiguration.aliases(("XAUUSD", "GOLD"))

    with pytest.raises(ValueError, match="timezone-aware"):
        resolve_gold_instrument(  # type: ignore[arg-type]
            ExactSymbolGateway(("XAUUSD",)),
            config,
            resolved_at=datetime(2026, 9, 14, 12, 0),
        )


def test_resolved_identity_is_journal_ready_and_excludes_operational_time() -> None:
    gateway = ExactSymbolGateway(("XAUUSD.sc",))
    config = GoldSymbolConfiguration.aliases(("XAUUSD", "XAUUSD.sc", "GOLD"))
    first = resolve_gold_instrument(gateway, config, resolved_at=NOW)  # type: ignore[arg-type]
    second = first.model_copy(update={"available_at": NOW.replace(minute=1)})

    record = JournalRecord.from_semantic(first, event_id=None)

    assert first.resolution_id == second.resolution_id
    assert record.record_type is JournalRecordType.INSTRUMENT_RESOLUTION
    assert record.semantic_id == first.resolution_id


def test_resolver_has_no_discovery_selection_or_fuzzy_boundary() -> None:
    tree = ast.parse(Path("src/axq/mt5/symbols.py").read_text(encoding="utf-8"))
    attributes = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }

    assert not attributes & {"symbols_get", "symbol_select"}
