from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.agents import (
    ContinuityStatus,
    EntryEligibility,
    ScenarioDefinition,
    ScenarioPolicy,
    ThesisState,
    update_scenario,
)
from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    InMemoryEventSource,
    MarketState,
    ReplayClock,
    RuntimeEvent,
    RuntimeEventType,
    SystemUTCClock,
    initial_runtime_state,
)
from axq.runtime.journal import (
    JournalOutcome,
    JournalOutcomeStatus,
    JournalRecordType,
    SQLiteRuntimeJournal,
)
from axq.runtime.kernel import AGENT_ORDER, EvidenceBundle, EvidenceKernel
from axq.runtime.replay import JournalEventSource, RuntimeStreamRunner, run_event_stream
from axq.tools import (
    CausalFeatureSnapshot,
    FeatureFactTool,
    ToolCatalog,
    ToolCategory,
)

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
POLICY = ScenarioPolicy(ttl_seconds=900, max_m5_bars=3)
DEFINITIONS = (
    ScenarioDefinition(
        name="continuation",
        confirmation_facts=("structure_bos_up",),
    ),
)


def _event(at: datetime, sequence: int) -> RuntimeEvent:
    freshness = ComponentFreshness(
        component="market",
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=300_000,
    )
    return RuntimeEvent(
        event_type=RuntimeEventType.M5_CLOSED,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="mt5",
        source_version="1.0.0",
        source_sequence=sequence,
        symbol="XAUUSD",
        payload=MarketState(
            source="mt5",
            symbol="XAUUSD",
            as_of=at,
            freshness=freshness,
            bid=2500.0 + sequence,
            ask=2500.2 + sequence,
            last=2500.1 + sequence,
            spread_points=20.0,
            base_timeframe="M5",
            completed_timeframes=("M5",),
            feature_manifest_id="fm-test",
        ),
    )


def _snapshot(event: RuntimeEvent, *, bos_up: bool = True) -> CausalFeatureSnapshot:
    return CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=event.available_at,
        available_at=event.available_at,
        feature_manifest_id="fm-test",
        completed_timeframes=("M5",),
        values={
            "h4_structure_bias": 1.0,
            "h1_structure_bias": 1.0,
            "structure_bos_up": bos_up,
            "trend_close_to_ema_20": 0.004,
            "trend_adx_14": 31.0,
            "statistics_efficiency_ratio_20": 0.58,
        },
        source="phase2-feature-engine",
        source_version="2.0.0",
    )


def _kernel() -> EvidenceKernel:
    tools = (
        FeatureFactTool(
            name="structure.core",
            category=ToolCategory.STRUCTURE,
            feature_names=(
                "h4_structure_bias",
                "h1_structure_bias",
                "structure_bos_up",
            ),
        ),
        FeatureFactTool(
            name="trend.core",
            category=ToolCategory.TREND,
            feature_names=("trend_close_to_ema_20", "trend_adx_14"),
        ),
        FeatureFactTool(
            name="statistics.core",
            category=ToolCategory.STATISTICS,
            feature_names=("statistics_efficiency_ratio_20",),
        ),
    )
    return EvidenceKernel(
        initial_state=initial_runtime_state("XAUUSD", at=T0),
        catalog=ToolCatalog(tools),
        tool_access={
            "chart": ("structure.core",),
            "quant": ("trend.core",),
            "historical": (),
            "regime": ("trend.core", "statistics.core"),
            "news": (),
        },
    )


def _scenario_transition(
    event: RuntimeEvent,
    bundle: EvidenceBundle,
    previous: ThesisState | None,
) -> ThesisState | None:
    return update_scenario(
        event,
        bundle.input_for("chart"),
        bundle.by_agent("chart"),
        previous,
        policy=POLICY,
        scenario_definitions=DEFINITIONS if previous is None else (),
    )


def test_live_like_and_replay_use_same_kernel_and_semantic_ids() -> None:
    events = (_event(T0, 1), _event(T0 + timedelta(minutes=5), 2))
    snapshots = {event.event_id: _snapshot(event) for event in events}

    live = run_event_stream(
        InMemoryEventSource(events),
        _kernel(),
        SystemUTCClock(),
        snapshots=snapshots,
        scenario_transition=_scenario_transition,
    )
    replay_clock = ReplayClock(T0)
    replay = run_event_stream(
        InMemoryEventSource(reversed(events)),
        _kernel(),
        replay_clock,
        snapshots=snapshots,
        scenario_transition=_scenario_transition,
    )

    assert live.steps == replay.steps
    assert replay_clock.now() == events[-1].available_at
    assert live.steps[-1].thesis_state_id == replay.steps[-1].thesis_state_id
    assert live.steps[-1].scenario_state_ids == replay.steps[-1].scenario_state_ids
    assert live.steps[-1].entry_eligibility is EntryEligibility.ELIGIBLE


def test_journaled_events_replay_to_identical_bundle_ids(tmp_path) -> None:
    events = (_event(T0, 1), _event(T0 + timedelta(minutes=5), 2))
    snapshots = {event.event_id: _snapshot(event) for event in events}
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    original = run_event_stream(
        InMemoryEventSource(events),
        _kernel(),
        ReplayClock(T0),
        snapshots=snapshots,
        journal=journal,
    )

    replayed = run_event_stream(
        JournalEventSource(journal),
        _kernel(),
        ReplayClock(T0),
        snapshots=journal.feature_snapshots(),
    )

    assert tuple(item.bundle_id for item in original.steps) == tuple(
        item.bundle_id for item in replayed.steps
    )
    assert tuple(item.runtime_state_id for item in original.steps) == tuple(
        item.runtime_state_id for item in replayed.steps
    )


def test_duplicate_event_is_journaled_without_second_decision_record(tmp_path) -> None:
    event = _event(T0, 1)
    snapshot = _snapshot(event)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = RuntimeStreamRunner(
        _kernel(),
        ReplayClock(T0),
        journal=journal,
    )

    first = runner.process(event, snapshot)
    duplicate = runner.process(event, snapshot)

    assert duplicate == first
    records = journal.records()
    assert sum(
        item.record.record_type is JournalRecordType.EVIDENCE_BUNDLE
        for item in records
    ) == 1
    outcomes = [
        JournalOutcome.model_validate(item.record.decode())
        for item in records
        if item.record.record_type is JournalRecordType.OUTCOME
    ]
    assert outcomes[-1].status is JournalOutcomeStatus.DUPLICATE


def test_duplicate_event_with_different_snapshot_is_rejected_and_journaled(
    tmp_path,
) -> None:
    event = _event(T0, 1)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = RuntimeStreamRunner(_kernel(), ReplayClock(T0), journal=journal)
    runner.process(event, _snapshot(event, bos_up=True))

    with pytest.raises(ValueError, match="different feature snapshot"):
        runner.process(event, _snapshot(event, bos_up=False))

    outcomes = [
        JournalOutcome.model_validate(item.record.decode())
        for item in journal.records()
        if item.record.record_type is JournalRecordType.OUTCOME
    ]
    assert outcomes[-1].status is JournalOutcomeStatus.REJECTED
    assert outcomes[-1].reason_code == "FEATURE_SNAPSHOT_MISMATCH"


def test_source_sequence_collision_is_explicitly_journaled(tmp_path) -> None:
    first = _event(T0, 1)
    collision = _event(T0 + timedelta(minutes=5), 1)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = RuntimeStreamRunner(_kernel(), ReplayClock(T0), journal=journal)
    runner.process(first, _snapshot(first))

    with pytest.raises(ValueError, match="source sequence collision"):
        runner.process(collision, _snapshot(collision))

    outcomes = [
        JournalOutcome.model_validate(item.record.decode())
        for item in journal.records()
        if item.record.record_type is JournalRecordType.OUTCOME
    ]
    assert outcomes[-1].reason_code == "SOURCE_SEQUENCE_COLLISION"


def test_scenario_continuity_status_is_preserved_in_journal(tmp_path) -> None:
    event = _event(T0, 1)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")

    def missing_continuity(
        current_event: RuntimeEvent,
        bundle: EvidenceBundle,
        previous: ThesisState | None,
    ) -> ThesisState | None:
        thesis = _scenario_transition(current_event, bundle, previous)
        assert thesis is not None
        body = thesis.model_dump(mode="python", exclude={"state_id"})
        body["continuity_status"] = ContinuityStatus.MISSING_INTRABAR_DATA
        return ThesisState.model_validate(body)

    runner = RuntimeStreamRunner(
        _kernel(),
        ReplayClock(T0),
        journal=journal,
        scenario_transition=missing_continuity,
    )
    step = runner.process(event, _snapshot(event))

    theses = [
        ThesisState.model_validate(item.record.decode())
        for item in journal.records()
        if item.record.record_type is JournalRecordType.THESIS_STATE
    ]
    assert step.thesis_state_id == theses[-1].state_id
    assert theses[-1].continuity_status is ContinuityStatus.MISSING_INTRABAR_DATA
    assert all(
        scenario.confirmation_progress == 0.0 for scenario in theses[-1].scenarios
    )


def test_specialist_inputs_remain_account_free_and_optional_ml_is_not_required() -> None:
    event = _event(T0, 1)
    run = run_event_stream(
        InMemoryEventSource((event,)),
        _kernel(),
        ReplayClock(T0),
        snapshots={event.event_id: _snapshot(event)},
    )
    bundle = run.steps[0].bundle

    assert bundle.by_agent("quant").status.value != "ERROR"
    assert tuple(item.agent_name for item in bundle.evidence) == AGENT_ORDER
    serialized = str(
        [item.model_dump(mode="json") for item in bundle.agent_inputs]
    ).lower()
    assert "balance" not in serialized
    assert "equity" not in serialized
