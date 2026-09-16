"""Composition and CLI for the read-only live shadow runtime."""

from __future__ import annotations

import argparse
import time
from collections.abc import Mapping
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from axq.agents import (
    DirectionalBias,
    EntryEligibility,
    ScenarioDefinition,
    ThesisState,
    update_scenario,
)
from axq.discipline import DisciplineContext, DisciplineState
from axq.execution_boundary import ExecutionIntent, SQLiteExecutionLedger
from axq.interaction.processor import EvidenceBoundInteractionProcessor
from axq.master import fuse_evidence
from axq.mt5 import (
    GoldSymbolConfiguration,
    MetaTrader5Gateway,
    MT5BrokerEnvironmentIdentity,
    MT5BrokerSnapshotProvider,
    MT5BrokerTimeNormalizer,
    MT5BrokerTimeOffsetResolution,
    MT5SymbolMapping,
    MT5TimeNormalizationError,
    infer_broker_time_offset,
    resolve_gold_instrument,
)
from axq.mt5.live_source import LiveShadowPoll, MT5CompletedM5Source
from axq.orchestration.config import RuntimeConfig
from axq.orchestration.contracts import DecisionPlan, RuntimeMode
from axq.orchestration.performance import RuntimePerformanceTracker
from axq.orchestration.processor import (
    DeterministicDecisionProcessor,
    EntryDecisionInputs,
)
from axq.orchestration.service import RuntimeOrchestrator
from axq.orchestration.shadow import LiveShadowRuntime
from axq.orchestration.shadow_control import (
    ManagedRuntimeControl,
    ManagedRuntimeStatus,
    ShadowRuntimeInstanceGuard,
    SQLiteShadowControlStore,
)
from axq.position_actions import PositionActionContext, SQLitePositionActionTransportLedger
from axq.replay_validation import default_shared_kernel_policy_set
from axq.risk_boundary import RiskContext
from axq.runtime import RuntimeEvent, SystemUTCClock, initial_runtime_state
from axq.runtime.journal import JournalRecordType, SQLiteRuntimeJournal
from axq.runtime.kernel import EvidenceBundle, EvidenceKernel
from axq.runtime.replay import RuntimeStreamRunner, SemanticTraceStep
from axq.runtime.shadow import ShadowExecutionRecord
from axq.runtime.shadow_sink import JournalShadowExecutionSink
from axq.schemas import Signal
from axq.tools import (
    FeatureFactTool,
    ToolCatalog,
    ToolCategory,
)
from axq.versioning import canonical_hash


def _catalog() -> tuple[ToolCatalog, dict[str, tuple[str, ...]]]:
    tools = (
        FeatureFactTool(
            "structure.core",
            ToolCategory.STRUCTURE,
            (
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
        "regime": ("trend.core", "statistics.core", "volatility.core", "breakout.core"),
        "news": (),
    }
    return ToolCatalog(tools), access


def _scenario_transition(
    event: RuntimeEvent,
    bundle: EvidenceBundle,
    previous: ThesisState | None,
    policy: Any,
) -> ThesisState | None:
    chart = bundle.by_agent("chart")
    definitions = (
        ScenarioDefinition(
            name="directional_continuation",
            confirmation_facts=("m5_structure_bias",),
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
        policy=policy,
        scenario_definitions=definitions,
    )


class _LiveContext:
    def __init__(
        self,
        runner: RuntimeStreamRunner,
        policy_id: str,
        journal: SQLiteRuntimeJournal,
    ) -> None:
        self.runner = runner
        self.policy_id = policy_id
        self.journal = journal

    def _shadow_history(
        self, at: datetime
    ) -> tuple[int, datetime | None, Signal | None, tuple[str, ...], tuple[str, ...]]:
        operational_history = self.journal.query_records(
            record_types=(
                JournalRecordType.EXECUTION_INTENT,
                JournalRecordType.SHADOW_EXECUTION,
            )
        )
        intents = {
            item.record.semantic_id: item.record.decode()
            for item in operational_history
            if item.record.record_type is JournalRecordType.EXECUTION_INTENT
        }
        executions = [
            cast(ShadowExecutionRecord, item.record.decode())
            for item in operational_history
            if item.record.record_type is JournalRecordType.SHADOW_EXECUTION
            and item.record.available_at.date() == at.date()
        ]
        linked = [
            cast(ExecutionIntent, intents[item.execution_intent_id])
            for item in executions
            if item.execution_intent_id in intents
        ]
        latest = executions[-1] if executions else None
        latest_intent = linked[-1] if linked else None
        return (
            len(executions),
            None if latest is None else latest.as_of,
            None if latest_intent is None else latest_intent.direction,
            tuple(sorted({item.setup_id for item in linked if item.setup_id})),
            tuple(sorted({item.thesis_id for item in linked if item.thesis_id})),
        )

    def entry(
        self,
        event: RuntimeEvent,
        state: Any,
        trace: SemanticTraceStep,
    ) -> EntryDecisionInputs:
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
        trades, last_entry, last_direction, executed_setups, executed_theses = (
            self._shadow_history(event.available_at)
        )
        discipline_context = DisciplineContext(
            as_of=event.available_at,
            available_at=event.available_at,
            trading_day=event.available_at.date(),
            session_id="ASIA_KUALA_LUMPUR_20_23",
            setup_id=setup_id,
            thesis_id=thesis.thesis_id if thesis and scenario else None,
            scenario_id=setup_id,
            thesis_relationship=thesis.relationship if thesis else None,
        )
        positions = tuple(
            # Broker positions without AXQ setup/thesis linkage remain visible but unclaimed.
            __import__("axq.discipline", fromlist=["DisciplinePosition"]).DisciplinePosition(
                position_ref=item.position_id,
                direction=Signal.BUY if item.side.value == "BUY" else Signal.SELL,
                setup_id=item.setup_id,
                thesis_id=item.thesis_id,
                opened_at=item.opened_at,
            )
            for item in state.positions.positions
        )
        discipline_state = DisciplineState(
            policy_id=self.policy_id,
            as_of=event.available_at,
            available_at=event.available_at,
            trading_day=event.available_at.date(),
            session_id="ASIA_KUALA_LUMPUR_20_23",
            trades_today=trades,
            trades_this_session=trades,
            consecutive_losses=0,
            last_entry_at=last_entry,
            last_entry_direction=last_direction,
            active_positions=positions,
            active_setup_ids=tuple(item.setup_id for item in positions if item.setup_id),
            active_thesis_ids=tuple(item.thesis_id for item in positions if item.thesis_id),
            recently_executed_setup_ids=executed_setups,
            recently_executed_thesis_ids=executed_theses,
        )
        account = state.account
        if account.daily_drawdown is None or account.total_drawdown is None:
            raise ValueError("live broker drawdown facts are unavailable")
        if account.balance is None or account.balance <= 0:
            raise ValueError("live broker balance is unavailable")
        direction = trace.bundle.by_agent("chart").direction
        entry = state.market.ask if direction is DirectionalBias.BULLISH else state.market.bid
        risk = RiskContext(
            as_of=event.available_at,
            available_at=event.available_at,
            symbol=state.symbol,
            account=account,
            market=state.market,
            positions=state.positions,
            orders=state.orders,
            exposure=state.exposure,
            broker_constraints=state.broker_constraints,
            entry_price=entry,
            stop_loss_price=None,
            estimated_margin_required=None,
            estimated_slippage_points=None,
            daily_drawdown_fraction=account.daily_drawdown / account.balance,
            total_drawdown_fraction=account.total_drawdown / account.balance,
            kill_switch_active=False,
        )
        return EntryDecisionInputs(
            discipline_context=discipline_context,
            discipline_state=discipline_state,
            risk_context=risk,
        )

    @staticmethod
    def positions(
        event: RuntimeEvent,
        state: Any,
        trace: SemanticTraceStep,
    ) -> tuple[()]:
        del event, state, trace
        return ()

    @staticmethod
    def action(outcome: Any, state: Any, readiness: Any) -> PositionActionContext:
        del outcome, state, readiness
        raise RuntimeError("unlinked live positions cannot produce shadow position actions")


class _FailClosedLiveProcessor:
    """Preserve Master evidence if live-only Risk inputs are not yet available."""

    def __init__(self, delegate: DeterministicDecisionProcessor, fusion_policy: Any) -> None:
        self.delegate = delegate
        self.fusion_policy = fusion_policy
        self._fallback_master_latency_ms = 0.0

    @property
    def last_master_latency_ms(self) -> float:
        return max(self.delegate.last_master_latency_ms, self._fallback_master_latency_ms)

    def evaluate(
        self,
        event: RuntimeEvent,
        state: Any,
        trace: SemanticTraceStep,
        readiness: Any,
        controls: Any,
    ) -> DecisionPlan:
        self._fallback_master_latency_ms = 0.0
        try:
            return self.delegate.evaluate(event, state, trace, readiness, controls)
        except ValueError as error:
            if "live broker" not in str(error):
                raise
            started = time.perf_counter()
            master = fuse_evidence(trace.bundle, self.fusion_policy)
            self._fallback_master_latency_ms = (time.perf_counter() - started) * 1_000.0
            return DecisionPlan(master=master)


def _poll_after_recovery_refresh(
    orchestrator: RuntimeOrchestrator,
    source: MT5CompletedM5Source,
) -> LiveShadowPoll:
    """Refresh broker facts before constructing the next source-available event."""
    orchestrator.refresh_snapshot_if_due()
    return source.poll()


def _run_live_shadow_locked(
    *,
    broker_symbol: str | None,
    gold_symbols: str | None,
    output_dir: Path,
    terminal_path: Path | None,
    once: bool,
    poll_seconds: float,
    control: ManagedRuntimeControl | None,
) -> None:
    clock = SystemUTCClock()
    gateway = MetaTrader5Gateway(
        terminal_path=str(terminal_path) if terminal_path is not None else None
    )
    configuration = symbol_configuration(broker_symbol, gold_symbols)
    output_dir.mkdir(parents=True, exist_ok=True)
    journal = SQLiteRuntimeJournal(output_dir / "shadow-runtime.sqlite3")
    gateway.connect()
    try:
        resolution = resolve_gold_instrument(
            gateway,
            configuration,
            resolved_at=clock.now(),
        )
        broker_time = resolve_session_broker_time(
            gateway=gateway,
            journal=journal,
            instrument_resolution=resolution,
            clock=clock.now,
        )
    finally:
        gateway.close()
    resolved_broker_symbol = resolution.resolved_broker_symbol
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol=resolved_broker_symbol,
        instrument_resolution_id=resolution.resolution_id,
        point_size=resolution.point_size,
        clock=clock.now,
        broker_time_normalizer=broker_time,
    )
    journal.append_semantic(resolution, event_id=None)
    if not journal.contains_semantic_id(broker_time.resolution.resolution_id):
        journal.append_semantic(
            broker_time.resolution,
            event_id=None,
            available_at=broker_time.resolution.resolved_at,
        )
    execution_ledger = SQLiteExecutionLedger(output_dir / "shadow-execution.sqlite3")
    action_ledger = SQLitePositionActionTransportLedger(
        output_dir / "shadow-position-actions.sqlite3"
    )
    policies = default_shared_kernel_policy_set()
    catalog, access = _catalog()
    runner = RuntimeStreamRunner(
        EvidenceKernel(
            initial_state=initial_runtime_state("XAUUSD", at=clock.now()),
            catalog=catalog,
            tool_access=access,
        ),
        clock,
        journal=journal,
        scenario_transition=lambda event, bundle, previous: _scenario_transition(
            event, bundle, previous, policies.scenario_policy
        ),
    )
    context = _LiveContext(runner, policies.discipline_policy.policy_id, journal)
    delegate = DeterministicDecisionProcessor(
        fusion_policy=policies.fusion_policy,
        discipline_policy=policies.discipline_policy,
        risk_policy=policies.risk_policy,
        execution_policy=policies.execution_policy,
        position_management_policy=policies.position_management_policy,
        position_action_policy=policies.position_action_policy,
        entry_context_provider=context.entry,
        position_context_provider=context.positions,
        position_action_context_provider=context.action,
    )
    snapshot_provider = MT5BrokerSnapshotProvider(
        gateway=gateway,
        symbol_mapping=MT5SymbolMapping(
            internal_symbol="XAUUSD", broker_symbol=resolved_broker_symbol
        ),
        clock=clock.now,
        source="mt5-shadow",
        source_version="1.0.0",
        stale_after_ms=300_000,
        select_symbol=False,
        broker_time_normalizer=broker_time,
    )
    fail_closed_processor = _FailClosedLiveProcessor(delegate, policies.fusion_policy)

    def scan_id_for_event(event_id: str) -> str | None:
        records = journal.query_records(
            record_types=(JournalRecordType.M5_CANDIDATE_SCAN,),
            event_id=event_id,
            newest_first=True,
            limit=1,
        )
        return None if not records else records[0].record.semantic_id

    interaction_processor = EvidenceBoundInteractionProcessor(
        delegate=fail_closed_processor,
        fusion_policy=policies.fusion_policy,
        journal=journal,
        scan_id_for_event=scan_id_for_event,
    )
    orchestrator = RuntimeOrchestrator(
        config=RuntimeConfig(
            mode=RuntimeMode.SHADOW,
            symbol="XAUUSD",
            broker_symbol=resolved_broker_symbol,
            runtime_journal_path=output_dir / "shadow-runtime.sqlite3",
            execution_ledger_path=output_dir / "shadow-execution.sqlite3",
            position_action_ledger_path=output_dir / "shadow-position-actions.sqlite3",
            mt5_terminal_path=terminal_path,
        ),
        runner=runner,
        processor=interaction_processor,
        journal=journal,
        execution_ledger=execution_ledger,
        position_action_ledger=action_ledger,
        clock=clock.now,
        gateway=gateway,
        snapshot_provider=snapshot_provider,
    )
    status = orchestrator.startup()
    if not status.accepting_events:
        raise RuntimeError(status.last_error or "live shadow startup is not safe")
    if control is not None:
        control.record(
            ManagedRuntimeStatus.RUNNING,
            now=clock.now(),
            reason_code="RUNTIME_READY",
        )
    runtime = LiveShadowRuntime(
        orchestrator=orchestrator,
        runner=runner,
        journal=journal,
        symbol="XAUUSD",
        feature_manifest_id=source.feature_manifest_id,
        resolved_broker_symbol=resolved_broker_symbol,
        instrument_resolution_id=resolution.resolution_id,
        execution_sink=JournalShadowExecutionSink(journal),
    )
    performance = RuntimePerformanceTracker(output_dir / "runtime-performance.json")
    try:
        while True:
            if control is not None and control.stop_requested():
                control.record(
                    ManagedRuntimeStatus.STOPPING,
                    now=clock.now(),
                    reason_code="EXACT_INSTANCE_STOP_ACCEPTED",
                )
                break
            poll = _poll_after_recovery_refresh(orchestrator, source)
            runtime.record_availability(poll.availability)
            if control is not None:
                waiting = poll.availability.status.value in {"STALE_QUOTE", "UNAVAILABLE"}
                control.record(
                    (
                        ManagedRuntimeStatus.WAITING_FOR_MARKET
                        if waiting
                        else ManagedRuntimeStatus.RUNNING
                    ),
                    now=clock.now(),
                    reason_code=poll.availability.reason_code,
                )
            if poll.bar is not None:
                journal.append_semantic(
                    poll.bar.m5_trace,
                    event_id=poll.bar.event.event_id,
                    available_at=poll.bar.event.available_at,
                )
                journal.append_semantic(
                    poll.bar.m15_trace,
                    event_id=poll.bar.event.event_id,
                    available_at=poll.bar.event.available_at,
                )
                runtime.process(poll.bar.event, poll.bar.feature_snapshot)
                performance.record(
                    source=source.last_performance,
                    cycle_latency_ms=runtime.last_performance.cycle_latency_ms,
                    scanner_latency_ms=runtime.last_performance.scanner_latency_ms,
                    kernel=runner.last_kernel_performance,
                    master_latency_ms=interaction_processor.last_master_latency_ms,
                    discussion_latency_ms=interaction_processor.last_discussion_latency_ms,
                )
            else:
                performance.record(source=source.last_performance)
            if once:
                break
            deadline = time.monotonic() + poll_seconds
            while time.monotonic() < deadline:
                if control is not None and control.stop_requested():
                    break
                time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))
    finally:
        orchestrator.shutdown()


def run_live_shadow(
    *,
    broker_symbol: str | None,
    gold_symbols: str | None,
    output_dir: Path,
    terminal_path: Path | None,
    once: bool,
    poll_seconds: float,
    managed_instance_id: str | None = None,
    control_db: Path | None = None,
) -> None:
    """Run one guarded SHADOW instance; operational control never enters semantic IDs."""
    managed = managed_control_configuration(managed_instance_id, control_db)
    control = (
        None
        if managed is None
        else ManagedRuntimeControl(SQLiteShadowControlStore(managed[1]), managed[0])
    )
    guard = ShadowRuntimeInstanceGuard(output_dir)
    try:
        with guard:
            _run_live_shadow_locked(
                broker_symbol=broker_symbol,
                gold_symbols=gold_symbols,
                output_dir=output_dir,
                terminal_path=terminal_path,
                once=once,
                poll_seconds=poll_seconds,
                control=control,
            )
    except Exception as error:
        if control is not None:
            with suppress(Exception):
                control.record(
                    ManagedRuntimeStatus.ERROR,
                    now=SystemUTCClock().now(),
                    reason_code="RUNTIME_CRASHED",
                    error=(str(error) or type(error).__name__)[:500],
                )
        raise
    else:
        if control is not None:
            control.record(
                ManagedRuntimeStatus.STOPPED,
                now=SystemUTCClock().now(),
                reason_code="GRACEFUL_SHUTDOWN_COMPLETE",
            )


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _broker_environment(
    terminal: Mapping[str, object], account: Mapping[str, object]
) -> MT5BrokerEnvironmentIdentity:
    return MT5BrokerEnvironmentIdentity(
        broker_server=_optional_str(account.get("server")),
        account_login_digest=(
            canonical_hash({"account_login": str(account["login"])})
            if account.get("login") is not None
            else None
        ),
        account_trade_mode=_optional_int(account.get("trade_mode")),
        terminal_company=_optional_str(terminal.get("company")),
        terminal_build=_optional_int(terminal.get("build")),
    )


def _required_tick_epoch(tick: Mapping[str, object], name: str) -> int | None:
    value = tick.get(name)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
        return int(value)
    return None


def resolve_session_broker_time(
    *,
    gateway: Any,
    journal: SQLiteRuntimeJournal,
    instrument_resolution: Any,
    clock: Any,
) -> MT5BrokerTimeNormalizer:
    """Resolve once from a fresh tick or reuse one exactly compatible persisted record."""
    terminal = gateway.terminal_info()
    account = gateway.account_info()
    if terminal is None or account is None:
        raise MT5TimeNormalizationError("MT5 environment identity is unavailable")
    environment = _broker_environment(terminal, account)
    tick = gateway.symbol_info_tick(instrument_resolution.resolved_broker_symbol)
    if tick is None:
        raise MT5TimeNormalizationError("MT5 broker tick is unavailable")
    seconds = _required_tick_epoch(tick, "time")
    if seconds is None:
        raise MT5TimeNormalizationError("MT5 broker tick time is unavailable")
    milliseconds = _required_tick_epoch(tick, "time_msc")
    observed_at = clock()
    try:
        inferred = infer_broker_time_offset(
            raw_tick_time=seconds,
            raw_tick_time_msc=milliseconds,
            observed_at=observed_at,
            canonical_instrument="XAUUSD",
            resolved_broker_symbol=instrument_resolution.resolved_broker_symbol,
            instrument_resolution_id=instrument_resolution.resolution_id,
            environment=environment,
        )
        return MT5BrokerTimeNormalizer(inferred)
    except MT5TimeNormalizationError as inference_error:
        persisted = tuple(
            MT5BrokerTimeOffsetResolution.model_validate(item.record.decode())
            for item in journal.query_records(
                record_types=(JournalRecordType.MT5_TIME_OFFSET_RESOLUTION,)
            )
        )
        for prior in reversed(persisted):
            try:
                normalizer = MT5BrokerTimeNormalizer.from_persisted(
                    prior,
                    canonical_instrument="XAUUSD",
                    resolved_broker_symbol=instrument_resolution.resolved_broker_symbol,
                    instrument_resolution_id=instrument_resolution.resolution_id,
                    environment=environment,
                )
                normalizer.normalize_tick(
                    raw_tick_time=seconds,
                    raw_tick_time_msc=milliseconds,
                    observed_at=observed_at,
                )
                return normalizer
            except MT5TimeNormalizationError:
                continue
        raise MT5TimeNormalizationError(
            "fresh broker offset could not be inferred and no compatible persisted "
            "resolution is available"
        ) from inference_error


def symbol_configuration(
    broker_symbol: str | None,
    gold_symbols: str | None,
) -> GoldSymbolConfiguration:
    if broker_symbol is not None:
        return GoldSymbolConfiguration.single(broker_symbol)
    if gold_symbols is None:
        raise ValueError("one explicit broker symbol mode is required")
    return GoldSymbolConfiguration.aliases(tuple(gold_symbols.split(",")))


def managed_control_configuration(
    instance_id: str | None,
    control_db: str | Path | None,
) -> tuple[str, Path] | None:
    """Require exact managed-process identity and store path as one boundary."""
    if (instance_id is None) != (control_db is None):
        raise ValueError("managed instance ID and control database must be supplied together")
    if instance_id is None or control_db is None:
        return None
    if not instance_id.strip():
        raise ValueError("managed instance ID cannot be empty")
    return instance_id, Path(control_db)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AXQ read-only live shadow runtime")
    symbols = parser.add_mutually_exclusive_group(required=True)
    symbols.add_argument("--broker-symbol")
    symbols.add_argument("--gold-symbols")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--terminal-path", type=Path)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--managed-instance-id")
    parser.add_argument("--control-db", type=Path)
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()
    managed = managed_control_configuration(args.managed_instance_id, args.control_db)
    run_live_shadow(
        broker_symbol=args.broker_symbol,
        gold_symbols=args.gold_symbols,
        output_dir=args.output_dir,
        terminal_path=args.terminal_path,
        once=args.once,
        poll_seconds=args.poll_seconds,
        managed_instance_id=None if managed is None else managed[0],
        control_db=None if managed is None else managed[1],
    )


if __name__ == "__main__":
    main()
