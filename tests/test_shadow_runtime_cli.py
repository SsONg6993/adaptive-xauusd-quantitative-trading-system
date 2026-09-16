from __future__ import annotations

import pytest

from axq.mt5 import BrokerSymbolSelectionMode
from axq.orchestration import shadow_runtime
from axq.orchestration.shadow_runtime import (
    build_argument_parser,
    managed_control_configuration,
    symbol_configuration,
)


def test_shadow_cli_single_symbol_and_alias_modes_are_mutually_exclusive() -> None:
    parser = build_argument_parser()
    single = parser.parse_args(
        ["--broker-symbol", "XAUUSD.sc", "--output-dir", "runtime/shadow", "--once"]
    )
    aliases = parser.parse_args(
        [
            "--gold-symbols",
            "XAUUSD,XAUUSD.sc,GOLD",
            "--output-dir",
            "runtime/shadow",
            "--once",
        ]
    )

    single_config = symbol_configuration(single.broker_symbol, single.gold_symbols)
    alias_config = symbol_configuration(aliases.broker_symbol, aliases.gold_symbols)

    assert single_config.mode is BrokerSymbolSelectionMode.SINGLE
    assert single_config.broker_symbols == ("XAUUSD.sc",)
    assert alias_config.mode is BrokerSymbolSelectionMode.ORDERED_ALLOWLIST
    assert alias_config.broker_symbols == ("XAUUSD", "XAUUSD.sc", "GOLD")
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--broker-symbol",
                "XAUUSD.sc",
                "--gold-symbols",
                "XAUUSD,GOLD",
                "--output-dir",
                "runtime/shadow",
            ]
        )


def test_managed_runtime_identity_and_control_database_must_be_supplied_together() -> None:
    with pytest.raises(ValueError, match="together"):
        managed_control_configuration("instance-only", None)
    with pytest.raises(ValueError, match="together"):
        managed_control_configuration(None, "runtime/control.sqlite3")
    assert managed_control_configuration(None, None) is None
    configured = managed_control_configuration(
        "instance-a", "runtime/live-shadow/shadow-control.sqlite3"
    )
    assert configured is not None
    assert configured[0] == "instance-a"


def test_live_poll_refreshes_before_source_constructs_event() -> None:
    calls: list[str] = []

    class Orchestrator:
        def refresh_snapshot_if_due(self) -> bool:
            calls.append("refresh")
            return True

    class Source:
        def poll(self) -> object:
            calls.append("poll")
            return object()

    poll = shadow_runtime._poll_after_recovery_refresh(Orchestrator(), Source())  # type: ignore[arg-type]

    assert poll is not None
    assert calls == ["refresh", "poll"]
