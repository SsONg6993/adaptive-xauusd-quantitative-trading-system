"""Append-only persistence for operator proposal-transition permission."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from axq.database import Database
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.paired_evaluation_contracts import PairedEvaluationResult
from axq.reflection.paired_evaluation_review_contracts import (
    PairedEvaluationReviewDecision,
)
from axq.reflection.paired_evaluation_review_store import SQLitePairedEvaluationReviewStore
from axq.reflection.paired_evaluation_store import SQLitePairedEvaluationStore
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.proposal_transition_authorization_contracts import (
    ProposalTransitionAuthorization,
)
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


class SQLiteProposalTransitionAuthorizationStore:
    """Persist one strict linear authorization history per proposal."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)
        self._proposals = SQLiteImprovementProposalStore(self.path)
        self._evaluations = SQLiteProposalEvaluationStore(self.path)
        self._paired = SQLitePairedEvaluationStore(self.path)
        self._reviews = SQLitePairedEvaluationReviewStore(self.path)

    def paired_result(self, result_id: str) -> PairedEvaluationResult | None:
        return self._paired.result_by_id(result_id)

    def append(self, authorization: ProposalTransitionAuthorization) -> bool:
        authorization = ProposalTransitionAuthorization.model_validate(authorization.model_dump())
        payload = canonical_record_bytes(authorization).decode("ascii")
        with self._database.transaction() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT record_json FROM proposal_transition_authorizations
                WHERE authorization_id = ?
                """,
                (authorization.authorization_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("authorization ID already exists with different content")
            action = connection.execute(
                """
                SELECT authorization_id FROM proposal_transition_authorizations
                WHERE proposal_id = ? AND action_id = ?
                """,
                (authorization.proposal_id, authorization.action_id),
            ).fetchone()
            if action is not None:
                raise ValueError("authorization action ID already exists with different content")

            proposal = self._proposals.proposal(authorization.proposal_id)
            candidate = self._evaluations.candidate(authorization.candidate_id)
            plan = self._evaluations.plan(authorization.plan_id)
            result = self._paired.result_by_id(authorization.paired_result_id)
            review = self._reviews.review(authorization.accepted_review_id)
            if any(item is None for item in (proposal, candidate, plan, result, review)):
                raise ValueError("authorization authoritative linkage is missing")
            assert proposal is not None
            assert candidate is not None
            assert plan is not None
            assert result is not None
            assert review is not None
            if (
                proposal.proposal_key != authorization.proposal_key
                or candidate.proposal_id != authorization.proposal_id
                or plan.proposal_id != authorization.proposal_id
                or plan.candidate_id != authorization.candidate_id
                or result.proposal_id != authorization.proposal_id
                or result.candidate_id != authorization.candidate_id
                or result.plan_id != authorization.plan_id
                or review.result_id != authorization.paired_result_id
                or review.request_id != result.request_id
                or review.proposal_id != authorization.proposal_id
                or review.candidate_id != authorization.candidate_id
                or review.plan_id != authorization.plan_id
            ):
                raise ValueError("authorization linkage does not match authoritative records")
            if (
                self._proposals.current_status(authorization.proposal_id)
                is not ProposalStatus.CANDIDATE
            ):
                raise ValueError("authorization requires current CANDIDATE proposal status")
            terminal_review = self._reviews.current(authorization.paired_result_id)
            if terminal_review is None or terminal_review.review_id != review.review_id:
                raise ValueError("authorization review is not the current terminal review")
            if review.decision is not PairedEvaluationReviewDecision.ACCEPT_EVIDENCE:
                raise ValueError("authorization requires terminal ACCEPT_EVIDENCE review")
            if authorization.authorized_at < review.effective_at:
                raise ValueError("authorization cannot predate accepted review")

            latest = connection.execute(
                """
                SELECT authorization_id, authorized_at
                FROM proposal_transition_authorizations
                WHERE proposal_id = ? ORDER BY authorization_sequence DESC LIMIT 1
                """,
                (authorization.proposal_id,),
            ).fetchone()
            expected_parent = None if latest is None else str(latest["authorization_id"])
            if authorization.previous_authorization_id != expected_parent:
                raise ValueError(
                    "authorization predecessor is not the current terminal authorization"
                )
            if latest is not None and authorization.authorized_at < datetime.fromisoformat(
                str(latest["authorized_at"])
            ):
                raise ValueError("authorization authorized_at cannot move backward")
            connection.execute(
                """
                INSERT INTO proposal_transition_authorizations(
                    authorization_id, proposal_id, proposal_key, candidate_id, plan_id,
                    paired_result_id, accepted_review_id, from_status, to_status,
                    operator_id, action_id, reason_code, authorized_at,
                    previous_authorization_id, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    authorization.authorization_id,
                    authorization.proposal_id,
                    authorization.proposal_key,
                    authorization.candidate_id,
                    authorization.plan_id,
                    authorization.paired_result_id,
                    authorization.accepted_review_id,
                    authorization.from_status.value,
                    authorization.to_status.value,
                    authorization.operator_id,
                    authorization.action_id,
                    authorization.reason_code,
                    authorization.authorized_at.isoformat(),
                    authorization.previous_authorization_id,
                    authorization.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def authorization(self, authorization_id: str) -> ProposalTransitionAuthorization | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT record_json FROM proposal_transition_authorizations
                WHERE authorization_id = ?
                """,
                (authorization_id,),
            ).fetchone()
        return (
            None
            if row is None
            else ProposalTransitionAuthorization.model_validate_json(row["record_json"])
        )

    def history(self, proposal_id: str) -> tuple[ProposalTransitionAuthorization, ...]:
        if self._proposals.proposal(proposal_id) is None:
            raise ValueError("proposal is not persisted")
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT record_json FROM proposal_transition_authorizations
                WHERE proposal_id = ? ORDER BY authorization_sequence
                """,
                (proposal_id,),
            ).fetchall()
        history = tuple(
            ProposalTransitionAuthorization.model_validate_json(row["record_json"]) for row in rows
        )
        previous: str | None = None
        for authorization in history:
            if authorization.previous_authorization_id != previous:
                raise ValueError("stored authorization chain has invalid predecessor")
            previous = authorization.authorization_id
        return history

    def current(self, proposal_id: str) -> ProposalTransitionAuthorization | None:
        history = self.history(proposal_id)
        return None if not history else history[-1]

    def authorizations(self) -> tuple[ProposalTransitionAuthorization, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT record_json FROM proposal_transition_authorizations
                ORDER BY authorization_sequence
                """
            ).fetchall()
        return tuple(
            ProposalTransitionAuthorization.model_validate_json(row["record_json"]) for row in rows
        )

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
