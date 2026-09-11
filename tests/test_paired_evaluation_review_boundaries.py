from __future__ import annotations

from pathlib import Path

REVIEW_MODULES = (
    "src/axq/reflection/paired_evaluation_review_contracts.py",
    "src/axq/reflection/paired_evaluation_review_store.py",
    "src/axq/reflection/paired_evaluation_review_cli.py",
)


def test_review_bridge_has_no_execution_final_oos_or_broker_boundary() -> None:
    combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in REVIEW_MODULES)
    forbidden = (
        "MetaTrader5",
        "order_send",
        "run_system_replay",
        "FINAL_OOS",
        "append_transition",
        "execute_paired_evaluation",
    )
    for token in forbidden:
        assert token not in combined
