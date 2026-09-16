"""Live-shadow processor decorator for advisory interaction persistence."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, cast

from axq.interaction.service import SpecialistResponder, build_evidence_bound_interaction
from axq.master import FusionPolicy, fuse_evidence
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
        proposal = fuse_evidence(trace.bundle, self._fusion_policy)
        scan_id = self._scan_id_for_event(event.event_id)
        session = None
        if scan_id is not None:
            session = build_evidence_bound_interaction(
                bundle=trace.bundle,
                proposal=proposal,
                policy=self._fusion_policy,
                scan_id=scan_id,
                available_at=event.available_at,
                responder=self._responder,
            )
            self._append(session.assessment, event.event_id)
            if session.round is not None:
                self._append(session.round, event.event_id)
                for turn in session.turns:
                    self._append(turn, event.event_id)

        plan = self._delegate.evaluate(event, state, trace, readiness, controls)
        if session is None or session.resolution is None:
            return plan
        if plan.master is None or plan.master.proposal_id != proposal.proposal_id:
            return plan
        self._append(session.resolution, event.event_id)
        return plan.model_copy(
            update={"interaction_resolution_id": session.resolution.resolution_id}
        )
