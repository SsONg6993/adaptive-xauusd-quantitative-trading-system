from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from axq.experience import (
    AttributionStatus,
    ExperienceProvenance,
    RejectedDecisionExperience,
    RejectionLayer,
    TradeExperience,
)
from axq.experience.__main__ import main
from axq.experience.analytics import summarize_experiences
from axq.experience.store import SQLiteExperienceStore
from axq.schemas import Signal

T0 = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _trade(*, pnl: float, direction: Signal, suffix: str) -> TradeExperience:
    return TradeExperience(
        occurred_at=T0 + timedelta(hours=int(suffix)),
        available_at=T0 + timedelta(hours=int(suffix)),
        symbol="XAUUSD",
        session="LONDON",
        outcome="PROTECTIVE_STOP",
        provenance=ExperienceProvenance(replay_trade_ids=(f"trade-{suffix}",)),
        replay_trade_id=f"trade-{suffix}",
        execution_intent_id=f"intent-{suffix}",
        execution_result_id=f"result-{suffix}",
        replay_fill_id=f"fill-{suffix}",
        position_id=f"position-{suffix}",
        direction=direction,
        entry_time=T0,
        exit_time=T0 + timedelta(minutes=30),
        entry_price=2500.0,
        exit_price=2501.0,
        volume_lots=0.1,
        realized_pnl=pnl,
        r_outcome=pnl / 10.0,
        mfe_points=20.0,
        mae_points=5.0,
        holding_seconds=1800.0,
        exit_cause="PROTECTIVE_STOP",
        stop_triggered=True,
        explicit_position_exit=False,
    )


def _rejection() -> RejectedDecisionExperience:
    return RejectedDecisionExperience(
        occurred_at=T0,
        available_at=T0,
        symbol=None,
        outcome="DISCIPLINE",
        attribution_status=AttributionStatus.INCOMPLETE,
        missing_links=("RUNTIME_EVENT_SYMBOL:ev-1",),
        provenance=ExperienceProvenance(master_proposal_ids=("mp-1",)),
        rejection_layer=RejectionLayer.DISCIPLINE,
        source_proposal_id="mp-1",
        source_outcome_id="do-1",
        reason_codes=("COOLDOWN_ACTIVE",),
        master_confidence=0.8,
    )


def test_summary_is_descriptive_and_preserves_unknowns() -> None:
    summary = summarize_experiences(
        (_trade(pnl=10.0, direction=Signal.BUY, suffix="1"),
         _trade(pnl=-5.0, direction=Signal.SELL, suffix="2"),
         _rejection())
    )

    assert summary.total_experiences == 3
    assert summary.incomplete_attributions == 1
    assert summary.trade_count == 2
    assert summary.trade_direction_counts == {"BUY": 1, "SELL": 1}
    assert summary.realized_pnl == 5.0
    assert summary.win_rate == 0.5
    assert summary.profit_factor == 2.0
    assert summary.rejection_reason_counts == {"COOLDOWN_ACTIVE": 1}


def test_show_and_summary_cli_emit_json(tmp_path, capsys) -> None:
    path = tmp_path / "experiences.sqlite3"
    store = SQLiteExperienceStore(path)
    store.append_many((_trade(pnl=10.0, direction=Signal.BUY, suffix="1"), _rejection()))

    assert main(["show-experiences", "--store", str(path), "--type", "TRADE"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert [item["experience_type"] for item in shown] == ["TRADE"]

    assert main(["summary", "--store", str(path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["trade_count"] == 1
    assert summary["incomplete_attributions"] == 1
