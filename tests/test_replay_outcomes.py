from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axq.replay_validation import ReplayClosedTrade, ReplayFill, ReplaySide
from axq.replay_validation.outcomes import (
    ReplayActionApplication,
    ReplayEventContext,
    ReplayFillOutcome,
    ReplayOutcomeArtifact,
    ReplayTradeOutcome,
)

T0 = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _artifact() -> ReplayOutcomeArtifact:
    return ReplayOutcomeArtifact(
        source_metrics_id="replay-metrics-1",
        input_sha256="a" * 64,
        entry_model="NEXT_M5_OPEN_V1",
        stop_model="CAUSAL_BAR_TOUCH_V1",
        spread_model="HALF_RECORDED_SPREAD_EACH_SIDE_V1",
        slippage_points=1.0,
        fills=(
            ReplayFillOutcome(
                replay_fill_id="rfill-1",
                execution_intent_id="xi-1",
                execution_result_id="xr-1",
                position_id="rpos-1",
                direction="BUY",
                volume_lots=0.1,
                fill_price=2500.0,
                executed_at=T0,
            ),
        ),
        trades=(
            ReplayTradeOutcome(
                replay_trade_id="rtrade-1",
                source_execution_intent_id="xi-1",
                position_id="rpos-1",
                direction="BUY",
                volume_lots=0.1,
                opened_at=T0,
                closed_at=T0 + timedelta(minutes=15),
                entry_price=2500.0,
                exit_price=2499.0,
                initial_stop_loss=2499.0,
                exit_reason="POSITION_ACTION_CLOSE",
                source_position_action_intent_id="pai-1",
                mfe_points=0.0,
                mae_points=100.0,
            ),
        ),
        action_applications=(
            ReplayActionApplication(
                position_action_intent_id="pai-1",
                position_id="rpos-1",
                action_type="CLOSE_POSITION",
                applied_at=T0 + timedelta(minutes=15),
            ),
        ),
        event_contexts=(
            ReplayEventContext(
                runtime_event_id="ev-1",
                available_at=T0,
                session="LONDON",
                regime=None,
            ),
        ),
    )


def test_replay_outcome_artifact_is_deterministic_and_serializable(tmp_path) -> None:
    first = _artifact()
    second = _artifact()
    path = tmp_path / "replay-outcomes.json"

    first.write(path)

    assert first.artifact_id == second.artifact_id
    assert ReplayOutcomeArtifact.read(path) == first
    assert path.read_bytes().endswith(b"\n")


def test_trade_preserves_exact_close_action_and_none_vs_zero() -> None:
    trade = _artifact().trades[0]
    event_context = _artifact().event_contexts[0]

    assert trade.source_position_action_intent_id == "pai-1"
    assert trade.mfe_points == 0.0
    assert event_context.regime is None


def test_source_records_convert_existing_replay_semantics_without_reidentifying() -> None:
    fill = ReplayFill(
        instruction_id="xi-1",
        position_id="rpos-1",
        side=ReplaySide.BUY,
        volume_lots=0.1,
        price=2500.0,
        executed_at=T0,
    )
    trade = ReplayClosedTrade(
        position_id="rpos-1",
        source_intent_id="xi-1",
        side=ReplaySide.BUY,
        volume_lots=0.1,
        opened_at=T0,
        closed_at=T0 + timedelta(minutes=15),
        entry_price=2500.0,
        exit_price=2499.0,
        initial_stop_loss=2499.0,
        exit_reason="POSITION_ACTION_CLOSE",
        executed_at=T0 + timedelta(minutes=15),
        mfe_points=0.0,
        mae_points=100.0,
    )

    fill_record = ReplayFillOutcome.from_replay(fill, execution_result_id="xr-1")
    trade_record = ReplayTradeOutcome.from_replay(
        trade,
        source_position_action_intent_id="pai-1",
    )

    assert fill_record.replay_fill_id == fill.semantic_id
    assert fill_record.execution_intent_id == fill.instruction_id
    assert trade_record.replay_trade_id == trade.semantic_id
    assert trade_record.source_position_action_intent_id == "pai-1"
