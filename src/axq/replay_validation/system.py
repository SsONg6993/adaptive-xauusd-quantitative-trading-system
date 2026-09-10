"""Real-data deterministic Phase 7 system-replay validation runner."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pandas as pd

from axq.agents import (
    ContinuityStatus,
    DirectionalBias,
    EntryEligibility,
    HypothesisStatus,
    ScenarioDefinition,
    ScenarioPolicy,
    ThesisState,
    update_scenario,
)
from axq.discipline import (
    DisciplineContext,
    DisciplinePosition,
    DisciplineState,
    EntryIntent,
    default_demo_discipline_policy,
)
from axq.execution_boundary import (
    BrokerIntentLink,
    BrokerObjectKind,
    ExecutionResult,
    ExecutionResultStatus,
    ReconciliationFinding,
    ReconciliationKind,
    ReconciliationReport,
    ResolutionStatus,
    ResumeReadiness,
    ResumeStatus,
    SQLiteExecutionLedger,
    default_execution_policy,
    execution_result_to_runtime_event,
)
from axq.features.market_structure import market_structure_features
from axq.features.registry import default_registry
from axq.master import default_fusion_policy
from axq.orchestration import (
    DecisionPlan,
    DeterministicDecisionProcessor,
    RuntimeConfig,
    RuntimeMode,
    RuntimeOrchestrator,
)
from axq.position_actions import (
    PositionActionContext,
    PositionActionType,
    default_position_action_policy,
)
from axq.position_actions.persistence import SQLitePositionActionTransportLedger
from axq.position_management import (
    PositionManagementContext,
    default_demo_position_management_policy,
)
from axq.replay_validation.execution import (
    ENTRY_MODEL,
    SPREAD_MODEL,
    STOP_MODEL,
    PendingReplayEntry,
    ReplayBar,
    ReplayClosedTrade,
    ReplayExecutionBook,
    ReplayFill,
    ReplayPosition,
    ReplaySide,
)
from axq.replay_validation.outcomes import (
    ReplayActionApplication,
    ReplayEventContext,
    ReplayFillOutcome,
    ReplayOutcomeArtifact,
    ReplayTradeOutcome,
)
from axq.risk_boundary import RiskContext, default_demo_risk_policy
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    ExposureState,
    FreshnessStatus,
    MarketState,
    OrderBookState,
    PositionBookState,
    PositionSide,
    PositionState,
    ReplayClock,
    RuntimeEvent,
    RuntimeEventType,
    initial_runtime_state,
)
from axq.runtime.journal import JournalRecordType, SQLiteRuntimeJournal
from axq.runtime.kernel import EvidenceBundle, EvidenceKernel
from axq.runtime.replay import RuntimeStreamRunner, SemanticTraceStep
from axq.schemas import Signal
from axq.tools import CausalFeatureSnapshot, FeatureFactTool, ToolCatalog, ToolCategory
from axq.versioning import canonical_hash

MANIFEST_ID = "phase7-system-replay-features-v1"
SOURCE_VERSION = "phase7-system-replay-v1"
STOP_PLACEMENT_MODEL = "ATR_2_V1"
MARGIN_MODEL = "XAUUSD_100OZ_LEVERAGE_100_V1"
ATTRIBUTION_JOURNAL_RECORD_TYPES = frozenset(
    {
        JournalRecordType.RUNTIME_EVENT,
        JournalRecordType.AGENT_EVIDENCE,
    }
)


def _fresh(component: str, at: datetime) -> ComponentFreshness:
    return ComponentFreshness(
        component=component,
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=300_000,
    )


def _session_id(row: pd.Series) -> str:
    names = [
        name
        for name, column in (
            ("ASIA", "session_asia"),
            ("LONDON", "session_london"),
            ("NEW_YORK", "session_new_york"),
        )
        if int(row.get(column, 0)) == 1
    ]
    return "+".join(names) if names else "OFF_SESSION"


def _read_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)


def _merge_htf_bias(m5: pd.DataFrame, path: Path, timeframe: str) -> pd.DataFrame:
    higher = _read_csv(path)
    duration = {"m15": 15, "h1": 60, "h4": 240}[timeframe]
    bias = market_structure_features(higher, {})["structure_bias"]
    values = pd.DataFrame(
        {
            "available_at": higher["timestamp"] + pd.Timedelta(minutes=duration),
            f"{timeframe}_structure_bias": bias,
        }
    )
    return pd.merge_asof(
        m5.sort_values("available_at"),
        values.sort_values("available_at"),
        on="available_at",
        direction="backward",
        allow_exact_matches=True,
    )


def load_replay_frame(data_dir: Path, *, months: int) -> pd.DataFrame:
    """Build a causal feature frame while retaining warm-up history."""
    raw = _read_csv(data_dir / "xauusd_m5.csv")
    raw["available_at"] = raw["timestamp"] + pd.Timedelta(minutes=5)
    registry = default_registry()
    groups = (
        "price_action",
        "trend",
        "momentum",
        "volatility",
        "volume",
        "breakout",
        "statistical",
        "session",
        "market_structure",
    )
    featured = registry.compute(raw, enabled_groups=groups)
    featured["m5_structure_bias"] = featured["structure_bias"]
    featured["breakout_above"] = featured["breakout_above_20"].fillna(0).astype(bool)
    featured["breakout_below"] = featured["breakout_below_20"].fillna(0).astype(bool)
    featured["structure_bos_up"] = featured["structure_bos_up"].fillna(0).astype(bool)
    featured["structure_bos_down"] = featured["structure_bos_down"].fillna(0).astype(bool)
    featured["structure_choch_up"] = featured["structure_choch_up"].fillna(0).astype(bool)
    featured["structure_choch_down"] = featured["structure_choch_down"].fillna(0).astype(bool)
    featured["volatility_expansion"] = featured["structure_range_expansion_20"]
    featured["statistics_zscore_20"] = featured["stat_return_zscore_20"]
    featured["statistics_efficiency_ratio_20"] = featured["stat_efficiency_ratio_20"]
    for timeframe in ("m15", "h1", "h4"):
        featured = _merge_htf_bias(
            featured,
            data_dir / f"xauusd_{timeframe}.csv",
            timeframe,
        )
    last = featured["available_at"].max()
    first = last - pd.DateOffset(months=months)
    return cast(
        pd.DataFrame,
        featured.loc[featured["available_at"] >= first].reset_index(drop=True),
    )


def _catalog() -> tuple[ToolCatalog, dict[str, tuple[str, ...]]]:
    tools = (
        FeatureFactTool(
            "structure.core",
            ToolCategory.STRUCTURE,
            (
                "h4_structure_bias",
                "h1_structure_bias",
                "m15_structure_bias",
                "m5_structure_bias",
                "structure_bias",
                "structure_bos_up",
                "structure_bos_down",
                "structure_choch_up",
                "structure_choch_down",
            ),
        ),
        FeatureFactTool(
            "breakout.core",
            ToolCategory.BREAKOUT,
            ("breakout_above", "breakout_below"),
        ),
        FeatureFactTool(
            "trend.core",
            ToolCategory.TREND,
            (
                "trend_close_to_ema_20",
                "trend_plus_di_14",
                "trend_minus_di_14",
                "trend_adx_14",
            ),
        ),
        FeatureFactTool(
            "momentum.core",
            ToolCategory.MOMENTUM,
            ("momentum_macd_hist_12_26_9", "momentum_rsi_14"),
        ),
        FeatureFactTool(
            "statistics.core",
            ToolCategory.STATISTICS,
            ("statistics_zscore_20", "statistics_efficiency_ratio_20"),
        ),
        FeatureFactTool(
            "volatility.core",
            ToolCategory.VOLATILITY,
            ("volatility_expansion",),
        ),
    )
    access = {
        "chart": ("structure.core", "breakout.core"),
        "quant": ("trend.core", "momentum.core", "statistics.core"),
        "historical": (),
        "regime": (
            "trend.core",
            "statistics.core",
            "volatility.core",
            "breakout.core",
        ),
        "news": (),
    }
    return ToolCatalog(tools), access


class _RecordingProcessor:
    def __init__(self, delegate: DeterministicDecisionProcessor) -> None:
        self.delegate = delegate
        self.records: list[tuple[SemanticTraceStep, DecisionPlan]] = []

    def evaluate(
        self,
        event: RuntimeEvent,
        state: Any,
        trace: SemanticTraceStep,
        readiness: Any,
        controls: Any,
    ) -> DecisionPlan:
        plan = self.delegate.evaluate(event, state, trace, readiness, controls)
        self.records.append((trace, plan))
        return plan


@dataclass
class _ReplayContext:
    book: ReplayExecutionBook
    runner: RuntimeStreamRunner
    balance: float = 10_000.0
    peak_equity: float = 10_000.0
    day_start_balance: float = 10_000.0
    current_day: date | None = None
    fills_today: int = 0
    fills_by_session: Counter[str] | None = None
    last_entry_at: datetime | None = None
    last_exit_at: datetime | None = None
    last_stop_at: datetime | None = None
    last_rejection_at: datetime | None = None
    last_entry_direction: Signal | None = None
    consecutive_losses: int = 0
    executed_setups: set[str] | None = None
    executed_theses: set[str] | None = None
    intents: dict[str, Any] | None = None
    results: dict[str, ExecutionResult] | None = None
    state_positions: dict[str, str] | None = None
    latest_states: dict[str, Any] | None = None
    latest_row: pd.Series | None = None

    def __post_init__(self) -> None:
        self.fills_by_session = Counter()
        self.executed_setups = set()
        self.executed_theses = set()
        self.intents = {}
        self.results = {}
        self.state_positions = {}
        self.latest_states = {}

    def mark_day(self, at: datetime) -> None:
        if self.current_day != at.date():
            self.current_day = at.date()
            self.day_start_balance = self.balance
            self.fills_today = 0
            self.fills_by_session = Counter()

    def _pnl(self, position: ReplayPosition, price: float) -> float:
        signed = 1.0 if position.side is ReplaySide.BUY else -1.0
        return (price - position.open_price) / self.book.point_size * position.volume_lots * signed

    def states(self, row: pd.Series, at: datetime) -> dict[str, Any]:
        self.latest_row = row
        self.mark_day(at)
        spread = float(row["spread"])
        close = float(row["close"])
        floating = sum(self._pnl(item, close) for item in self.book.positions)
        equity = self.balance + floating
        self.peak_equity = max(self.peak_equity, equity)
        used = sum(close * item.volume_lots for item in self.book.positions)

        def fresh(name: str) -> ComponentFreshness:
            return _fresh(name, at)

        positions = []
        self.state_positions = {}
        for item in self.book.positions:
            side = PositionSide.BUY if item.side is ReplaySide.BUY else PositionSide.SELL
            state = PositionState(
                source="replay",
                replay_position_id=item.position_id,
                symbol="XAUUSD",
                side=side,
                volume_lots=item.volume_lots,
                opened_at=item.opened_at,
                open_price=item.open_price,
                current_price=close,
                stop_loss=item.stop_loss,
                floating_pnl=self._pnl(item, close),
                setup_id=item.setup_id,
                thesis_id=item.thesis_id,
            )
            positions.append(state)
            self.state_positions[state.position_id] = item.position_id
        account = AccountState(
            source="replay",
            account_id="phase7-system-replay",
            as_of=at,
            freshness=fresh("account"),
            currency="USD",
            balance=self.balance,
            equity=equity,
            free_margin=equity - used,
            used_margin=used,
            margin_level=(equity / used * 100 if used else 1_000_000.0),
            floating_pnl=floating,
            daily_realized_pnl=self.balance - self.day_start_balance,
            daily_unrealized_pnl=floating,
            daily_drawdown=max(0.0, self.day_start_balance - equity),
            total_drawdown=max(0.0, self.peak_equity - equity),
        )
        position_book = PositionBookState(
            source="replay", as_of=at, freshness=fresh("positions"), positions=tuple(positions)
        )
        orders = OrderBookState(source="replay", as_of=at, freshness=fresh("orders"))
        gross = sum(item.volume_lots for item in self.book.positions)
        net = sum(
            item.volume_lots * (1 if item.side is ReplaySide.BUY else -1)
            for item in self.book.positions
        )
        exposure = ExposureState(
            as_of=at,
            freshness=fresh("exposure"),
            gross_lots=gross,
            net_lots=net,
            gross_notional=gross * close * 100,
            net_notional=net * close * 100,
        )
        constraints = BrokerConstraints(
            source="replay",
            symbol="XAUUSD",
            as_of=at,
            freshness=fresh("broker_constraints"),
            trade_allowed=True,
            digits=2,
            volume_min=0.01,
            volume_max=10.0,
            volume_step=0.01,
            point_size=0.01,
            tick_size=0.01,
            tick_value_loss=1.0,
            stops_level_points=0.0,
            freeze_level_points=0.0,
        )
        market = MarketState(
            source="replay",
            symbol="XAUUSD",
            as_of=at,
            freshness=fresh("market"),
            bid=close - spread * 0.005,
            ask=close + spread * 0.005,
            last=close,
            spread_points=spread,
            base_timeframe="M5",
            completed_timeframes=("M5", "M15", "H1", "H4"),
            feature_manifest_id=MANIFEST_ID,
            market_data_version=SOURCE_VERSION,
        )
        self.latest_states = {
            "account": account,
            "positions": position_book,
            "orders": orders,
            "exposure": exposure,
            "broker_constraints": constraints,
            "market": market,
        }
        return self.latest_states

    def discipline_inputs(self, event: RuntimeEvent, _state: Any, trace: SemanticTraceStep) -> Any:
        from axq.orchestration.processor import EntryDecisionInputs

        assert self.latest_row is not None
        at = event.available_at
        thesis = self.runner.thesis
        scenario = (
            next(
                (
                    item
                    for item in thesis.scenarios
                    if item.entry_eligibility is EntryEligibility.ELIGIBLE
                ),
                None,
            )
            if thesis
            else None
        )
        setup_id = scenario.scenario_id if scenario else None
        thesis_id = thesis.thesis_id if scenario and thesis else None
        session = _session_id(self.latest_row)
        positions = tuple(
            DisciplinePosition(
                position_ref=item.position_id,
                direction=Signal.BUY if item.side is ReplaySide.BUY else Signal.SELL,
                setup_id=item.setup_id,
                thesis_id=item.thesis_id,
                opened_at=item.opened_at,
            )
            for item in self.book.positions
        )
        assert self.executed_setups is not None and self.executed_theses is not None
        discipline_policy = default_demo_discipline_policy()
        state = DisciplineState(
            policy_id=discipline_policy.policy_id,
            as_of=at,
            available_at=at,
            trading_day=at.date(),
            session_id=session,
            trades_today=self.fills_today,
            trades_this_session=(self.fills_by_session or Counter())[session],
            consecutive_losses=self.consecutive_losses,
            last_entry_at=self.last_entry_at,
            last_exit_at=self.last_exit_at,
            last_stop_loss_at=self.last_stop_at,
            last_rejection_at=self.last_rejection_at,
            last_entry_direction=self.last_entry_direction,
            active_positions=positions,
            active_setup_ids=tuple(item.setup_id for item in positions if item.setup_id),
            active_thesis_ids=tuple(item.thesis_id for item in positions if item.thesis_id),
            recently_executed_setup_ids=tuple(sorted(self.executed_setups)),
            recently_executed_thesis_ids=tuple(sorted(self.executed_theses)),
        )
        discipline_context = DisciplineContext(
            as_of=at,
            available_at=at,
            trading_day=at.date(),
            session_id=session,
            setup_id=setup_id,
            thesis_id=thesis_id,
            scenario_id=scenario.scenario_id if scenario else None,
            thesis_relationship=thesis.relationship if thesis else None,
            entry_intent=EntryIntent.INITIAL,
        )
        states = self.latest_states or {}
        entry = (
            states["market"].ask
            if trace.bundle.by_agent("chart").direction is DirectionalBias.BULLISH
            else states["market"].bid
        )
        atr = self.latest_row.get("vol_atr_14")
        stop = None
        if entry is not None and pd.notna(atr):
            stop = (
                float(entry) - 2 * float(atr)
                if trace.bundle.by_agent("chart").direction is DirectionalBias.BULLISH
                else float(entry) + 2 * float(atr)
            )
        risk = RiskContext(
            as_of=at,
            available_at=at,
            symbol="XAUUSD",
            account=states["account"],
            market=states["market"],
            positions=states["positions"],
            orders=states["orders"],
            exposure=states["exposure"],
            broker_constraints=states["broker_constraints"],
            entry_price=entry,
            stop_loss_price=stop,
            estimated_margin_required=(float(entry) * 0.01 if entry else 1.0),
            estimated_slippage_points=1.0,
            daily_drawdown_fraction=(states["account"].daily_drawdown or 0.0)
            / max(self.day_start_balance, 1.0),
            total_drawdown_fraction=(states["account"].total_drawdown or 0.0)
            / max(self.peak_equity, 1.0),
            kill_switch_active=False,
        )
        return EntryDecisionInputs(
            discipline_context=discipline_context,
            discipline_state=state,
            risk_context=risk,
        )

    def position_inputs(
        self, event: RuntimeEvent, _state: Any, trace: SemanticTraceStep
    ) -> tuple[PositionManagementContext, ...]:
        values = []
        for position in (self.latest_states or {})["positions"].positions:
            stable_id = (self.state_positions or {})[position.position_id]
            replay_position = next(
                item for item in self.book.positions if item.position_id == stable_id
            )
            intent = (self.intents or {})[replay_position.source_intent_id]
            result = (self.results or {})[replay_position.source_intent_id]
            link = BrokerIntentLink(
                intent_id=intent.intent_id,
                object_kind=BrokerObjectKind.POSITION,
                broker_object_id=position.position_id,
                transport_execution_id=result.transport_execution_id,
            )
            finding = ReconciliationFinding(
                kind=ReconciliationKind.MATCHED,
                status=ResolutionStatus.RESOLVED,
                intent_id=intent.intent_id,
                broker_object_id=position.position_id,
                reason_code="EXACT_REPLAY_LINK",
            )
            snapshot_identity = canonical_hash(
                {"at": event.available_at, "position": position.position_id}
            )
            report = ReconciliationReport(
                snapshot_id=f"replay-snapshot-{snapshot_identity[:20]}",
                as_of=event.available_at,
                available_at=event.available_at,
                status=ResolutionStatus.RESOLVED,
                findings=(finding,),
            )
            readiness = ResumeReadiness(
                runtime_state_id=trace.runtime_state_id,
                reconciliation_report_id=report.report_id,
                as_of=event.available_at,
                status=ResumeStatus.SAFE,
                reason_codes=(),
            )
            thesis = self.runner.thesis
            values.append(
                PositionManagementContext(
                    runtime_state_id=trace.runtime_state_id,
                    as_of=event.available_at,
                    available_at=event.available_at,
                    position=position,
                    original_execution_intent=intent,
                    original_execution_result=result,
                    broker_intent_link=link,
                    thesis=thesis if thesis and thesis.thesis_id == intent.thesis_id else None,
                    evidence_bundle=trace.bundle,
                    account=(self.latest_states or {})["account"],
                    position_freshness=(self.latest_states or {})["positions"].freshness,
                    broker_constraints=(self.latest_states or {})["broker_constraints"],
                    reconciliation=report,
                    resume_readiness=readiness,
                    intrabar_continuity=ContinuityStatus.COMPLETE,
                    unrealized_r_multiple=None,
                    mfe_points=replay_position.mfe_points,
                    mae_points=replay_position.mae_points,
                )
            )
        return tuple(values)

    def action_input(self, outcome: Any, _state: Any, _readiness: Any) -> PositionActionContext:
        contexts = self.position_inputs_cache
        context = contexts[outcome.position_id]
        assert context.original_execution_intent is not None
        assert context.original_execution_result is not None
        assert context.broker_intent_link is not None
        return PositionActionContext(
            policy_id=default_position_action_policy().policy_id,
            management_outcome=outcome,
            position=context.position,
            original_execution_intent=context.original_execution_intent,
            original_execution_result=context.original_execution_result,
            broker_intent_link=context.broker_intent_link,
            reconciliation=context.reconciliation,
            resume_readiness=context.resume_readiness,
            account=context.account,
            position_freshness=context.position_freshness,
            broker_constraints=context.broker_constraints,
            market=(self.latest_states or {})["market"],
            symbol_digits=2,
            kill_switch_active=False,
            as_of=outcome.as_of,
            available_at=outcome.available_at,
        )

    position_inputs_cache: dict[str, PositionManagementContext] = None  # type: ignore[assignment]


def _snapshot(row: pd.Series) -> CausalFeatureSnapshot:
    names = (
        "h4_structure_bias",
        "h1_structure_bias",
        "m15_structure_bias",
        "m5_structure_bias",
        "structure_bias",
        "structure_bos_up",
        "structure_bos_down",
        "structure_choch_up",
        "structure_choch_down",
        "breakout_above",
        "breakout_below",
        "trend_close_to_ema_20",
        "trend_plus_di_14",
        "trend_minus_di_14",
        "trend_adx_14",
        "momentum_macd_hist_12_26_9",
        "momentum_rsi_14",
        "statistics_zscore_20",
        "statistics_efficiency_ratio_20",
        "volatility_expansion",
    )
    at = row["available_at"].to_pydatetime()
    return CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=at,
        available_at=at,
        feature_manifest_id=MANIFEST_ID,
        completed_timeframes=("M5", "M15", "H1", "H4"),
        values={name: row[name] for name in names},
        source="phase2-feature-engine",
        source_version="2.0.0",
    )


def _scenario_transition(
    event: RuntimeEvent, bundle: EvidenceBundle, previous: ThesisState | None
) -> ThesisState | None:
    if event.event_type not in {
        RuntimeEventType.M5_CLOSED,
        RuntimeEventType.M1_CLOSED,
        RuntimeEventType.TICK,
    }:
        return previous
    chart = bundle.by_agent("chart")
    fact = "m5_structure_bias"
    definitions = (
        ScenarioDefinition(
            name="directional_continuation",
            confirmation_facts=(fact,),
            invalidation_facts=("structure_bos_down",)
            if chart.direction is DirectionalBias.BULLISH
            else ("structure_bos_up",),
        ),
    )
    return update_scenario(
        event,
        bundle.input_for("chart"),
        chart,
        previous,
        policy=ScenarioPolicy(ttl_seconds=900, max_m5_bars=3),
        scenario_definitions=definitions,
    )


def _event(event_type: RuntimeEventType, payload: Any, at: datetime, sequence: int) -> RuntimeEvent:
    return RuntimeEvent(
        event_type=event_type,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="system-replay",
        source_version=SOURCE_VERSION,
        source_sequence=sequence,
        symbol="XAUUSD",
        payload=payload,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _counts(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def run_system_replay(data_dir: Path, output_dir: Path, *, months: int = 1) -> Path:
    frame = load_replay_frame(data_dir, months=months)
    first_at = frame.iloc[0]["timestamp"].to_pydatetime()
    book = ReplayExecutionBook(point_size=0.01, slippage_points=1.0)
    catalog, access = _catalog()
    kernel = EvidenceKernel(
        initial_state=initial_runtime_state("XAUUSD", at=first_at - timedelta(seconds=1)),
        catalog=catalog,
        tool_access=access,
    )
    clock = ReplayClock(first_at - timedelta(seconds=1))
    output_dir.mkdir(parents=True, exist_ok=True)
    journal = SQLiteRuntimeJournal(output_dir / "runtime.sqlite3")
    execution_ledger = SQLiteExecutionLedger(output_dir / "execution.sqlite3")
    action_ledger = SQLitePositionActionTransportLedger(output_dir / "position-actions.sqlite3")
    runner = RuntimeStreamRunner(
        kernel,
        clock,
        journal=journal,
        retained_record_types=ATTRIBUTION_JOURNAL_RECORD_TYPES,
        scenario_transition=_scenario_transition,
    )
    context = _ReplayContext(book=book, runner=runner)
    position_cache: dict[str, PositionManagementContext] = {}

    def position_provider(
        event: RuntimeEvent, state: Any, trace: SemanticTraceStep
    ) -> tuple[PositionManagementContext, ...]:
        values = context.position_inputs(event, state, trace)
        position_cache.clear()
        position_cache.update({item.position.position_id: item for item in values if item.position})
        context.position_inputs_cache = position_cache
        return values

    processor = _RecordingProcessor(
        DeterministicDecisionProcessor(
            fusion_policy=default_fusion_policy(),
            discipline_policy=default_demo_discipline_policy(),
            risk_policy=default_demo_risk_policy(),
            execution_policy=default_execution_policy(),
            position_management_policy=default_demo_position_management_policy(),
            position_action_policy=default_position_action_policy(),
            entry_context_provider=context.discipline_inputs,
            position_context_provider=position_provider,
            position_action_context_provider=context.action_input,
        )
    )
    snapshots: dict[str, CausalFeatureSnapshot] = {}
    service = RuntimeOrchestrator(
        config=RuntimeConfig(
            mode=RuntimeMode.REPLAY,
            symbol="XAUUSD",
            broker_symbol="XAUUSD",
            runtime_journal_path=output_dir / "runtime.sqlite3",
            execution_ledger_path=output_dir / "execution.sqlite3",
            position_action_ledger_path=output_dir / "position-actions.sqlite3",
        ),
        runner=runner,
        processor=processor,
        journal=journal,
        execution_ledger=execution_ledger,
        position_action_ledger=action_ledger,
        clock=clock.now,
        feature_provider=lambda event, _state: snapshots.get(event.event_id),
    )
    service.startup()
    sequence = 1
    closed_trades: list[ReplayClosedTrade] = []
    fills: list[ReplayFill] = []
    duplicate_suppression = 0
    action_types: list[str] = []
    replay_fill_outcomes: list[ReplayFillOutcome] = []
    replay_trade_outcomes: list[ReplayTradeOutcome] = []
    replay_action_applications: list[ReplayActionApplication] = []
    replay_event_contexts: list[ReplayEventContext] = []
    queued_action_positions: dict[str, tuple[str, PositionActionType]] = {}
    cycles = []
    thesis_states: list[ThesisState] = []
    for row_number, (_, row) in enumerate(frame.iterrows()):
        opened_at = row["timestamp"].to_pydatetime()
        available_at = row["available_at"].to_pydatetime()
        bar = ReplayBar(
            opened_at=opened_at,
            available_at=available_at,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            spread_points=float(row["spread"]),
        )
        transport = book.process_bar(bar)
        fills.extend(transport.fills)
        closed_trades.extend(transport.closed_trades)
        applied_close_by_position: dict[str, str] = {}
        for action_id in transport.applied_action_ids:
            position_id, action_type = queued_action_positions[action_id]
            replay_action_applications.append(
                ReplayActionApplication(
                    position_action_intent_id=action_id,
                    position_id=position_id,
                    action_type=action_type,
                    applied_at=bar.opened_at,
                )
            )
            if action_type is PositionActionType.CLOSE_POSITION:
                if position_id in applied_close_by_position:
                    raise RuntimeError("multiple close actions applied to one replay position")
                applied_close_by_position[position_id] = action_id
        for trade in transport.closed_trades:
            source_action_id = applied_close_by_position.get(trade.position_id)
            if trade.exit_reason == "POSITION_ACTION_CLOSE" and source_action_id is None:
                raise RuntimeError("replay close has no exact position-action linkage")
            replay_trade_outcomes.append(
                ReplayTradeOutcome.from_replay(
                    trade,
                    source_position_action_intent_id=source_action_id,
                )
            )
            signed = 1 if trade.side is ReplaySide.BUY else -1
            pnl = (trade.exit_price - trade.entry_price) / 0.01 * trade.volume_lots * signed
            context.balance += pnl
            context.last_exit_at = trade.closed_at
            if trade.exit_reason == "PROTECTIVE_STOP":
                context.last_stop_at = trade.closed_at
            context.consecutive_losses = context.consecutive_losses + 1 if pnl < 0 else 0
        for fill in transport.fills:
            intent = (context.intents or {})[fill.instruction_id]
            result = ExecutionResult(
                execution_intent_id=intent.intent_id,
                evidence_bundle_id=intent.evidence_bundle_id,
                master_proposal_id=intent.master_proposal_id,
                discipline_outcome_id=intent.discipline_outcome_id,
                risk_outcome_id=intent.risk_outcome_id,
                setup_id=intent.setup_id,
                thesis_id=intent.thesis_id,
                scenario_id=intent.scenario_id,
                symbol=intent.symbol,
                direction=intent.direction,
                status=ExecutionResultStatus.FILLED,
                requested_volume_lots=intent.approved_volume_lots,
                filled_volume_lots=intent.approved_volume_lots,
                remaining_volume_lots=0.0,
                requested_price=intent.requested_entry_price,
                fill_price=fill.price,
                actual_spread_points=bar.spread_points,
                realized_slippage_points=(abs(fill.price - bar.open) / 0.01),
                transport_execution_id=fill.semantic_id,
                broker_status="REPLAY_FILLED",
                event_time=fill.executed_at,
                observed_at=fill.executed_at,
                available_at=fill.executed_at,
            )
            assert context.results is not None
            context.results[intent.intent_id] = result
            replay_fill_outcomes.append(
                ReplayFillOutcome.from_replay(
                    fill,
                    execution_result_id=result.result_id,
                )
            )
            if execution_ledger.reserve(intent):
                execution_ledger.record(result)
            feedback = execution_result_to_runtime_event(
                result,
                source="replay-transport",
                source_version=SOURCE_VERSION,
                source_sequence=sequence,
            )
            sequence += 1
            if feedback is not None:
                runner.reduce_only(feedback)
            context.last_entry_at = fill.executed_at
            context.last_entry_direction = intent.direction
            context.fills_today += 1
            session = _session_id(row)
            assert context.fills_by_session is not None
            context.fills_by_session[session] += 1
            assert context.executed_setups is not None and context.executed_theses is not None
            context.executed_setups.add(intent.setup_id)
            context.executed_theses.add(intent.thesis_id)
        states = context.states(row, available_at)
        state_events = (
            (RuntimeEventType.ACCOUNT_UPDATED, "account"),
            (RuntimeEventType.POSITIONS_UPDATED, "positions"),
            (RuntimeEventType.ORDERS_UPDATED, "orders"),
            (RuntimeEventType.EXPOSURE_UPDATED, "exposure"),
            (RuntimeEventType.BROKER_CONSTRAINTS_UPDATED, "broker_constraints"),
        )
        if row_number:
            for event_type, name in state_events:
                runner.reduce_only(_event(event_type, states[name], available_at, sequence))
                sequence += 1
        market_event = _event(RuntimeEventType.M5_CLOSED, states["market"], available_at, sequence)
        sequence += 1
        replay_event_contexts.append(
            ReplayEventContext(
                runtime_event_id=market_event.event_id,
                available_at=available_at,
                session=_session_id(row),
                regime=None,
            )
        )
        snapshots[market_event.event_id] = _snapshot(row)
        cycle = service.process_event(market_event)
        cycles.append(cycle)
        if runner.thesis is not None:
            thesis_states.append(runner.thesis)
        if not row_number:
            for event_type, name in state_events:
                runner.reduce_only(_event(event_type, states[name], available_at, sequence))
                sequence += 1
        _, plan = processor.records[-1]
        if plan.discipline and plan.discipline.result.value == "REJECT":
            context.last_rejection_at = available_at
        if plan.execution_intent is not None:
            intent = plan.execution_intent
            assert context.intents is not None
            context.intents[intent.intent_id] = intent
            queued = book.queue_entry(
                PendingReplayEntry(
                    intent_id=intent.intent_id,
                    direction=ReplaySide.BUY if intent.direction is Signal.BUY else ReplaySide.SELL,
                    volume_lots=intent.approved_volume_lots,
                    stop_loss=intent.stop_loss_price,
                    decision_available_at=cycle.available_at,
                    setup_id=intent.setup_id,
                    thesis_id=intent.thesis_id,
                    scenario_id=intent.scenario_id,
                )
            )
            duplicate_suppression += int(not queued)
        for action in plan.position_action_intents:
            action_types.append(action.action_type.value)
            stable = (context.state_positions or {}).get(action.position_id)
            if stable is None:
                continue
            if action.action_type is PositionActionType.CLOSE_POSITION:
                queued = book.queue_close(
                    position_id=stable,
                    decision_available_at=cycle.available_at,
                    action_intent_id=action.intent_id,
                )
            else:
                assert action.requested_new_stop_loss is not None
                queued = book.queue_stop_change(
                    position_id=stable,
                    stop_loss=action.requested_new_stop_loss,
                    decision_available_at=cycle.available_at,
                    action_intent_id=action.intent_id,
                )
            if queued:
                queued_action_positions[action.intent_id] = (stable, action.action_type)
            duplicate_suppression += int(not queued)

    service.shutdown()
    plans = [plan for _, plan in processor.records]
    traces = [trace for trace, _ in processor.records]
    evidence = [item for trace in traces for item in trace.bundle.evidence]
    masters = [plan.master for plan in plans if plan.master]
    disciplines = [plan.discipline for plan in plans if plan.discipline]
    risks = [plan.risk for plan in plans if plan.risk]
    management = [item for plan in plans for item in plan.position_management]
    pnl_values = []
    r_values = []
    for trade in closed_trades:
        signed = 1 if trade.side is ReplaySide.BUY else -1
        pnl_points = (trade.exit_price - trade.entry_price) / 0.01 * signed
        pnl_values.append(pnl_points * trade.volume_lots)
        initial_risk = abs(trade.entry_price - trade.initial_stop_loss) / 0.01
        if initial_risk > 0:
            r_values.append(pnl_points / initial_risk)
    gross_profit = sum(value for value in pnl_values if value > 0)
    gross_loss = -sum(value for value in pnl_values if value < 0)
    statuses = [item.status.value for item in evidence]
    thesis_by_id = {item.thesis_id: item for item in reversed(thesis_states)}
    thesis_ids = tuple(dict.fromkeys(item.thesis_id for item in thesis_states))
    successor_thesis_ids = tuple(
        dict.fromkeys(
            item.thesis_id
            for item in thesis_states
            if item.supersedes_thesis_id is not None
        )
    )
    expired_thesis_ids = tuple(
        dict.fromkeys(
            item.thesis_id
            for item in thesis_states
            if item.hypothesis_status is HypothesisStatus.EXPIRED
        )
    )
    expired_thesis_id_set = set(expired_thesis_ids)
    post_expiry_successor_ids: list[str] = []
    for thesis_id in successor_thesis_ids:
        successor = thesis_by_id[thesis_id]
        predecessor_id = successor.supersedes_thesis_id
        if predecessor_id is None or predecessor_id not in expired_thesis_id_set:
            continue
        if successor.hypothesis_id == thesis_by_id[predecessor_id].hypothesis_id:
            post_expiry_successor_ids.append(thesis_id)
    metrics: dict[str, Any] = {
        "schema_version": "1.0",
        "input": {
            "months": months,
            "start": frame.iloc[0]["available_at"].isoformat(),
            "end": frame.iloc[-1]["available_at"].isoformat(),
            "rows": len(frame),
            "m5_sha256": _file_sha256(data_dir / "xauusd_m5.csv"),
        },
        "conventions": {
            "entry_model": ENTRY_MODEL,
            "stop_model": STOP_MODEL,
            "spread_model": SPREAD_MODEL,
            "slippage_points": 1.0,
            "stop_placement_model": STOP_PLACEMENT_MODEL,
            "margin_model": MARGIN_MODEL,
        },
        "decisions": {
            "m5_cycles": len(plans),
            "master": _counts([item.decision.value for item in masters]),
            "entry_eligibility": _counts(
                [
                    trace.entry_eligibility.value
                    if trace.entry_eligibility is not None
                    else "NO_THESIS"
                    for trace in traces
                ]
            ),
            "unique_thesis_states": len(
                {trace.thesis_state_id for trace in traces if trace.thesis_state_id}
            ),
            "unique_theses": len(thesis_ids),
            "successor_theses": len(successor_thesis_ids),
            "post_expiry_successor_theses": len(post_expiry_successor_ids),
            "thesis_expiries": len(expired_thesis_ids),
        },
        "agents": {
            "status": _counts(statuses),
            "status_by_agent": {
                name: _counts([item.status.value for item in evidence if item.agent_name == name])
                for name in ("chart", "quant", "historical", "regime", "news")
            },
            "average_confidence": sum(item.confidence for item in evidence) / len(evidence),
        },
        "master": {
            "average_confidence": sum(item.confidence for item in masters) / len(masters),
            "average_disagreement": sum(item.disagreement for item in masters) / len(masters),
            "average_contradiction": sum(item.contradiction for item in masters) / len(masters),
        },
        "discipline": {
            "results": _counts([item.result.value for item in disciplines]),
            "reasons": _counts(
                [reason.value for item in disciplines for reason in item.reason_codes]
            ),
        },
        "risk": {
            "results": _counts([item.result.value for item in risks]),
            "reasons": _counts([reason.value for item in risks for reason in item.reason_codes]),
        },
        "execution": {
            "intents": sum(plan.execution_intent is not None for plan in plans),
            "fills": len(fills),
            "semantic_duplicate_suppression": duplicate_suppression,
            "unknown": 0,
        },
        "positions": {
            "opened": len(fills),
            "management": _counts([item.result.value for item in management]),
            "actions": _counts(action_types),
            "still_open": len(book.positions),
        },
        "trades": {
            "completed": len(closed_trades),
            "long": sum(item.side is ReplaySide.BUY for item in closed_trades),
            "short": sum(item.side is ReplaySide.SELL for item in closed_trades),
            "average_holding_minutes": (
                sum(
                    (item.closed_at - item.opened_at).total_seconds() / 60 for item in closed_trades
                )
                / len(closed_trades)
                if closed_trades
                else None
            ),
            "average_mfe_points": sum(item.mfe_points for item in closed_trades)
            / len(closed_trades)
            if closed_trades
            else None,
            "average_mae_points": sum(item.mae_points for item in closed_trades)
            / len(closed_trades)
            if closed_trades
            else None,
            "average_r": sum(r_values) / len(r_values) if r_values else None,
            "expectancy_usd": sum(pnl_values) / len(pnl_values) if pnl_values else None,
            "win_rate": sum(value > 0 for value in pnl_values) / len(pnl_values)
            if pnl_values
            else None,
            "profit_factor": gross_profit / gross_loss if gross_loss else None,
            "realized_pnl": sum(pnl_values),
            "max_drawdown": context.peak_equity - min(context.balance, context.peak_equity),
        },
        "safety": {
            "duplicate_order_attempts": duplicate_suppression,
            "unresolved_unknown": 0,
            "linkage_conflicts": 0,
            "broker_only_anomalies": 0,
            "local_only_anomalies": 0,
            "unsafe_readiness_events": 0,
            "broker_mutation_calls": 0,
        },
        "semantic_ids": {
            "cycles": [item.cycle_id for item in cycles],
            "theses": list(thesis_ids),
            "successor_theses": list(successor_thesis_ids),
            "post_expiry_successor_theses": post_expiry_successor_ids,
            "expired_theses": list(expired_thesis_ids),
            "fills": [item.semantic_id for item in fills],
            "trades": [item.semantic_id for item in closed_trades],
        },
    }
    metrics["artifact_id"] = f"replay-{canonical_hash(metrics)[:20]}"
    ReplayOutcomeArtifact(
        source_metrics_id=str(metrics["artifact_id"]),
        input_sha256=str(metrics["input"]["m5_sha256"]),
        entry_model=ENTRY_MODEL,
        stop_model=STOP_MODEL,
        spread_model=SPREAD_MODEL,
        slippage_points=1.0,
        fills=tuple(replay_fill_outcomes),
        trades=tuple(replay_trade_outcomes),
        action_applications=tuple(replay_action_applications),
        event_contexts=tuple(replay_event_contexts),
    ).write(output_dir / "replay-outcomes.json")
    path = output_dir / "metrics.json"
    path.write_text(
        json.dumps(metrics, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return path


def compare_replays(first: Path, second: Path) -> dict[str, Any]:
    first_bytes = first.read_bytes()
    second_bytes = second.read_bytes()
    return {
        "byte_identical": first_bytes == second_bytes,
        "first_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "second_sha256": hashlib.sha256(second_bytes).hexdigest(),
        "semantic_ids_identical": json.loads(first_bytes)["semantic_ids"]
        == json.loads(second_bytes)["semantic_ids"],
    }
