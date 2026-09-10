"""Deterministic, transport-only fill mechanics for system replay."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from axq.versioning import canonical_hash

ENTRY_MODEL = "NEXT_M5_OPEN_V1"
STOP_MODEL = "CAUSAL_BAR_TOUCH_V1"
SPREAD_MODEL = "HALF_RECORDED_SPREAD_EACH_SIDE_V1"


class ReplaySide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


def _identity(prefix: str, value: object) -> str:
    return f"{prefix}-{canonical_hash(value)[:20]}"


@dataclass(frozen=True)
class ReplayBar:
    opened_at: datetime
    available_at: datetime
    open: float
    high: float
    low: float
    close: float
    spread_points: float

    def __post_init__(self) -> None:
        if self.opened_at.tzinfo is None or self.available_at.tzinfo is None:
            raise ValueError("replay bars require timezone-aware timestamps")
        if self.available_at <= self.opened_at:
            raise ValueError("bar availability must follow its open")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("invalid OHLC envelope")
        if self.low > self.high or self.spread_points < 0:
            raise ValueError("invalid replay bar")


@dataclass(frozen=True)
class PendingReplayEntry:
    intent_id: str
    direction: ReplaySide
    volume_lots: float
    stop_loss: float
    decision_available_at: datetime
    setup_id: str | None = None
    thesis_id: str | None = None
    scenario_id: str | None = None


@dataclass(frozen=True)
class ReplayFill:
    instruction_id: str
    position_id: str
    side: ReplaySide
    volume_lots: float
    price: float
    executed_at: datetime
    model: str = ENTRY_MODEL

    @property
    def semantic_id(self) -> str:
        return _identity("rfill", self)


@dataclass(frozen=True)
class ReplayPosition:
    position_id: str
    source_intent_id: str
    side: ReplaySide
    volume_lots: float
    opened_at: datetime
    open_price: float
    initial_stop_loss: float
    stop_loss: float
    stop_active_after: datetime
    setup_id: str | None = None
    thesis_id: str | None = None
    scenario_id: str | None = None
    mfe_points: float = 0.0
    mae_points: float = 0.0


@dataclass(frozen=True)
class ReplayClosedTrade:
    position_id: str
    source_intent_id: str
    side: ReplaySide
    volume_lots: float
    opened_at: datetime
    closed_at: datetime
    entry_price: float
    exit_price: float
    initial_stop_loss: float
    exit_reason: str
    executed_at: datetime
    mfe_points: float
    mae_points: float

    @property
    def semantic_id(self) -> str:
        return _identity("rtrade", self)


@dataclass(frozen=True)
class ReplayBarResult:
    fills: tuple[ReplayFill, ...] = ()
    closed_trades: tuple[ReplayClosedTrade, ...] = ()
    applied_action_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class _PendingStop:
    position_id: str
    stop_loss: float
    decision_available_at: datetime
    action_intent_id: str


@dataclass(frozen=True)
class _PendingClose:
    position_id: str
    decision_available_at: datetime
    action_intent_id: str


class ReplayExecutionBook:
    """A causal fill book; it contains no signal or policy decisions."""

    def __init__(self, *, point_size: float, slippage_points: float) -> None:
        if point_size <= 0 or slippage_points < 0:
            raise ValueError("invalid replay execution convention")
        self.point_size = point_size
        self.slippage_points = slippage_points
        self._entries: list[PendingReplayEntry] = []
        self._stops: list[_PendingStop] = []
        self._closes: list[_PendingClose] = []
        self._positions: dict[str, ReplayPosition] = {}
        self._seen_instructions: set[str] = set()

    @property
    def positions(self) -> tuple[ReplayPosition, ...]:
        return tuple(self._positions[key] for key in sorted(self._positions))

    def queue_entry(self, entry: PendingReplayEntry) -> bool:
        if entry.intent_id in self._seen_instructions:
            return False
        self._seen_instructions.add(entry.intent_id)
        self._entries.append(entry)
        return True

    def queue_stop_change(
        self,
        *,
        position_id: str,
        stop_loss: float,
        decision_available_at: datetime,
        action_intent_id: str,
    ) -> bool:
        if action_intent_id in self._seen_instructions:
            return False
        self._seen_instructions.add(action_intent_id)
        self._stops.append(
            _PendingStop(position_id, stop_loss, decision_available_at, action_intent_id)
        )
        return True

    def queue_close(
        self,
        *,
        position_id: str,
        decision_available_at: datetime,
        action_intent_id: str,
    ) -> bool:
        if action_intent_id in self._seen_instructions:
            return False
        self._seen_instructions.add(action_intent_id)
        self._closes.append(_PendingClose(position_id, decision_available_at, action_intent_id))
        return True

    def _price(self, mid: float, spread: float, *, buying: bool) -> float:
        adjustment = spread * self.point_size / 2 + self.slippage_points * self.point_size
        return round(mid + adjustment if buying else mid - adjustment, 10)

    def process_bar(self, bar: ReplayBar) -> ReplayBarResult:
        fills: list[ReplayFill] = []
        closed: list[ReplayClosedTrade] = []
        applied: list[str] = []

        remaining_entries: list[PendingReplayEntry] = []
        for entry in self._entries:
            if entry.decision_available_at > bar.opened_at:
                remaining_entries.append(entry)
                continue
            buying = entry.direction is ReplaySide.BUY
            price = self._price(bar.open, bar.spread_points, buying=buying)
            position_id = _identity("rpos", {"intent_id": entry.intent_id})
            self._positions[position_id] = ReplayPosition(
                position_id=position_id,
                source_intent_id=entry.intent_id,
                side=entry.direction,
                volume_lots=entry.volume_lots,
                opened_at=bar.opened_at,
                open_price=price,
                initial_stop_loss=entry.stop_loss,
                stop_loss=entry.stop_loss,
                stop_active_after=bar.available_at,
                setup_id=entry.setup_id,
                thesis_id=entry.thesis_id,
                scenario_id=entry.scenario_id,
            )
            fills.append(
                ReplayFill(
                    instruction_id=entry.intent_id,
                    position_id=position_id,
                    side=entry.direction,
                    volume_lots=entry.volume_lots,
                    price=price,
                    executed_at=bar.opened_at,
                )
            )
        self._entries = remaining_entries

        remaining_stops: list[_PendingStop] = []
        for stop_action in self._stops:
            if stop_action.decision_available_at > bar.opened_at:
                remaining_stops.append(stop_action)
                continue
            position = self._positions.get(stop_action.position_id)
            if position is not None:
                self._positions[stop_action.position_id] = replace(
                    position,
                    stop_loss=stop_action.stop_loss,
                    stop_active_after=bar.available_at,
                )
                applied.append(stop_action.action_intent_id)
        self._stops = remaining_stops

        remaining_closes: list[_PendingClose] = []
        for close_action in self._closes:
            if close_action.decision_available_at > bar.opened_at:
                remaining_closes.append(close_action)
                continue
            position = self._positions.pop(close_action.position_id, None)
            if position is not None:
                closed.append(self._close(position, bar, bar.open, "POSITION_ACTION_CLOSE"))
                applied.append(close_action.action_intent_id)
        self._closes = remaining_closes

        for position_id, position in tuple(self._positions.items()):
            favorable = (
                (bar.high - position.open_price) / self.point_size
                if position.side is ReplaySide.BUY
                else (position.open_price - bar.low) / self.point_size
            )
            adverse = (
                (position.open_price - bar.low) / self.point_size
                if position.side is ReplaySide.BUY
                else (bar.high - position.open_price) / self.point_size
            )
            position = replace(
                position,
                mfe_points=max(position.mfe_points, favorable),
                mae_points=max(position.mae_points, adverse),
            )
            self._positions[position_id] = position
            if position.stop_active_after >= bar.available_at:
                continue
            touched = (
                bar.low <= position.stop_loss
                if position.side is ReplaySide.BUY
                else bar.high >= position.stop_loss
            )
            if touched:
                mid = (
                    min(bar.open, position.stop_loss)
                    if position.side is ReplaySide.BUY
                    else max(bar.open, position.stop_loss)
                )
                self._positions.pop(position_id)
                closed.append(self._close(position, bar, mid, "PROTECTIVE_STOP"))
        return ReplayBarResult(tuple(fills), tuple(closed), tuple(applied))

    def _close(
        self, position: ReplayPosition, bar: ReplayBar, mid: float, reason: str
    ) -> ReplayClosedTrade:
        exit_price = self._price(
            mid,
            bar.spread_points,
            buying=position.side is ReplaySide.SELL,
        )
        return ReplayClosedTrade(
            position_id=position.position_id,
            source_intent_id=position.source_intent_id,
            side=position.side,
            volume_lots=position.volume_lots,
            opened_at=position.opened_at,
            closed_at=bar.available_at,
            entry_price=position.open_price,
            exit_price=exit_price,
            initial_stop_loss=position.initial_stop_loss,
            exit_reason=reason,
            executed_at=bar.available_at,
            mfe_points=position.mfe_points,
            mae_points=position.mae_points,
        )
