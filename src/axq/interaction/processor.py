"""Live-shadow processor decorator for advisory interaction persistence."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any, Protocol, cast

from axq.interaction.contracts import SpecialistInteractionImpact
from axq.interaction.service import SpecialistResponder, build_evidence_bound_interaction
from axq.master import FusionPolicy
from axq.orchestration.contracts import DecisionPlan
from axq.runtime.journal import JournalRecord, JournalSemantic, RuntimeJournal


class DecisionProcessor(Protocol):
    def evaluate(
        self,
        event: Any,
        state: Any,
        trace: Any,
        readiness: Any,
        controls: Any,
    ) -> DecisionPlan: ...


class EvidenceBoundInteractionProcessor:
    """Decorate Live Shadow only; final decisions still use the unmodified delegate."""

    def __init__(
        self,
        *,
        delegate: DecisionProcessor,
        fusion_policy: FusionPolicy,
        journal: RuntimeJournal,
        scan_id_for_event: Callable[[str], str | None],
        responder: SpecialistResponder | None = None,
    ) -> None:
        self._delegate = delegate
        self._fusion_policy = fusion_policy
        self._journal = journal
        self._scan_id_for_event = scan_id_for_event
        self._responder = responder
        self._last_discussion_latency_ms = 0.0

    @property
    def last_discussion_latency_ms(self) -> float:
        return self._last_discussion_latency_ms

    @property
    def last_master_latency_ms(self) -> float:
        return float(getattr(self._delegate, "last_master_latency_ms", 0.0))

    def _append(self, value: object, event_id: str) -> None:
        self._journal.append(
            JournalRecord.from_semantic(cast(JournalSemantic, value), event_id=event_id)
        )

    def evaluate(
        self,
        event: Any,
        state: Any,
        trace: Any,
        readiness: Any,
        controls: Any,
    ) -> DecisionPlan:
        self._last_discussion_latency_ms = 0.0
        plan = self._delegate.evaluate(event, state, trace, readiness, controls)
        proposal = plan.master
        if proposal is None:
            return plan
        scan_id = self._scan_id_for_event(event.event_id)
        session = None
        if scan_id is not None:
            discussion_started = perf_counter()
            session = build_evidence_bound_interaction(
                bundle=trace.bundle,
                proposal=proposal,
                policy=self._fusion_policy,
                scan_id=scan_id,
                available_at=event.available_at,
                responder=self._responder,
            )
            self._last_discussion_latency_ms = (
                perf_counter() - discussion_started
            ) * 1_000.0
            self._append(session.assessment, event.event_id)
            if session.round is not None:
                self._append(session.round, event.event_id)
                for turn in session.turns:
                    self._append(turn, event.event_id)

        if session is None or session.resolution is None:
            return plan
        if plan.master is None or plan.master.proposal_id != proposal.proposal_id:
            return plan
        self._append(session.resolution, event.event_id)
        impact = SpecialistInteractionImpact(
            discussion_id=session.round.round_id if session.round is not None else "unavailable",
            resolution_id=session.resolution.resolution_id,
            event_id=event.event_id,
            master_before_id=proposal.proposal_id,
            master_after_id=plan.master.proposal_id,
            confidence_before=proposal.confidence,
            confidence_after=plan.master.confidence,
            confidence_delta=plan.master.confidence - proposal.confidence,
            stance_before=proposal.decision,
            stance_after=plan.master.decision,
            stance_changed=proposal.decision is not plan.master.decision,
            final_reason=(
                "Evidence-bound discussion preserved the immutable initial evidence; "
                "no decision re-synthesis was authorized."
            ),
            as_of=proposal.as_of,
            available_at=event.available_at,
        )
        self._append(impact, event.event_id)
        return plan.model_copy(
            update={"interaction_resolution_id": session.resolution.resolution_id}
        )
