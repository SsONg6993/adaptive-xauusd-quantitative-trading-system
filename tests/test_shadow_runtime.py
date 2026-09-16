from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from axq.orchestration.contracts import DecisionCycle, DecisionPlan
from axq.orchestration.shadow import LiveShadowRuntime
from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    RuntimeEvent,
    RuntimeEventType,
    initial_runtime_state,
)
from axq.runtime.journal import JournalRecordType, SQLiteRuntimeJournal
from axq.runtime.shadow import (
    CandidateResult,
    LiveMarketStatus,
    ShadowCycleStage,
    ShadowMarketAvailability,
)
from axq.tools import CausalFeatureSnapshot

T0 = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)  # 20:00 Malaysia


def _snapshot(*, candidate: bool) -> CausalFeatureSnapshot:
    values: dict[str, object] = {
        "m15_breakout_above": False,
        "m15_breakout_below": False,
        "m15_statistics_efficiency_ratio_20": 0.2,
        "m15_structure_bias": 1.0,
        "m15_trend_adx_14": 15.0,
        "m15_volatility_expansion": 1.0,
        "breakout_above_20": False,
        "breakout_below_20": False,
        "breakout_failed_down_20": False,
        "breakout_failed_up_20": False,
        "breakout_retest_down_20": False,
        "breakout_retest_up_20": False,
        "momentum_macd_hist_12_26_9": 0.05 if candidate else 0.0,
        "momentum_rsi_14": 50.0,
        "structure_bos_down": False,
        "structure_bos_up": False,
        "structure_choch_down": False,
        "structure_choch_up": False,
        "structure_hh": False,
        "structure_hl": False,
        "structure_lh": False,
        "structure_ll": False,
        "trend_close_to_ema_20": 0.0,
        "trend_minus_di_14": 20.0,
        "trend_plus_di_14": 20.0,
    }
    return CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=T0,
        available_at=T0,
        feature_manifest_id="fm-shadow",
        completed_timeframes=("M5", "M15"),
        values=values,
        source="fixture",
        source_version="1",
    )


def _event(sequence: int = 1) -> RuntimeEvent:
    market = MarketState(
        source="fixture",
        symbol="XAUUSD",
        as_of=T0,
        freshness=ComponentFreshness(
            component="market",
            status=FreshnessStatus.AVAILABLE,
            observed_at=T0,
            available_at=T0,
            stale_after_ms=300_000,
        ),
        bid=2500.0,
        ask=2500.2,
        last=2500.1,
        spread_points=20.0,
        base_timeframe="M5",
        completed_timeframes=("M5", "M15"),
        feature_manifest_id="fm-shadow",
    )
    return RuntimeEvent(
        event_type=RuntimeEventType.M5_CLOSED,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
        source="fixture",
        source_version="1",
        source_sequence=sequence,
        symbol="XAUUSD",
        payload=market,
    )


class FakeRunner:
    def __init__(self) -> None:
        self.state = initial_runtime_state("XAUUSD", at=T0)
        self.quiet_calls = 0
        self.process_calls = 0

    def reduce_quiet(self, event: RuntimeEvent, feature_snapshot: CausalFeatureSnapshot) -> None:
        del event, feature_snapshot
        self.quiet_calls += 1

    def process(self, event: RuntimeEvent, feature_snapshot: CausalFeatureSnapshot) -> object:
        del event, feature_snapshot
        self.process_calls += 1
        return SimpleNamespace(bundle=SimpleNamespace(bundle_id="bundle-live"))


class FakeOrchestrator:
    def __init__(self, runner: FakeRunner) -> None:
        self.runner = runner
        self.latest_plan = DecisionPlan()

    def process_event(
        self, event: RuntimeEvent, *, feature_snapshot: CausalFeatureSnapshot
    ) -> DecisionCycle:
        self.runner.process(event, feature_snapshot)
        return DecisionCycle(
            event_id=event.event_id,
            event_type=event.event_type,
            available_at=event.available_at,
        )


def test_quiet_shadow_cycle_uses_shared_specialist_and_decision_path(tmp_path: Path) -> None:
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = FakeRunner()
    runtime = LiveShadowRuntime(
        orchestrator=FakeOrchestrator(runner),  # type: ignore[arg-type]
        runner=runner,  # type: ignore[arg-type]
        journal=journal,
        symbol="XAUUSD",
        feature_manifest_id="fm-shadow",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
    )

    outcome = runtime.process(_event(), _snapshot(candidate=False))

    assert outcome.scan.result is CandidateResult.NO_SETUP
    assert outcome.shadow_cycle.stage is ShadowCycleStage.QUIET
    assert outcome.decision_cycle is not None
    assert runner.quiet_calls == 0
    assert runner.process_calls == 1
    types = tuple(item.record.record_type for item in journal.records())
    assert types == (
        JournalRecordType.M15_CONTEXT,
        JournalRecordType.M5_CANDIDATE_SCAN,
        JournalRecordType.SHADOW_RUNTIME_CYCLE,
    )


def test_candidate_shadow_cycle_enters_existing_processor_once(tmp_path: Path) -> None:
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = FakeRunner()
    runtime = LiveShadowRuntime(
        orchestrator=FakeOrchestrator(runner),  # type: ignore[arg-type]
        runner=runner,  # type: ignore[arg-type]
        journal=journal,
        symbol="XAUUSD",
        feature_manifest_id="fm-shadow",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
    )

    outcome = runtime.process(_event(), _snapshot(candidate=True))

    assert outcome.scan.result is CandidateResult.CANDIDATE
    assert outcome.shadow_cycle.stage is ShadowCycleStage.SETUP_DETECTED
    assert runner.quiet_calls == 0
    assert runner.process_calls == 1


def test_stale_availability_is_journaled_without_scanner_specialists_or_execution(
    tmp_path: Path,
) -> None:
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = FakeRunner()
    runtime = LiveShadowRuntime(
        orchestrator=FakeOrchestrator(runner),  # type: ignore[arg-type]
        runner=runner,  # type: ignore[arg-type]
        journal=journal,
        symbol="XAUUSD",
        feature_manifest_id="fm-shadow",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
    )
    availability = ShadowMarketAvailability(
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        observed_at=T0,
        available_at=T0,
        broker_tick_at=T0.replace(day=12),
        status=LiveMarketStatus.STALE_QUOTE,
        reason_code="STALE_QUOTE",
    )

    assert runtime.record_availability(availability) is True
    repeated = availability.model_copy(
        update={
            "availability_id": "",
            "observed_at": T0.replace(second=2),
            "available_at": T0.replace(second=2),
        }
    )
    repeated = ShadowMarketAvailability.model_validate(repeated.model_dump())
    assert runtime.record_availability(repeated) is False

    assert runner.quiet_calls == 0
    assert runner.process_calls == 0
    records = journal.records()
    assert len(records) == 1
    assert records[0].record.record_type is JournalRecordType.SHADOW_MARKET_AVAILABILITY
