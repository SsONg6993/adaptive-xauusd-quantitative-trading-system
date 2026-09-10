from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.execution_boundary import (
    ExecutionIntent,
    ExecutionMode,
    ExecutionOrderType,
    ExecutionPolicy,
    ExecutionReason,
    ExecutionResultStatus,
    InMemoryExecutionLedger,
    SQLiteExecutionLedger,
    default_execution_policy,
)
from axq.mt5 import MT5Constants, MT5SymbolMapping
from axq.mt5.entry import MT5ExecutionAdapter, default_mt5_transport_config
from axq.schemas import Signal

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


class EntryGateway:
    constants = _constants()

    def __init__(
        self,
        *,
        trade_mode: int = 0,
        connected: bool = True,
        trade_allowed: bool = True,
        tick_time: datetime = T0,
        check_retcode: int = 0,
        send_response: dict[str, object] | None | object = ...,
        send_error: Exception | None = None,
        volume_step: float = 0.01,
    ) -> None:
        self.trade_mode = trade_mode
        self.connected = connected
        self.trade_allowed = trade_allowed
        self.tick_time = tick_time
        self.check_retcode = check_retcode
        self.send_response = (
            {
                "retcode": 10009,
                "deal": 7001,
                "order": 6001,
                "volume": 0.05,
                "price": 2500.2,
                "comment": "filled",
            }
            if send_response is ...
            else send_response
        )
        self.send_error = send_error
        self.volume_step = volume_step
        self.connect_calls = 0
        self.check_requests: list[dict[str, object]] = []
        self.send_requests: list[dict[str, object]] = []

    def connect(self) -> None:
        self.connect_calls += 1

    def close(self) -> None:
        return None

    def last_error(self) -> object:
        return (0, "ok")

    def terminal_info(self):
        return {"connected": self.connected, "trade_allowed": self.trade_allowed}

    def account_info(self):
        return {
            "login": 1,
            "trade_mode": self.trade_mode,
            "trade_allowed": self.trade_allowed,
            "trade_expert": self.trade_allowed,
        }

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        return symbol == "XAUUSD.demo" and enabled

    def symbol_info(self, symbol: str):
        return {
            "name": symbol,
            "visible": True,
            "trade_mode": 4 if self.trade_allowed else 0,
            "digits": 2,
            "point": 0.01,
            "trade_tick_size": 0.01,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": self.volume_step,
            "trade_stops_level": 20,
            "trade_freeze_level": 10,
        }

    def symbol_info_tick(self, symbol: str):
        return {
            "symbol": symbol,
            "time_msc": int(self.tick_time.timestamp() * 1000),
            "bid": 2500.0,
            "ask": 2500.2,
            "last": 2500.1,
        }

    def positions_get(self, symbol: str | None = None):
        return ()

    def orders_get(self, symbol: str | None = None):
        return ()

    def order_check(self, request):
        copied = dict(request)
        self.check_requests.append(copied)
        return {"retcode": self.check_retcode, "comment": "check"}

    def order_send(self, request):
        copied = dict(request)
        self.send_requests.append(copied)
        if self.send_error is not None:
            raise self.send_error
        return self.send_response


def _policy(mode: ExecutionMode) -> ExecutionPolicy:
    base = default_execution_policy()
    return ExecutionPolicy.model_validate(
        base.model_dump() | {"policy_id": "", "mode": mode}
    )


def _intent(mode: ExecutionMode, *, direction: Signal = Signal.BUY) -> ExecutionIntent:
    policy = _policy(mode)
    return ExecutionIntent(
        evidence_bundle_id="eb-entry",
        master_proposal_id="mp-entry",
        discipline_outcome_id="do-entry",
        risk_outcome_id="ro-entry",
        risk_context_id="rc-entry",
        setup_id="setup-entry",
        thesis_id="thesis-entry",
        scenario_id="scenario-entry",
        symbol="XAUUSD",
        broker_symbol="XAUUSD.demo",
        broker_source="mt5-demo",
        point_size=0.01,
        direction=direction,
        approved_volume_lots=0.05,
        order_type=ExecutionOrderType.MARKET,
        requested_entry_price=2500.2 if direction is Signal.BUY else 2500.0,
        stop_loss_price=2490.0 if direction is Signal.BUY else 2510.0,
        take_profit_price=None,
        as_of=T0,
        available_at=T0,
        expires_at=T0 + timedelta(seconds=30),
        execution_policy_id=policy.policy_id,
        execution_policy_version=policy.policy_version,
        execution_mode=mode,
    )


def _adapter(
    mode: ExecutionMode,
    gateway: EntryGateway,
    *,
    ledger=None,
    kill_switch=lambda: False,
) -> MT5ExecutionAdapter:
    return MT5ExecutionAdapter(
        policy=_policy(mode),
        ledger=ledger or InMemoryExecutionLedger(),
        gateway=gateway,
        symbol_mapping=MT5SymbolMapping(
            internal_symbol="XAUUSD",
            broker_symbol="XAUUSD.demo",
        ),
        config=default_mt5_transport_config(),
        clock=lambda: T0 + timedelta(seconds=1),
        kill_switch=kill_switch,
    )


def test_execution_disabled_by_default_never_touches_gateway() -> None:
    gateway = EntryGateway()
    policy = default_execution_policy()
    result = _adapter(ExecutionMode.DISABLED, gateway).execute(_intent(policy.mode))

    assert policy.mode is ExecutionMode.DISABLED
    assert result.status is ExecutionResultStatus.NO_ACTION
    assert result.reason_code is ExecutionReason.EXECUTION_DISABLED
    assert gateway.connect_calls == 0
    assert gateway.check_requests == []
    assert gateway.send_requests == []


def test_dry_run_performs_order_check_but_never_order_send() -> None:
    gateway = EntryGateway()
    result = _adapter(ExecutionMode.DRY_RUN, gateway).execute(
        _intent(ExecutionMode.DRY_RUN)
    )

    assert result.status is ExecutionResultStatus.NO_ACTION
    assert result.reason_code is ExecutionReason.DRY_RUN
    assert len(gateway.check_requests) == 1
    assert gateway.send_requests == []


@pytest.mark.parametrize("trade_mode", [1, 2, 999])
def test_demo_enabled_rejects_contest_live_or_unknown_account(trade_mode: int) -> None:
    gateway = EntryGateway(trade_mode=trade_mode)
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(ExecutionMode.DEMO_ENABLED)
    )

    assert result.status is ExecutionResultStatus.REJECTED
    assert result.reason_code in {
        ExecutionReason.LIVE_ACCOUNT_BLOCKED,
        ExecutionReason.UNKNOWN_ACCOUNT_MODE,
    }
    assert gateway.check_requests == []
    assert gateway.send_requests == []


@pytest.mark.parametrize(
    ("direction", "broker_type", "price", "stop"),
    [
        (Signal.BUY, 0, 2500.2, 2490.0),
        (Signal.SELL, 1, 2500.0, 2510.0),
    ],
)
def test_valid_demo_entry_preserves_direction_volume_price_and_stop(
    direction: Signal,
    broker_type: int,
    price: float,
    stop: float,
) -> None:
    gateway = EntryGateway()
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(ExecutionMode.DEMO_ENABLED, direction=direction)
    )

    assert result.status is ExecutionResultStatus.FILLED
    assert result.direction is direction
    assert len(gateway.check_requests) == 2
    assert len(gateway.send_requests) == 1
    request = gateway.send_requests[0]
    assert request["action"] == 1
    assert request["symbol"] == "XAUUSD.demo"
    assert request["type"] == broker_type
    assert request["volume"] == 0.05
    assert request["price"] == price
    assert request["sl"] == stop
    assert "tp" not in request
    assert request["comment"] == _intent(
        ExecutionMode.DEMO_ENABLED, direction=direction
    ).intent_id


def test_order_check_pass_does_not_override_order_send_rejection() -> None:
    gateway = EntryGateway(
        send_response={
            "retcode": 10004,
            "deal": 0,
            "order": 0,
            "volume": 0.0,
            "price": 0.0,
            "comment": "requote",
        }
    )
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(ExecutionMode.DEMO_ENABLED)
    )

    assert len(gateway.check_requests) == 2
    assert len(gateway.send_requests) == 1
    assert result.status is ExecutionResultStatus.REJECTED
    assert result.reason_code is ExecutionReason.BROKER_REJECTED
    assert result.broker_retcode == "10004"


def test_broker_partial_fill_maps_without_resubmitting_remainder() -> None:
    gateway = EntryGateway(
        send_response={
            "retcode": 10010,
            "deal": 7002,
            "order": 6002,
            "volume": 0.02,
            "price": 2500.2,
            "comment": "partial",
        }
    )
    adapter = _adapter(ExecutionMode.DEMO_ENABLED, gateway)
    intent = _intent(ExecutionMode.DEMO_ENABLED)

    first = adapter.execute(intent)
    second = adapter.execute(intent)

    assert first.status is ExecutionResultStatus.PARTIALLY_FILLED
    assert first.filled_volume_lots == 0.02
    assert first.remaining_volume_lots == 0.03
    assert second == first
    assert len(gateway.send_requests) == 1


def test_missing_send_acknowledgement_is_unknown_and_never_resent_after_restart(
    tmp_path,
) -> None:
    database = tmp_path / "runtime.sqlite3"
    gateway = EntryGateway(send_response=None)
    intent = _intent(ExecutionMode.DEMO_ENABLED)
    first = _adapter(
        ExecutionMode.DEMO_ENABLED,
        gateway,
        ledger=SQLiteExecutionLedger(database),
    ).execute(intent)
    second = _adapter(
        ExecutionMode.DEMO_ENABLED,
        gateway,
        ledger=SQLiteExecutionLedger(database),
    ).execute(intent)

    assert first.status is ExecutionResultStatus.UNKNOWN
    assert first.reason_code is ExecutionReason.UNKNOWN_SUBMISSION
    assert second == first
    assert len(gateway.send_requests) == 1


def test_order_send_exception_after_mutation_boundary_becomes_unknown() -> None:
    gateway = EntryGateway(send_error=OSError("connection dropped"))
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(ExecutionMode.DEMO_ENABLED)
    )

    assert result.status is ExecutionResultStatus.UNKNOWN
    assert result.reason_code is ExecutionReason.UNKNOWN_SUBMISSION


@pytest.mark.parametrize(
    ("gateway", "expected_reason"),
    [
        (EntryGateway(trade_allowed=False), ExecutionReason.TRANSPORT_FAILED),
        (
            EntryGateway(tick_time=T0 - timedelta(minutes=1)),
            ExecutionReason.OBSERVATION_STALE,
        ),
        (EntryGateway(volume_step=0.03), ExecutionReason.TRANSPORT_FAILED),
    ],
)
def test_stale_trade_disabled_or_invalid_constraints_block_mutation(
    gateway: EntryGateway,
    expected_reason: ExecutionReason,
) -> None:
    result = _adapter(ExecutionMode.DEMO_ENABLED, gateway).execute(
        _intent(ExecutionMode.DEMO_ENABLED)
    )

    assert result.status in {ExecutionResultStatus.REJECTED, ExecutionResultStatus.FAILED}
    assert result.reason_code is expected_reason
    assert gateway.send_requests == []


def test_kill_switch_blocks_before_order_check_or_send() -> None:
    gateway = EntryGateway()
    result = _adapter(
        ExecutionMode.DEMO_ENABLED,
        gateway,
        kill_switch=lambda: True,
    ).execute(_intent(ExecutionMode.DEMO_ENABLED))

    assert result.status is ExecutionResultStatus.FAILED
    assert gateway.check_requests == []
    assert gateway.send_requests == []
