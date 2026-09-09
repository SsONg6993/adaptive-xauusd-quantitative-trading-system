from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.agents import AgentStatus, DirectionalBias, HypothesisRelationship
from axq.discipline import (
    DisciplineContext,
    DisciplineOutcome,
    DisciplinePosition,
    DisciplineResult,
    DisciplineState,
    DuplicateStatus,
    EntryIntent,
    LossStreakReset,
    ReentryPolicy,
    ReentryStatus,
    default_demo_discipline_policy,
    evaluate_discipline,
)
from axq.master import (
    EvidenceDisposition,
    FusionReason,
    MasterProposal,
    SpecialistContribution,
)
from axq.runtime.kernel import AGENT_ORDER
from axq.schemas import Signal

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _proposal(signal: Signal = Signal.BUY, *, event_id: str = "ev-discipline") -> MasterProposal:
    direction = {
        Signal.BUY: DirectionalBias.BULLISH,
        Signal.SELL: DirectionalBias.BEARISH,
        Signal.HOLD: None,
    }[signal]
    contributions = tuple(
        SpecialistContribution(
            agent_name=name,
            evidence_id=f"ae-{name}-{event_id}",
            status=AgentStatus.READY,
            direction=direction if name == "chart" and signal is not Signal.HOLD else None,
            disposition=(
                EvidenceDisposition.CONTRIBUTED
                if name == "chart" and signal is not Signal.HOLD
                else EvidenceDisposition.CONTEXT_ONLY
            ),
            configured_weight=1.0,
            applied_weight=1.0 if name == "chart" and signal is not Signal.HOLD else 0.0,
            effective_strength=0.8 if name == "chart" and signal is not Signal.HOLD else 0.0,
            signed_score=(
                0.8
                if signal is Signal.BUY and name == "chart"
                else -0.8
                if signal is Signal.SELL and name == "chart"
                else 0.0
            ),
            uncertainty=0.1,
            internal_contradiction=0.0,
        )
        for name in AGENT_ORDER
    )
    actionable = signal is not Signal.HOLD
    return MasterProposal(
        bundle_id=f"eb-{event_id}",
        event_id=event_id,
        runtime_state_id="state-discipline",
        as_of=T0,
        policy_id="mfp-fixture",
        policy_version="1.0.0",
        decision=signal,
        actionable=actionable,
        confidence=0.8 if actionable else 0.0,
        net_score=0.8 if signal is Signal.BUY else -0.8 if signal is Signal.SELL else 0.0,
        bullish_score=0.8 if signal is Signal.BUY else 0.0,
        bearish_score=0.8 if signal is Signal.SELL else 0.0,
        contradiction=0.0,
        disagreement=0.0,
        uncertainty=0.1,
        ready_directional_agents=1 if actionable else 0,
        contributing_evidence_ids=(f"ae-chart-{event_id}",) if actionable else (),
        contributions=contributions,
        reason_codes=(
            (FusionReason.ACTIONABLE_BUY,)
            if signal is Signal.BUY
            else (FusionReason.ACTIONABLE_SELL,)
            if signal is Signal.SELL
            else (FusionReason.NO_READY_DIRECTIONAL_EVIDENCE,)
        ),
    )


def _policy(**changes: object):
    policy = default_demo_discipline_policy()
    return type(policy).model_validate(
        policy.model_dump() | {"policy_id": ""} | changes
    )


def _state(policy_id: str, **changes: object) -> DisciplineState:
    base: dict[str, object] = {
        "policy_id": policy_id,
        "as_of": T0,
        "available_at": T0,
        "trading_day": T0.date(),
        "session_id": "london",
        "trades_today": 0,
        "trades_this_session": 0,
        "consecutive_losses": 0,
    }
    return DisciplineState.model_validate(base | changes)


def _context(**changes: object) -> DisciplineContext:
    base: dict[str, object] = {
        "as_of": T0,
        "available_at": T0,
        "trading_day": T0.date(),
        "session_id": "london",
        "setup_id": "setup-new",
        "thesis_id": "thesis-new",
        "scenario_id": "scenario-new",
        "thesis_relationship": HypothesisRelationship.NEW,
        "entry_intent": EntryIntent.INITIAL,
    }
    return DisciplineContext.model_validate(base | changes)


def test_master_hold_becomes_no_action_not_rejection() -> None:
    policy = default_demo_discipline_policy()

    outcome = evaluate_discipline(
        _proposal(Signal.HOLD), _context(), _state(policy.policy_id), policy
    )

    assert outcome.result is DisciplineResult.NO_ACTION
    assert outcome.eligible_for_risk is False
    assert outcome.duplicate_status is DuplicateStatus.NONE


@pytest.mark.parametrize("signal", [Signal.BUY, Signal.SELL])
def test_clear_actionable_proposal_passes_loose_demo_policy(signal: Signal) -> None:
    policy = default_demo_discipline_policy()

    outcome = evaluate_discipline(
        _proposal(signal), _context(), _state(policy.policy_id), policy
    )

    assert outcome.result is DisciplineResult.PASS
    assert outcome.eligible_for_risk is True


def test_duplicate_setup_is_rejected_even_after_cooldown() -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        recently_executed_setup_ids=("setup-new",),
        last_entry_at=T0 - timedelta(hours=1),
    )

    outcome = evaluate_discipline(_proposal(), _context(), state, policy)

    assert outcome.result is DisciplineResult.REJECT
    assert outcome.duplicate_status is DuplicateStatus.DUPLICATE_SETUP


def test_same_thesis_continuation_is_rejected_as_duplicate() -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        recently_executed_thesis_ids=("thesis-new",),
    )

    outcome = evaluate_discipline(
        _proposal(),
        _context(thesis_relationship=HypothesisRelationship.UNCHANGED),
        state,
        policy,
    )

    assert outcome.result is DisciplineResult.REJECT
    assert outcome.duplicate_status is DuplicateStatus.DUPLICATE_THESIS


@pytest.mark.parametrize(
    "relationship",
    [HypothesisRelationship.NEW, HypothesisRelationship.REVERSED],
)
def test_genuinely_distinct_new_or_reversed_thesis_is_allowed(
    relationship: HypothesisRelationship,
) -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        recently_executed_thesis_ids=("thesis-old",),
    )

    outcome = evaluate_discipline(
        _proposal(), _context(thesis_relationship=relationship), state, policy
    )

    assert outcome.result is DisciplineResult.PASS


def test_valid_reentry_requires_new_setup_recorded_exit_and_elapsed_cooldown() -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        recently_executed_setup_ids=("setup-old",),
        recently_executed_thesis_ids=("thesis-new",),
        last_exit_at=T0 - timedelta(minutes=10),
        last_entry_direction=Signal.BUY,
    )

    outcome = evaluate_discipline(
        _proposal(),
        _context(entry_intent=EntryIntent.REENTRY),
        state,
        policy,
    )

    assert outcome.result is DisciplineResult.PASS
    assert outcome.reentry_status is ReentryStatus.ALLOWED


def test_reentry_with_same_setup_remains_a_duplicate() -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        recently_executed_setup_ids=("setup-new",),
        recently_executed_thesis_ids=("thesis-new",),
        last_exit_at=T0 - timedelta(minutes=10),
        last_entry_direction=Signal.BUY,
    )

    outcome = evaluate_discipline(
        _proposal(), _context(entry_intent=EntryIntent.REENTRY), state, policy
    )

    assert outcome.result is DisciplineResult.REJECT
    assert outcome.duplicate_status is DuplicateStatus.DUPLICATE_SETUP


def test_disabled_reentry_policy_rejects_explicit_reentry() -> None:
    policy = _policy(reentry_policy=ReentryPolicy.DISABLED)
    state = _state(
        policy.policy_id,
        recently_executed_thesis_ids=("thesis-new",),
        last_exit_at=T0 - timedelta(minutes=10),
    )

    outcome = evaluate_discipline(
        _proposal(), _context(entry_intent=EntryIntent.REENTRY), state, policy
    )

    assert outcome.result is DisciplineResult.REJECT
    assert outcome.reentry_status is ReentryStatus.POLICY_BLOCKED


def test_ordinary_and_stop_loss_cooldowns_are_causal_and_expire() -> None:
    policy = default_demo_discipline_policy()
    ordinary = _state(policy.policy_id, last_entry_at=T0 - timedelta(seconds=30))
    stopped = _state(policy.policy_id, last_stop_loss_at=T0 - timedelta(minutes=2))
    expired = _state(policy.policy_id, last_stop_loss_at=T0 - timedelta(minutes=6))

    ordinary_outcome = evaluate_discipline(_proposal(), _context(), ordinary, policy)
    stopped_outcome = evaluate_discipline(_proposal(), _context(), stopped, policy)
    expired_outcome = evaluate_discipline(_proposal(), _context(), expired, policy)

    assert ordinary_outcome.result is DisciplineResult.REJECT
    assert ordinary_outcome.next_eligible_at == T0 + timedelta(seconds=30)
    assert stopped_outcome.result is DisciplineResult.REJECT
    assert stopped_outcome.next_eligible_at == T0 + timedelta(minutes=3)
    assert expired_outcome.result is DisciplineResult.PASS


@pytest.mark.parametrize(
    ("state_changes", "counter_name"),
    [
        ({"trades_today": 16}, "trades_today"),
        ({"trades_this_session": 10}, "trades_this_session"),
    ],
)
def test_daily_and_session_caps_reject_without_becoming_risk_rules(
    state_changes: dict[str, object],
    counter_name: str,
) -> None:
    policy = default_demo_discipline_policy()

    outcome = evaluate_discipline(
        _proposal(), _context(), _state(policy.policy_id, **state_changes), policy
    )

    assert outcome.result is DisciplineResult.REJECT
    assert getattr(outcome.counters, counter_name) == next(iter(state_changes.values()))


def test_loss_streak_pause_and_expiry_are_distinct_from_rejection() -> None:
    policy = default_demo_discipline_policy()
    active = _state(
        policy.policy_id,
        consecutive_losses=3,
        last_stop_loss_at=T0 - timedelta(minutes=5),
    )
    expired = _state(
        policy.policy_id,
        consecutive_losses=3,
        last_stop_loss_at=T0 - timedelta(minutes=20),
    )

    paused = evaluate_discipline(_proposal(), _context(), active, policy)
    resumed = evaluate_discipline(_proposal(), _context(), expired, policy)

    assert paused.result is DisciplineResult.PAUSE
    assert paused.next_eligible_at == T0 + timedelta(minutes=10)
    assert resumed.result is DisciplineResult.PASS


def test_persisted_pause_is_causal_and_expires() -> None:
    policy = default_demo_discipline_policy()
    active = _state(
        policy.policy_id,
        paused_until=T0 + timedelta(minutes=2),
        pause_reason="manual behavioral review",
    )
    expired = _state(policy.policy_id, paused_until=T0)

    paused = evaluate_discipline(_proposal(), _context(), active, policy)
    resumed = evaluate_discipline(_proposal(), _context(), expired, policy)

    assert paused.result is DisciplineResult.PAUSE
    assert paused.next_eligible_at == T0 + timedelta(minutes=2)
    assert resumed.result is DisciplineResult.PASS


def test_optional_post_rejection_and_same_direction_reentry_cooldowns() -> None:
    policy = _policy(post_rejection_cooldown_seconds=30)
    after_rejection = _state(
        policy.policy_id,
        last_rejection_at=T0 - timedelta(seconds=10),
    )
    reentry = _state(
        policy.policy_id,
        recently_executed_thesis_ids=("thesis-new",),
        last_exit_at=T0 - timedelta(minutes=2),
        last_entry_direction=Signal.BUY,
    )

    rejected = evaluate_discipline(_proposal(), _context(), after_rejection, policy)
    reentry_rejected = evaluate_discipline(
        _proposal(), _context(entry_intent=EntryIntent.REENTRY), reentry, policy
    )

    assert rejected.result is DisciplineResult.REJECT
    assert rejected.next_eligible_at == T0 + timedelta(seconds=20)
    assert reentry_rejected.result is DisciplineResult.REJECT
    assert reentry_rejected.reentry_status is ReentryStatus.COOLDOWN


def test_policy_declares_how_consecutive_loss_state_resets() -> None:
    policy = default_demo_discipline_policy()

    assert policy.loss_streak_reset is LossStreakReset.AFTER_NON_LOSS_EXIT


def test_demo_defaults_allow_meaningful_sample_collection_below_caps() -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        trades_today=15,
        trades_this_session=9,
    )

    outcome = evaluate_discipline(_proposal(), _context(), state, policy)
    assert outcome.result is DisciplineResult.PASS


def test_bounded_position_awareness_blocks_same_direction_without_financial_data() -> None:
    policy = _policy(max_simultaneous_positions=2)
    state = _state(
        policy.policy_id,
        active_positions=(
            DisciplinePosition(
                position_ref="position-1",
                direction=Signal.BUY,
                setup_id="setup-old",
                thesis_id="thesis-old",
                opened_at=T0 - timedelta(minutes=10),
            ),
        ),
        active_setup_ids=("setup-old",),
        active_thesis_ids=("thesis-old",),
    )

    outcome = evaluate_discipline(_proposal(), _context(), state, policy)

    assert outcome.result is DisciplineResult.REJECT
    assert outcome.counters.active_positions == 1
    dumped = state.model_dump()
    assert not {"balance", "equity", "margin", "volume_lots"} & set(dumped)


def test_bounded_position_count_cap_is_enforced_independently_of_direction() -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        active_positions=(
            DisciplinePosition(
                position_ref="position-1",
                direction=Signal.SELL,
                opened_at=T0 - timedelta(minutes=10),
            ),
        ),
    )

    outcome = evaluate_discipline(_proposal(Signal.BUY), _context(), state, policy)

    assert outcome.result is DisciplineResult.REJECT
    assert outcome.counters.active_positions == 1


def test_rejected_outcome_retains_proposal_bundle_policy_and_setup_provenance() -> None:
    policy = default_demo_discipline_policy()
    proposal = _proposal(event_id="ev-provenance")
    context = _context()
    state = _state(policy.policy_id, recently_executed_setup_ids=("setup-new",))

    outcome = evaluate_discipline(proposal, context, state, policy)

    assert outcome.master_proposal_id == proposal.proposal_id
    assert outcome.evidence_bundle_id == proposal.bundle_id
    assert outcome.discipline_policy_id == policy.policy_id
    assert outcome.setup_id == context.setup_id
    assert outcome.thesis_id == context.thesis_id
    assert outcome.scenario_id == context.scenario_id


def test_policy_state_and_outcome_identities_are_content_addressed() -> None:
    policy = default_demo_discipline_policy()
    same_policy = type(policy).model_validate_json(policy.model_dump_json())
    state = _state(policy.policy_id)
    same_state = DisciplineState.model_validate_json(state.model_dump_json())
    proposal = _proposal()
    context = _context()

    first = evaluate_discipline(proposal, context, state, policy)
    second = evaluate_discipline(proposal, context, same_state, same_policy)
    changed_policy = _policy(max_trades_per_day=20)

    assert same_policy.policy_id == policy.policy_id
    assert same_state.state_id == state.state_id
    assert second.outcome_id == first.outcome_id
    assert evaluate_discipline(
        proposal,
        context,
        _state(changed_policy.policy_id),
        changed_policy,
    ).outcome_id != first.outcome_id


def test_operational_recorded_at_is_excluded_from_state_identity() -> None:
    policy = default_demo_discipline_policy()
    first = _state(policy.policy_id, recorded_at=T0 + timedelta(seconds=1))
    second = _state(policy.policy_id, recorded_at=T0 + timedelta(seconds=2))

    assert first.state_id == second.state_id


def test_future_discipline_state_is_rejected_at_the_causal_boundary() -> None:
    policy = default_demo_discipline_policy()
    state = _state(
        policy.policy_id,
        as_of=T0 + timedelta(minutes=1),
        available_at=T0,
    )

    with pytest.raises(ValueError, match="causally available"):
        evaluate_discipline(_proposal(), _context(), state, policy)


def test_discipline_contracts_reject_naive_and_future_position_timestamps() -> None:
    policy = default_demo_discipline_policy()
    naive_context = _context().model_dump() | {
        "context_id": "",
        "as_of": datetime(2025, 1, 6, 12, 0),
    }

    with pytest.raises(ValidationError, match="timezone-aware"):
        DisciplineContext.model_validate(naive_context)

    with pytest.raises(ValidationError, match="position cannot open after state as_of"):
        _state(
            policy.policy_id,
            active_positions=(
                DisciplinePosition(
                    position_ref="future-position",
                    direction=Signal.BUY,
                    opened_at=T0 + timedelta(seconds=1),
                ),
            ),
        )


def test_live_and_replay_equivalent_inputs_produce_identical_outcome() -> None:
    policy = default_demo_discipline_policy()
    proposal = _proposal()
    context = _context()
    state = _state(policy.policy_id)

    live = evaluate_discipline(proposal, context, state, policy)
    replay = evaluate_discipline(
        MasterProposal.model_validate_json(proposal.model_dump_json()),
        DisciplineContext.model_validate_json(context.model_dump_json()),
        DisciplineState.model_validate_json(state.model_dump_json()),
        type(policy).model_validate_json(policy.model_dump_json()),
    )

    assert replay == live
    assert replay.outcome_id == live.outcome_id


def test_discipline_contracts_reject_risk_sizing_and_execution_fields() -> None:
    policy = default_demo_discipline_policy()
    outcome = evaluate_discipline(
        _proposal(), _context(), _state(policy.policy_id), policy
    )

    for forbidden in ("risk_fraction", "volume_lots", "broker_order"):
        with pytest.raises(ValidationError):
            DisciplineOutcome.model_validate(outcome.model_dump() | {forbidden: 1})


def test_guard_does_not_mutate_master_proposal() -> None:
    policy = default_demo_discipline_policy()
    proposal = _proposal()
    before = proposal.model_dump_json()

    evaluate_discipline(proposal, _context(), _state(policy.policy_id), policy)

    assert proposal.model_dump_json() == before
