"""Append-only persistence for governed paired-evaluation reviews."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from axq.database import Database
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.paired_evaluation_contracts import PairedEvaluationResult
from axq.reflection.paired_evaluation_review_contracts import PairedEvaluationReview
from axq.reflection.paired_evaluation_store import SQLitePairedEvaluationStore
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


class SQLitePairedEvaluationReviewStore:
    """Persist and replay one strict linear review chain per paired result."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)
        self._paired = SQLitePairedEvaluationStore(self.path)
        self._evaluations = SQLiteProposalEvaluationStore(self.path)

    def paired_result(self, result_id: str) -> PairedEvaluationResult | None:
        return self._paired.result_by_id(result_id)

    def append(self, review: PairedEvaluationReview) -> bool:
        review = PairedEvaluationReview.model_validate(review.model_dump())
        payload = canonical_record_bytes(review).decode("ascii")
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM paired_evaluation_reviews WHERE review_id = ?",
                (review.review_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("review ID already exists with different content")
            action = connection.execute(
                """
                SELECT review_id FROM paired_evaluation_reviews
                WHERE result_id = ? AND action_id = ?
                """,
                (review.result_id, review.action_id),
            ).fetchone()
            if action is not None:
                raise ValueError("review action ID already exists with different content")

            result = self._paired.result_by_id(review.result_id)
            request = self._paired.request(review.request_id)
            if result is None or request is None:
                raise ValueError("paired review authoritative linkage is missing")
            if (
                result.request_id != review.request_id
                or result.proposal_id != review.proposal_id
                or result.candidate_id != review.candidate_id
                or result.plan_id != review.plan_id
                or request.proposal_id != review.proposal_id
                or request.candidate_id != review.candidate_id
                or request.plan_id != review.plan_id
            ):
                raise ValueError("paired review linkage does not match immutable result")
            if review.effective_at < result.available_at:
                raise ValueError("paired review cannot predate result availability")
            self._validate_support(review)

            latest = connection.execute(
                """
                SELECT review_id, effective_at FROM paired_evaluation_reviews
                WHERE result_id = ? ORDER BY review_sequence DESC LIMIT 1
                """,
                (review.result_id,),
            ).fetchone()
            expected_parent = None if latest is None else str(latest["review_id"])
            if review.previous_review_id != expected_parent:
                raise ValueError("review predecessor is not the current terminal review")
            if latest is not None and review.effective_at < datetime.fromisoformat(
                str(latest["effective_at"])
            ):
                raise ValueError("review effective_at cannot move backward")
            connection.execute(
                """
                INSERT INTO paired_evaluation_reviews(
                    review_id, result_id, request_id, proposal_id, candidate_id, plan_id,
                    decision, operator_id, action_id, reason_code, effective_at,
                    previous_review_id, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review.review_id,
                    review.result_id,
                    review.request_id,
                    review.proposal_id,
                    review.candidate_id,
                    review.plan_id,
                    review.decision.value,
                    review.operator_id,
                    review.action_id,
                    review.reason_code,
                    review.effective_at.isoformat(),
                    review.previous_review_id,
                    review.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def _validate_support(self, review: PairedEvaluationReview) -> None:
        for result_id in review.supporting_evaluation_result_ids:
            evaluation_result = self._evaluations.result(result_id)
            if evaluation_result is None:
                raise ValueError("supporting evaluation result is not persisted")
            if (
                evaluation_result.proposal_id != review.proposal_id
                or evaluation_result.candidate_id != review.candidate_id
                or evaluation_result.plan_id != review.plan_id
            ):
                raise ValueError("supporting evaluation result linkage mismatch")
        for result_id in review.supporting_paired_result_ids:
            paired_result = self._paired.result_by_id(result_id)
            if paired_result is None:
                raise ValueError("supporting paired result is not persisted")
            if (
                paired_result.proposal_id != review.proposal_id
                or paired_result.candidate_id != review.candidate_id
                or paired_result.plan_id != review.plan_id
            ):
                raise ValueError("supporting paired result linkage mismatch")

    def review(self, review_id: str) -> PairedEvaluationReview | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM paired_evaluation_reviews WHERE review_id = ?",
                (review_id,),
            ).fetchone()
        return (
            None if row is None else PairedEvaluationReview.model_validate_json(row["record_json"])
        )

    def history(self, result_id: str) -> tuple[PairedEvaluationReview, ...]:
        if self._paired.result_by_id(result_id) is None:
            raise ValueError("paired evaluation result is not persisted")
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT record_json FROM paired_evaluation_reviews
                WHERE result_id = ? ORDER BY review_sequence
                """,
                (result_id,),
            ).fetchall()
        history = tuple(
            PairedEvaluationReview.model_validate_json(row["record_json"]) for row in rows
        )
        previous: str | None = None
        for review in history:
            if review.previous_review_id != previous:
                raise ValueError("stored paired review chain has invalid predecessor")
            previous = review.review_id
        return history

    def current(self, result_id: str) -> PairedEvaluationReview | None:
        history = self.history(result_id)
        return None if not history else history[-1]

    def reviews(self) -> tuple[PairedEvaluationReview, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM paired_evaluation_reviews ORDER BY review_sequence"
            ).fetchall()
        return tuple(PairedEvaluationReview.model_validate_json(row["record_json"]) for row in rows)

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
