from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axq.replay_validation import (
    PendingReplayEntry,
    ReplayBar,
    ReplayExecutionBook,
    ReplaySide,
)

T0 = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)


def _bar(offset: int, *, low: float = 2498.0, high: float = 2502.0) -> ReplayBar:
    opened_at = T0 + timedelta(minutes=5 * offset)
    return ReplayBar(
        opened_at=opened_at,
        available_at=opened_at + timedelta(minutes=5),
        open=2500.0,
        high=high,
        low=low,
        close=2501.0,
        spread_points=20.0,
    )


def test_entry_executes_at_next_m5_open_and_cannot_stop_on_fill_bar() -> None:
    book = ReplayExecutionBook(point_size=0.01, slippage_points=1.0)
    book.queue_entry(
        PendingReplayEntry(
            intent_id="intent-buy",
            direction=ReplaySide.BUY,
            volume_lots=0.1,
            stop_loss=2499.0,
            decision_available_at=_bar(0).available_at,
        )
    )

    assert book.process_bar(_bar(0)).fills == ()
    fill_bar = _bar(1, low=2490.0)
    result = book.process_bar(fill_bar)

    assert result.fills[0].executed_at == fill_bar.opened_at
    assert result.fills[0].price == 2500.11
    assert result.closed_trades == ()
    assert len(book.positions) == 1


def test_modified_stop_never_retroactively_triggers_in_modification_bar() -> None:
    book = ReplayExecutionBook(point_size=0.01, slippage_points=0.0)
    book.queue_entry(
        PendingReplayEntry(
            intent_id="intent-buy",
            direction=ReplaySide.BUY,
            volume_lots=0.1,
            stop_loss=2490.0,
            decision_available_at=_bar(0).available_at,
        )
    )
    book.process_bar(_bar(1))
    position_id = book.positions[0].position_id
    book.queue_stop_change(
        position_id=position_id,
        stop_loss=2499.5,
        decision_available_at=_bar(1).available_at,
        action_intent_id="protect-1",
    )

    changed = book.process_bar(_bar(2, low=2498.0))
    assert changed.closed_trades == ()
    assert book.positions[0].stop_loss == 2499.5

    stopped = book.process_bar(_bar(3, low=2498.0))
    assert stopped.closed_trades[0].exit_reason == "PROTECTIVE_STOP"
    assert stopped.closed_trades[0].executed_at == _bar(3).available_at


def test_identical_replay_books_produce_identical_semantic_ids() -> None:
    def run() -> tuple[str, ...]:
        book = ReplayExecutionBook(point_size=0.01, slippage_points=1.0)
        book.queue_entry(
            PendingReplayEntry(
                intent_id="intent-sell",
                direction=ReplaySide.SELL,
                volume_lots=0.1,
                stop_loss=2505.0,
                decision_available_at=_bar(0).available_at,
            )
        )
        first = book.process_bar(_bar(1))
        second = book.process_bar(_bar(2, high=2506.0))
        return tuple(
            item.semantic_id for item in (*first.fills, *second.fills, *second.closed_trades)
        )

    assert run() == run()
