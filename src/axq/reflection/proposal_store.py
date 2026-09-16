"""Append-only persistence for advisory improvement proposals."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from axq.database import Database
from axq.reflection.contracts import ReflectionModel
from axq.reflection.proposal_contracts import (
    ImprovementProposal,
    ImprovementProposalPolicy,
    ProposalStatus,
    ProposalStatusTransition,
)
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _payload(record: ReflectionModel) -> str:
    return json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


class SQLiteImprovementProposalStore:
    """Store immutable proposals and replay explicit lifecycle actions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)

    def append_policy(self, policy: ImprovementProposalPolicy) -> bool:
        payload = _payload(policy)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM improvement_proposal_policies WHERE policy_id = ?",
                (policy.policy_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("proposal policy ID already exists with different content")
            connection.execute(
                """
                INSERT INTO improvement_proposal_policies(
                    policy_id, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    policy.policy_id,
                    policy.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def append(self, proposal: ImprovementProposal) -> bool:
        payload = _payload(proposal)
        with self._database.transaction() as connection:
            policy = connection.execute(
                "SELECT 1 FROM improvement_proposal_policies WHERE policy_id = ?",
                (proposal.policy_id,),
            ).fetchone()
            if policy is None:
                raise ValueError("improvement proposal policy is not persisted")
            existing = connection.execute(
                "SELECT record_json FROM improvement_proposals WHERE proposal_id = ?",
                (proposal.proposal_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("proposal ID already exists with different content")
            latest = connection.execute(
                """
                SELECT proposal_id FROM improvement_proposals
                WHERE proposal_key = ? AND policy_id = ?
                ORDER BY proposal_sequence DESC LIMIT 1
                """,
                (proposal.proposal_key, proposal.policy_id),
            ).fetchone()
            if latest is None:
                if proposal.supersedes_proposal_id is not None:
                    raise ValueError("first proposal cannot supersede another record")
            elif proposal.supersedes_proposal_id != str(latest["proposal_id"]):
                raise ValueError("revised proposal must supersede latest record")
            connection.execute(
                """
                INSERT INTO improvement_proposals(
                    proposal_id, proposal_key, policy_id, target_component,
                    pattern_key, available_at, status, supersedes_proposal_id,
                    schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.proposal_id,
                    proposal.proposal_key,
                    proposal.policy_id,
                    proposal.target_component.value,
                    proposal.pattern_key,
                    proposal.available_at.isoformat(),
                    proposal.status.value,
                    proposal.supersedes_proposal_id,
                    proposal.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
            for guard in proposal.evidence_guards:
                guard_payload = _payload(guard)
                connection.execute(
                    """
                    INSERT INTO proposal_evidence_guards(
                        proposal_id, guard_id, guard_kind, status, payload_hash, record_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        proposal.proposal_id,
                        guard.guard_id,
                        guard.guard_kind.value,
                        guard.status.value,
                        canonical_hash(json.loads(guard_payload)),
                        guard_payload,
                    ),
                )
            sources = (
                *(
                    ("WEEKLY_REFLECTION", item)
                    for item in proposal.supporting_weekly_reflection_ids
                ),
                *(("WEEKLY_PATTERN", item) for item in proposal.supporting_pattern_ids),
                *(("DAILY_REFLECTION", item) for item in proposal.supporting_daily_reflection_ids),
                *(("FINDING", item) for item in proposal.supporting_finding_ids),
                *(("EXPERIENCE", item) for item in proposal.supporting_experience_ids),
                *(("WEEKLY_GUARD", item) for item in proposal.supporting_weekly_guard_ids),
            )
            connection.executemany(
                """
                INSERT INTO improvement_proposal_sources(
                    proposal_id, source_kind, source_semantic_id
                ) VALUES (?, ?, ?)
                """,
                (
                    (proposal.proposal_id, source_kind, source_id)
                    for source_kind, source_id in sorted(set(sources))
                ),
            )
        return True

    def proposals(self) -> tuple[ImprovementProposal, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM improvement_proposals "
                "ORDER BY proposal_key, proposal_sequence"
            ).fetchall()
        return tuple(ImprovementProposal.model_validate_json(row["record_json"]) for row in rows)

    def proposal(self, proposal_id: str) -> ImprovementProposal | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM improvement_proposals WHERE proposal_id = ?",
                (proposal_id,),
            ).fetchone()
        return None if row is None else ImprovementProposal.model_validate_json(row["record_json"])

    def latest(self, proposal_key: str, policy_id: str) -> ImprovementProposal | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT record_json FROM improvement_proposals
                WHERE proposal_key = ? AND policy_id = ?
                ORDER BY proposal_sequence DESC LIMIT 1
                """,
                (proposal_key, policy_id),
            ).fetchone()
        return None if row is None else ImprovementProposal.model_validate_json(row["record_json"])

    def by_source_id(self, source_id: str, source_kind: str) -> tuple[ImprovementProposal, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT proposals.record_json
                FROM improvement_proposals AS proposals
                JOIN improvement_proposal_sources AS sources
                  ON sources.proposal_id = proposals.proposal_id
                WHERE sources.source_semantic_id = ? AND sources.source_kind = ?
                ORDER BY proposals.proposal_key, proposals.proposal_sequence
                """,
                (source_id, source_kind),
            ).fetchall()
        return tuple(ImprovementProposal.model_validate_json(row["record_json"]) for row in rows)

    def append_transition(self, transition: ProposalStatusTransition) -> bool:
        payload = _payload(transition)
        with self._database.transaction() as connection:
            proposal = connection.execute(
                "SELECT proposal_key, available_at FROM improvement_proposals "
                "WHERE proposal_id = ?",
                (transition.proposal_id,),
            ).fetchone()
            if proposal is None:
                raise ValueError("proposal is not persisted")
            if str(proposal["proposal_key"]) != transition.proposal_key:
                raise ValueError("transition proposal key does not match persisted proposal")
            if transition.effective_at < datetime.fromisoformat(str(proposal["available_at"])):
                raise ValueError("transition cannot predate proposal availability")
            existing = connection.execute(
                "SELECT record_json FROM proposal_status_transitions WHERE transition_id = ?",
                (transition.transition_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("transition ID already exists with different content")
            latest = connection.execute(
                """
                SELECT transition_id, to_status, effective_at
                FROM proposal_status_transitions
                WHERE proposal_id = ? ORDER BY transition_sequence DESC LIMIT 1
                """,
                (transition.proposal_id,),
            ).fetchone()
            current = (
                ProposalStatus.OBSERVATION
                if latest is None
                else ProposalStatus(str(latest["to_status"]))
            )
            previous = None if latest is None else str(latest["transition_id"])
            if transition.from_status is not current:
                raise ValueError("transition from_status does not match current status")
            if transition.previous_transition_id != previous:
                raise ValueError("transition previous transition does not match latest")
            if latest is not None and transition.effective_at < datetime.fromisoformat(
                str(latest["effective_at"])
            ):
                raise ValueError("transition effective_at cannot move backward")
            connection.execute(
                """
                INSERT INTO proposal_status_transitions(
                    transition_id, proposal_id, proposal_key, from_status, to_status,
                    effective_at, previous_transition_id, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transition.transition_id,
                    transition.proposal_id,
                    transition.proposal_key,
                    transition.from_status.value,
                    transition.to_status.value,
                    transition.effective_at.isoformat(),
                    transition.previous_transition_id,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def transition_history(self, proposal_id: str) -> tuple[ProposalStatusTransition, ...]:
        if self.proposal(proposal_id) is None:
            raise ValueError("proposal is not persisted")
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM proposal_status_transitions "
                "WHERE proposal_id = ? ORDER BY transition_sequence",
                (proposal_id,),
            ).fetchall()
        history = tuple(
            ProposalStatusTransition.model_validate_json(row["record_json"]) for row in rows
        )
        current = ProposalStatus.OBSERVATION
        previous: str | None = None
        for transition in history:
            if transition.from_status is not current:
                raise ValueError("stored proposal transition chain has stale status")
            if transition.previous_transition_id != previous:
                raise ValueError("stored proposal transition chain has invalid predecessor")
            current = transition.to_status
            previous = transition.transition_id
        return history

    def current_status(self, proposal_id: str) -> ProposalStatus:
        history = self.transition_history(proposal_id)
        return ProposalStatus.OBSERVATION if not history else history[-1].to_status

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
