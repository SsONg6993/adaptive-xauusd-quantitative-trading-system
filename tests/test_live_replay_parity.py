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
    AccountState,
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


def test_post_expiry_successor_has_live_replay_semantic_parity() -> None:
    events = (
        _event(T0, 1),
        _event(T0 + timedelta(minutes=5), 2),
        _event(T0 + timedelta(minutes=10), 3),
    )
    snapshots = {event.event_id: _snapshot(event) for event in events}

    def rollover_transition(
        event: RuntimeEvent,
        bundle: EvidenceBundle,
        previous: ThesisState | None,
    ) -> ThesisState | None:
        return update_scenario(
            event,
            bundle.input_for("chart"),
            bundle.by_agent("chart"),
            previous,
            policy=ScenarioPolicy(ttl_seconds=300, max_m5_bars=3),
            scenario_definitions=DEFINITIONS,
        )

    live = RuntimeStreamRunner(
        _kernel(),
        SystemUTCClock(),
        scenario_transition=rollover_transition,
    )
    replay = RuntimeStreamRunner(
        _kernel(),
        ReplayClock(T0),
        scenario_transition=rollover_transition,
    )
    first_thesis_id = None
    for index, event in enumerate(events):
        live.process(event, snapshots[event.event_id])
        replay.process(event, snapshots[event.event_id])
        if index == 0:
            assert live.thesis is not None
            first_thesis_id = live.thesis.thesis_id

    assert live.steps == replay.steps
    assert live.thesis == replay.thesis
    assert live.thesis is not None
    assert live.thesis.thesis_id != first_thesis_id
    assert live.thesis.supersedes_thesis_id == first_thesis_id


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


def test_runtime_runner_can_retain_only_attribution_semantics(tmp_path) -> None:
    event = _event(T0, 1)
    snapshot = _snapshot(event)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = RuntimeStreamRunner(
        _kernel(),
        ReplayClock(T0),
        journal=journal,
        retained_record_types=frozenset({JournalRecordType.AGENT_EVIDENCE}),
    )

    filtered = runner.process(event, snapshot)
    unjournaled = RuntimeStreamRunner(_kernel(), ReplayClock(T0)).process(
        event,
        snapshot,
    )

    assert filtered == unjournaled
    records = journal.records()
    assert len(records) == len(AGENT_ORDER)
    assert {item.record.record_type for item in records} == {
        JournalRecordType.AGENT_EVIDENCE
    }
    assert tuple(item.record.semantic_id for item in records) == tuple(
        item.evidence_id for item in filtered.bundle.evidence
    )


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


def test_mixed_accepted_rejected_and_duplicate_events_replay_original_trace(
    tmp_path,
) -> None:
    first = _event(T0, 1)
    collision = _event(T0 + timedelta(minutes=5), 1)
    second = _event(T0 + timedelta(minutes=10), 2)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = RuntimeStreamRunner(_kernel(), ReplayClock(T0), journal=journal)

    first_step = runner.process(first, _snapshot(first))
    assert runner.process(first, _snapshot(first)) == first_step
    with pytest.raises(ValueError, match="source sequence collision"):
        runner.process(collision, _snapshot(collision))
    second_step = runner.process(second, _snapshot(second))

    replayed = run_event_stream(
        JournalEventSource(journal),
        _kernel(),
        ReplayClock(T0),
        snapshots=journal.feature_snapshots(),
    )

    assert tuple(event.event_id for event in journal.events()) == (
        first.event_id,
        second.event_id,
    )
    assert tuple(step.bundle_id for step in replayed.steps) == (
        first_step.bundle_id,
        second_step.bundle_id,
    )


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


def test_reduce_only_broker_refresh_preserves_next_decision_semantics() -> None:
    first = _event(T0, 1)
    second = _event(T0 + timedelta(minutes=5), 3)
    at = T0 + timedelta(minutes=1)
    account_event = RuntimeEvent(
        event_type=RuntimeEventType.ACCOUNT_UPDATED,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="replay-account",
        source_version="1.0",
        source_sequence=2,
        symbol="XAUUSD",
        payload=AccountState(
            source="replay-account",
            account_id="replay",
            as_of=at,
            freshness=ComponentFreshness(
                component="account",
                status=FreshnessStatus.AVAILABLE,
                observed_at=at,
                available_at=at,
                stale_after_ms=300_000,
            ),
            balance=10_000.0,
            equity=10_000.0,
            free_margin=10_000.0,
            used_margin=0.0,
            margin_level=1_000_000.0,
        ),
    )
    evaluated = _kernel()
    reduced = _kernel()
    evaluated.process(first, feature_snapshot=_snapshot(first))
    reduced.process(first, feature_snapshot=_snapshot(first))

    evaluated.process(account_event)
    reduced.reduce_event(account_event)

    evaluated_next = evaluated.process(second, feature_snapshot=_snapshot(second))
    reduced_next = reduced.process(second, feature_snapshot=_snapshot(second))
    assert evaluated.state == reduced.state
    assert evaluated_next.bundle_id == reduced_next.bundle_id


def test_broker_refresh_is_journaled_without_semantic_or_scenario_work(tmp_path) -> None:
    decision = _event(T0, 1)
    at = T0 + timedelta(minutes=1)
    account_event = RuntimeEvent(
        event_type=RuntimeEventType.ACCOUNT_UPDATED,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="mt5-snapshot",
        source_version="1.0",
        source_sequence=2,
        symbol="XAUUSD",
        payload=AccountState(
            source="mt5-snapshot",
            account_id="demo",
            as_of=at,
            freshness=ComponentFreshness(
                component="account",
                status=FreshnessStatus.AVAILABLE,
                observed_at=at,
                available_at=at,
                stale_after_ms=300_000,
            ),
            balance=10_000.0,
            equity=10_000.0,
            free_margin=10_000.0,
            used_margin=0.0,
        ),
    )
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    runner = RuntimeStreamRunner(
        _kernel(),
        ReplayClock(T0),
        journal=journal,
        scenario_transition=_scenario_transition,
    )
    runner.process(decision, _snapshot(decision))
    prior_steps = runner.steps
    prior_thesis = runner.thesis

    state = runner.reduce_broker_refresh(account_event)

    assert state.account == account_event.payload
    assert runner.steps == prior_steps
    assert runner.thesis == prior_thesis
    records = journal.records()
    matching = [item.record for item in records if item.record.event_id == account_event.event_id]
    assert tuple(item.record_type for item in matching) == (
        JournalRecordType.RUNTIME_EVENT,
        JournalRecordType.RUNTIME_STATE,
        JournalRecordType.OUTCOME,
    )
    outcome = JournalOutcome.model_validate(matching[-1].decode())
    assert outcome.status is JournalOutcomeStatus.APPLIED
    assert outcome.reason_code == "BROKER_REFRESH_APPLIED"


@pytest.mark.parametrize(
    "event_type",
    (
        RuntimeEventType.M5_CLOSED,
        RuntimeEventType.M1_CLOSED,
        RuntimeEventType.HTF_CLOSED,
    ),
)
def test_broker_refresh_rejects_decision_and_context_bar_events(
    tmp_path, event_type: RuntimeEventType
) -> None:
    market = _event(T0, 1).payload
    event = RuntimeEvent(
        event_type=event_type,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
        source="mt5-snapshot",
        source_version="1.0",
        source_sequence=1,
        symbol="XAUUSD",
        payload=market,
    )
    runner = RuntimeStreamRunner(
        _kernel(),
        ReplayClock(T0),
        journal=SQLiteRuntimeJournal(tmp_path / f"{event_type.value}.sqlite3"),
    )

    with pytest.raises(ValueError, match="rejects non-snapshot"):
        runner.reduce_broker_refresh(event)

    assert runner.steps == ()


def test_broker_snapshot_tick_is_state_only_but_live_tick_remains_semantic() -> None:
    scenario_events: list[RuntimeEventType] = []

    def scenario_transition(event, bundle, previous):
        del bundle
        scenario_events.append(event.event_type)
        return previous

    runner = RuntimeStreamRunner(
        _kernel(),
        ReplayClock(T0),
        scenario_transition=scenario_transition,
    )
    market = _event(T0, 1).payload
    snapshot_tick = RuntimeEvent(
        event_type=RuntimeEventType.TICK,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
        source="mt5-snapshot",
        source_version="1.0",
        source_sequence=1,
        symbol="XAUUSD",
        payload=market,
    )
    live_at = T0 + timedelta(seconds=1)
    live_market = market.model_copy(update={"as_of": live_at})
    live_tick = RuntimeEvent(
        event_type=RuntimeEventType.TICK,
        event_time=live_at,
        observed_at=live_at,
        available_at=live_at,
        source="mt5-live-events",
        source_version="1.0",
        source_sequence=1,
        symbol="XAUUSD",
        payload=live_market,
    )

    runner.reduce_broker_refresh(snapshot_tick)
    assert scenario_events == []
    assert runner.steps == ()

    runner.process(live_tick, None)
    assert scenario_events == [RuntimeEventType.TICK]
    assert len(runner.steps) == 1
