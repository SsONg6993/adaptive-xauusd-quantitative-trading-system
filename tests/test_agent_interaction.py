from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axq.agents import DirectionalBias
from axq.interaction import (
    InteractionResolutionStatus,
    InteractionTurnType,
    SpecialistInteractionSession,
    build_evidence_bound_interaction,
)
from axq.interaction.processor import EvidenceBoundInteractionProcessor
from axq.master import default_fusion_policy, fuse_evidence
from axq.orchestration import DecisionPlan, OperatorControls
from axq.runtime.journal import JournalRecordType, SQLiteRuntimeJournal
from tests.test_master_fusion import _bundle, _evidence

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _conflicted_bundle():
    return _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH, confidence=0.9),
            "quant": _evidence("quant", DirectionalBias.BEARISH, confidence=0.85),
            "historical": _evidence(
                "historical", DirectionalBias.BULLISH, confidence=0.7
            ),
            "regime": _evidence("regime", DirectionalBias.BEARISH, confidence=0.75),
        }
    )


def test_no_high_disagreement_creates_no_interaction_round() -> None:
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH, confidence=0.85),
            "quant": _evidence("quant", DirectionalBias.BULLISH, confidence=0.75),
        }
    )
    policy = default_fusion_policy()

    session = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=fuse_evidence(bundle, policy),
        policy=policy,
        scan_id="scan-no-conflict",
        available_at=T0,
    )

    assert session.assessment.interaction_required is False
    assert session.round is None
    assert session.turns == ()


def test_high_disagreement_creates_one_bounded_evidence_only_round() -> None:
    bundle = _conflicted_bundle()
    policy = default_fusion_policy()
    proposal = fuse_evidence(bundle, policy)

    session = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=proposal,
        policy=policy,
        scan_id="scan-conflict",
        available_at=T0,
    )

    assert session.assessment.interaction_required is True
    assert session.assessment.measured_disagreement == proposal.disagreement
    assert session.assessment.disagreement_threshold == policy.maximum_actionable_disagreement
    assert session.round is not None
    assert session.round.maximum_rebuttals == 3
    assert len(session.round.participating_specialists) == 3
    assert len(session.turns) == 6
    assert tuple(item.turn_index for item in session.turns) == tuple(range(6))
    for challenge, rebuttal in zip(session.turns[::2], session.turns[1::2], strict=True):
        assert challenge.turn_type is InteractionTurnType.MASTER_CHALLENGE
        assert rebuttal.turn_type is InteractionTurnType.SPECIALIST_REBUTTAL
        assert rebuttal.predecessor_turn_id == challenge.turn_id
        original = bundle.by_agent(rebuttal.speaker)
        assert rebuttal.stance is original.direction
        assert rebuttal.confidence == original.confidence
        assert rebuttal.cited_evidence_ids == (original.evidence_id,)
        assert rebuttal.original_evidence_id == original.evidence_id
    assert session.resolution is not None
    assert session.resolution.status is InteractionResolutionStatus.COMPLETED
    assert session.resolution.unresolved_conflict is True


def test_interaction_is_content_addressed_and_replay_equivalent() -> None:
    bundle = _conflicted_bundle()
    policy = default_fusion_policy()
    proposal = fuse_evidence(bundle, policy)
    first = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=proposal,
        policy=policy,
        scan_id="scan-parity",
        available_at=T0,
    )
    second = build_evidence_bound_interaction(
        bundle=type(bundle).model_validate_json(bundle.model_dump_json()),
        proposal=type(proposal).model_validate_json(proposal.model_dump_json()),
        policy=type(policy).model_validate_json(policy.model_dump_json()),
        scan_id="scan-parity",
        available_at=T0,
    )

    assert second == first


def test_malformed_responder_fails_closed_without_partial_dialogue() -> None:
    class MalformedResponder:
        def respond(self, *, evidence, challenge):
            del evidence, challenge
            return {"stance": "BULLISH", "confidence": 1.0, "new_fact": "invented"}

    bundle = _conflicted_bundle()
    policy = default_fusion_policy()
    session = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=fuse_evidence(bundle, policy),
        policy=policy,
        scan_id="scan-malformed",
        available_at=T0,
        responder=MalformedResponder(),
    )

    assert session.resolution is not None
    assert session.resolution.status is InteractionResolutionStatus.MALFORMED
    assert session.resolution.unresolved_conflict is True
    assert len(session.turns) == 1


def test_timeout_fails_closed() -> None:
    class TimeoutResponder:
        def respond(self, *, evidence, challenge):
            del evidence, challenge
            raise TimeoutError("bounded interaction timeout")

    bundle = _conflicted_bundle()
    policy = default_fusion_policy()
    session = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=fuse_evidence(bundle, policy),
        policy=policy,
        scan_id="scan-timeout",
        available_at=T0,
        responder=TimeoutResponder(),
    )

    assert session.resolution is not None
    assert session.resolution.status is InteractionResolutionStatus.TIMED_OUT
    assert session.resolution.unresolved_conflict is True


def test_contract_rejects_confidence_increase_or_direction_reversal() -> None:
    bundle = _conflicted_bundle()
    policy = default_fusion_policy()

    class IncreasedConfidenceResponder:
        def respond(self, *, evidence, challenge):
            del challenge
            return {
                "stance": evidence.direction,
                "confidence": min(1.0, evidence.confidence + 0.01),
                "rationale": "Unsupported confidence increase.",
                "cited_evidence_ids": (evidence.evidence_id,),
            }

    session = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=fuse_evidence(bundle, policy),
        policy=policy,
        scan_id="scan-invalid-confidence",
        available_at=T0,
        responder=IncreasedConfidenceResponder(),
    )
    assert session.resolution is not None
    assert session.resolution.status is InteractionResolutionStatus.MALFORMED


@pytest.mark.parametrize("speaker", ["master", "chart"])
def test_no_recursive_or_specialist_to_specialist_turns_are_possible(speaker: str) -> None:
    from axq.interaction import SpecialistInteractionTurn

    with pytest.raises(ValueError):
        SpecialistInteractionTurn(
            round_id="sir-test",
            turn_index=0,
            speaker=speaker,
            recipient="quant",
            turn_type=InteractionTurnType.SPECIALIST_REBUTTAL,
            original_evidence_id="ae-test",
            stance=DirectionalBias.BULLISH,
            confidence=0.5,
            rationale="Invalid route.",
            cited_evidence_ids=("ae-test",),
            available_at=T0,
        )


def test_processor_persists_interaction_but_final_master_uses_original_bundle(tmp_path) -> None:
    bundle = _conflicted_bundle()
    policy = default_fusion_policy()
    original_master = fuse_evidence(bundle, policy)

    class Delegate:
        calls = 0

        def evaluate(self, event, state, trace, readiness, controls):
            del event, state, readiness, controls
            self.calls += 1
            assert trace.bundle is bundle
            return DecisionPlan(master=fuse_evidence(trace.bundle, policy))

    class Trace:
        def __init__(self) -> None:
            self.bundle = bundle

    class Event:
        event_id = bundle.event_id
        available_at = T0

    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    delegate = Delegate()
    processor = EvidenceBoundInteractionProcessor(
        delegate=delegate,
        fusion_policy=policy,
        journal=journal,
        scan_id_for_event=lambda event_id: (
            "scan-processor" if event_id == bundle.event_id else None
        ),
    )

    plan = processor.evaluate(Event(), object(), Trace(), None, OperatorControls())

    assert delegate.calls == 1
    assert plan.master == original_master
    assert plan.master is not None and plan.master.decision.value == "HOLD"
    assert plan.interaction_resolution_id is not None
    record_types = tuple(item.record.record_type for item in journal.records())
    assert record_types == (
        JournalRecordType.MASTER_CONFLICT_ASSESSMENT,
        JournalRecordType.SPECIALIST_INTERACTION_ROUND,
        JournalRecordType.SPECIALIST_INTERACTION_TURN,
        JournalRecordType.SPECIALIST_INTERACTION_TURN,
        JournalRecordType.SPECIALIST_INTERACTION_TURN,
        JournalRecordType.SPECIALIST_INTERACTION_TURN,
        JournalRecordType.SPECIALIST_INTERACTION_TURN,
        JournalRecordType.SPECIALIST_INTERACTION_TURN,
        JournalRecordType.SPECIALIST_INTERACTION_RESOLUTION,
        JournalRecordType.SPECIALIST_INTERACTION_IMPACT,
    )
    impact = journal.records()[-1].record.decode()
    assert impact.confidence_delta == 0.0
    assert impact.stance_changed is False
    assert impact.master_before_id == impact.master_after_id == original_master.proposal_id


def test_interaction_does_not_change_memory_or_evidence_bytes(tmp_path) -> None:
    bundle = _conflicted_bundle()
    before = bundle.model_dump_json()
    memories_before = tuple(item.model_dump_json() for item in bundle.memories)
    policy = default_fusion_policy()
    build_evidence_bound_interaction(
        bundle=bundle,
        proposal=fuse_evidence(bundle, policy),
        policy=policy,
        scan_id="scan-immutable",
        available_at=T0,
    )
    assert bundle.model_dump_json() == before
    assert tuple(item.model_dump_json() for item in bundle.memories) == memories_before


def test_session_contract_rejects_more_than_one_exchange_per_participant() -> None:
    bundle = _conflicted_bundle()
    policy = default_fusion_policy()
    session = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=fuse_evidence(bundle, policy),
        policy=policy,
        scan_id="scan-no-recursion",
        available_at=T0,
    )
    assert session.resolution is not None
    duplicated = (*session.turns, session.turns[0], session.turns[1])
    with pytest.raises(ValueError, match="one challenge and one rebuttal"):
        SpecialistInteractionSession(
            assessment=session.assessment,
            round=session.round,
            turns=duplicated,
            resolution=session.resolution.model_copy(
                update={
                    "resolution_id": "",
                    "ordered_turn_ids": tuple(item.turn_id for item in duplicated),
                }
            ),
        )
