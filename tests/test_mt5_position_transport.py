from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from axq.execution_boundary import ExecutionMode, ExecutionResultStatus
from axq.mt5 import MT5Constants, MT5SymbolMapping
from axq.mt5.position import MT5PositionActionAdapter
from axq.position_actions import PositionActionIntent, PositionActionReason, PositionActionType
from axq.position_actions.persistence import SQLitePositionActionTransportLedger
from axq.position_actions.transport import (
    InMemoryPositionActionTransportLedger,
    position_action_result_to_runtime_event,
)
from axq.runtime import PositionSide, RuntimeEventType
from axq.runtime.journal import JournalRecord, JournalRecordType

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _constants() -> MT5Constants:
    return MT5Constants(
        account_trade_mode_demo=0,
        account_trade_mode_contest=1,
        account_trade_mode_real=2,
        symbol_trade_mode_disabled=0,
        position_type_buy=0,
        position_type_sell=1,
        order_type_buy=0,
        order_type_sell=1,
        order_type_buy_limit=2,
        order_type_sell_limit=3,
        order_type_buy_stop=4,
        order_type_sell_stop=5,
        order_type_buy_stop_limit=6,
        order_type_sell_stop_limit=7,
        trade_action_deal=1,
        trade_action_sltp=6,
        order_time_gtc=0,
        order_filling_ioc=1,
        trade_retcode_requote=10004,
        trade_retcode_placed=10008,
        trade_retcode_done=10009,
        trade_retcode_done_partial=10010,
    )


class PositionGateway:
    constants = _constants()

    def __init__(
        self,
        *,
        side: PositionSide = PositionSide.BUY,
        trade_mode: int = 0,
        send=...,
    ) -> None:
        self.side = side
        self.trade_mode = trade_mode
        self.send = {
            "retcode": 10009,
            "deal": 8001,
            "order": 0,
            "volume": 0.05,
            "price": 2510.0,
            "comment": "done",
        } if send is ... else send
        self.check_requests: list[dict[str, object]] = []
        self.send_requests: list[dict[str, object]] = []
        self.position_volume = 0.05
        self.position_stop = 2490.0 if side is PositionSide.BUY else 2510.0

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def last_error(self):
        return (0, "ok")

    def terminal_info(self):
        return {"connected": True, "trade_allowed": True}

    def account_info(self):
        return {
            "trade_mode": self.trade_mode,
            "trade_allowed": True,
            "trade_expert": True,
        }
    def symbol_select(self, symbol, enabled):
        return symbol == "XAUUSD.demo" and enabled

    def symbol_info(self, symbol):
        return {
            "name": symbol, "trade_mode": 4, "point": 0.01,
            "trade_tick_size": 0.01, "trade_stops_level": 20,
            "trade_freeze_level": 10, "volume_min": 0.01,
            "volume_max": 100.0, "volume_step": 0.01,
        }
    def symbol_info_tick(self, symbol):
        return {
            "time_msc": int(T0.timestamp() * 1000),
            "bid": 2510.0, "ask": 2510.2, "last": 2510.1,
        }
    def positions_get(self, symbol=None):
        return ({
            "ticket": 123, "symbol": "XAUUSD.demo",
            "type": 0 if self.side is PositionSide.BUY else 1,
            "volume": self.position_volume, "sl": self.position_stop, "tp": 2520.0,
        },)
    def orders_get(self, symbol=None):
        return ()

    def order_check(self, request):
        self.check_requests.append(dict(request))
        return {"retcode": 0, "comment": "ok"}
    def order_send(self, request):
        self.send_requests.append(dict(request))
        if isinstance(self.send, Exception):
            raise self.send
        return self.send


def _intent(action: PositionActionType, *, side=PositionSide.BUY) -> PositionActionIntent:
    protective = action is PositionActionType.MODIFY_PROTECTIVE_STOP
    return PositionActionIntent(
        policy_id="pap", safety_outcome_id="pas", position_management_outcome_id="pmo",
        position_id="pos-exact", broker_ticket=123,
        original_execution_intent_id="xi", original_execution_result_id="xe",
        broker_intent_link_id="bil", reconciliation_report_id="rr",
        resume_readiness_id="ready", setup_id="setup", thesis_id="thesis",
        scenario_id="scenario", action_type=action, symbol="XAUUSD",
        position_side=side, current_volume_lots=0.05,
        requested_close_volume_lots=None if protective else 0.05,
        existing_stop_loss=2490.0 if side is PositionSide.BUY else 2510.0,
        requested_new_stop_loss=(2500.0 if side is PositionSide.BUY else 2500.0)
        if protective else None,
        audit_reason_codes=(
            PositionActionReason.MODIFY_PROTECTIVE_STOP_SAFE if protective
            else PositionActionReason.CLOSE_POSITION_SAFE,
        ),
        as_of=T0, available_at=T0,
    )


def _adapter(mode, gateway, ledger=None):
    return MT5PositionActionAdapter(
        mode=mode,
        ledger=ledger or InMemoryPositionActionTransportLedger(),
        gateway=gateway,
        symbol_mapping=MT5SymbolMapping(
            internal_symbol="XAUUSD", broker_symbol="XAUUSD.demo"
        ),
        clock=lambda: T0 + timedelta(seconds=1),
        kill_switch=lambda: False,
    )


def test_disabled_is_zero_touch_and_dry_run_checks_without_send() -> None:
    disabled_gateway = PositionGateway()
    disabled = _adapter(ExecutionMode.DISABLED, disabled_gateway).execute(
        _intent(PositionActionType.CLOSE_POSITION)
    )
    assert disabled.status is ExecutionResultStatus.NO_ACTION
    assert disabled_gateway.check_requests == disabled_gateway.send_requests == []

    dry_gateway = PositionGateway()
    dry = _adapter(ExecutionMode.DRY_RUN, dry_gateway).execute(
        _intent(PositionActionType.MODIFY_PROTECTIVE_STOP)
    )
    assert dry.status is ExecutionResultStatus.NO_ACTION
    assert len(dry_gateway.check_requests) == 1
    assert dry_gateway.send_requests == []


@pytest.mark.parametrize("trade_mode", [1, 2, 999])
def test_position_transport_rejects_non_demo_account(trade_mode: int) -> None:
    gateway = PositionGateway(trade_mode=trade_mode)
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(PositionActionType.CLOSE_POSITION)
    )
    assert result.status is ExecutionResultStatus.FAILED
    assert gateway.check_requests == gateway.send_requests == []


def test_modify_stop_preserves_ticket_tp_and_cannot_increase_exposure() -> None:
    gateway = PositionGateway()
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(PositionActionType.MODIFY_PROTECTIVE_STOP)
    )
    request = gateway.send_requests[0]
    assert result.status is ExecutionResultStatus.FILLED
    assert request == gateway.check_requests[-1]
    assert request["action"] == 6
    assert request["position"] == 123
    assert request["sl"] == 2500.0
    assert request["tp"] == 2520.0
    assert "volume" not in request and "type" not in request


def test_close_is_exact_full_close_not_reversal() -> None:
    gateway = PositionGateway()
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(PositionActionType.CLOSE_POSITION)
    )
    request = gateway.send_requests[0]
    assert result.status is ExecutionResultStatus.FILLED
    assert request["position"] == 123
    assert request["type"] == 1
    assert request["volume"] == 0.05
    assert request["price"] == 2510.0


def test_send_rejection_is_authoritative_after_successful_checks() -> None:
    gateway = PositionGateway(
        send={
            "retcode": 10004,
            "deal": 0,
            "order": 0,
            "volume": 0.0,
            "price": 0.0,
            "comment": "requote",
        }
    )
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(PositionActionType.CLOSE_POSITION)
    )
    assert len(gateway.check_requests) == 2
    assert result.status is ExecutionResultStatus.REJECTED
    assert result.broker_retcode == "10004"


def test_second_submission_time_snapshot_can_block_mutation() -> None:
    gateway = PositionGateway()
    calls = 0
    original = gateway.positions_get

    def positions_get(symbol=None):
        nonlocal calls
        calls += 1
        values = original(symbol)
        if calls == 2:
            gateway.position_volume = 0.04
            return original(symbol)
        return values

    gateway.positions_get = positions_get  # type: ignore[method-assign]
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(PositionActionType.CLOSE_POSITION)
    )
    assert result.status is ExecutionResultStatus.FAILED
    assert gateway.send_requests == []


def test_exact_ticket_volume_and_stop_are_revalidated_before_send() -> None:
    for mutation in ("ticket", "volume", "stop"):
        gateway = PositionGateway()
        if mutation == "ticket":
            gateway.positions_get = lambda symbol=None: ()  # type: ignore[method-assign]
        elif mutation == "volume":
            gateway.position_volume = 0.04
        else:
            gateway.position_stop = 2495.0
        result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
            _intent(PositionActionType.CLOSE_POSITION)
        )
        assert result.status is ExecutionResultStatus.FAILED
        assert gateway.send_requests == []


@pytest.mark.parametrize(
    ("action", "send"),
    [
        (PositionActionType.CLOSE_POSITION, OSError("connection lost")),
        (PositionActionType.MODIFY_PROTECTIVE_STOP, None),
    ],
)
def test_unknown_action_submission_is_durable_and_never_resent(
    tmp_path, action: PositionActionType, send: object
) -> None:
    gateway = PositionGateway(send=send)
    database = tmp_path / "runtime.sqlite3"
    intent = _intent(action)
    first = _adapter(
        ExecutionMode.DEMO_ENABLED,
        gateway,
        SQLitePositionActionTransportLedger(database),
    ).execute(intent)
    second = _adapter(
        ExecutionMode.DEMO_ENABLED,
        gateway,
        SQLitePositionActionTransportLedger(database),
    ).execute(intent)
    assert first.status is ExecutionResultStatus.UNKNOWN
    assert second == first
    assert len(gateway.send_requests) == 1
    assert SQLitePositionActionTransportLedger(database).requires_reconciliation(
        intent.intent_id
    )

    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE position_action_transport_transitions SET intent_id = 'changed'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM position_action_transport_transitions")


def test_position_action_result_maps_to_canonical_runtime_feedback() -> None:
    result = _adapter(ExecutionMode.DEMO_ENABLED, PositionGateway()).execute(
        _intent(PositionActionType.CLOSE_POSITION)
    )
    event = position_action_result_to_runtime_event(
        result, source="mt5", source_version="1", source_sequence=9
    )
    assert event is not None
    assert event.event_type is RuntimeEventType.EXECUTION_FEEDBACK
    assert event.payload.instruction_id == result.position_action_intent_id
    record = JournalRecord.from_semantic(
        result,
        event_id=event.event_id,
        parent_id=result.position_id,
        previous_id=result.position_action_intent_id,
    )
    assert record.record_type is JournalRecordType.POSITION_ACTION_TRANSPORT_RESULT
    assert record.decode() == result
