"""Append-only SQLite persistence for daily reflection records."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from axq.database import Database
from axq.reflection.contracts import DailyReflection, ReflectionModel, ReflectionPolicy
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _canonical_payload(record: ReflectionModel) -> str:
    return json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


class SQLiteReflectionStore:
    """Persist policies and immutable daily revisions as semantic records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)

    def append_policy(self, policy: ReflectionPolicy) -> bool:
        payload = _canonical_payload(policy)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM reflection_policies WHERE policy_id = ?",
                (policy.policy_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("reflection policy ID already exists with different content")
            connection.execute(
                """
                INSERT INTO reflection_policies(
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

    def append(self, reflection: DailyReflection) -> bool:
        payload = _canonical_payload(reflection)
        with self._database.transaction() as connection:
            policy = connection.execute(
                "SELECT 1 FROM reflection_policies WHERE policy_id = ?",
                (reflection.policy_id,),
            ).fetchone()
            if policy is None:
                raise ValueError("reflection policy is not persisted")
            existing = connection.execute(
                "SELECT record_json FROM daily_reflections WHERE reflection_id = ?",
                (reflection.reflection_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("reflection ID already exists with different content")
            latest = connection.execute(
                """
                SELECT reflection_id
                FROM daily_reflections
                WHERE period_start = ? AND policy_id = ?
                ORDER BY reflection_sequence DESC
                LIMIT 1
                """,
                (reflection.period_start.isoformat(), reflection.policy_id),
            ).fetchone()
            if latest is None:
                if reflection.supersedes_reflection_id is not None:
                    raise ValueError("first reflection cannot supersede another record")
            elif reflection.supersedes_reflection_id != str(latest["reflection_id"]):
                raise ValueError("revised same-day reflection must supersede latest record")
            connection.execute(
                """
                INSERT INTO daily_reflections(
                    reflection_id, schema_version, policy_id, period_start,
                    period_end, available_at, supersedes_reflection_id,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reflection.reflection_id,
                    reflection.schema_version,
                    reflection.policy_id,
                    reflection.period_start.isoformat(),
                    reflection.period_end.isoformat(),
                    reflection.available_at.isoformat(),
                    reflection.supersedes_reflection_id,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
            connection.executemany(
                """
                INSERT INTO reflection_findings(
                    reflection_id, finding_id, category, signal, reason_code,
                    scope, scope_value, sample_size, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        reflection.reflection_id,
                        finding.finding_id,
                        finding.category.value,
                        finding.signal.value,
                        finding.reason_code,
                        finding.scope,
                        finding.scope_value,
                        finding.sample_size,
                        _canonical_payload(finding),
                    )
                    for finding in reflection.findings
                ),
            )
            connection.executemany(
                """
                INSERT INTO reflection_sample_guards(
                    reflection_id, guard_id, category, status, scope,
                    scope_value, observed_samples, required_samples, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        reflection.reflection_id,
                        guard.guard_id,
                        guard.category.value,
                        guard.status.value,
                        guard.scope,
                        guard.scope_value,
                        guard.observed_samples,
                        guard.required_samples,
                        _canonical_payload(guard),
                    )
                    for guard in reflection.sample_guards
                ),
            )
            connection.executemany(
                "INSERT INTO reflection_sources(reflection_id, experience_id) VALUES (?, ?)",
                (
                    (reflection.reflection_id, experience_id)
                    for experience_id in reflection.input_experience_ids
                ),
            )
        return True

    def policy(self, policy_id: str) -> ReflectionPolicy | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM reflection_policies WHERE policy_id = ?",
                (policy_id,),
            ).fetchone()
        return None if row is None else ReflectionPolicy.model_validate_json(row["record_json"])

    def latest(self, period_start: datetime, policy_id: str) -> DailyReflection | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT record_json FROM daily_reflections
                WHERE period_start = ? AND policy_id = ?
                ORDER BY reflection_sequence DESC LIMIT 1
                """,
                (period_start.isoformat(), policy_id),
            ).fetchone()
        return None if row is None else DailyReflection.model_validate_json(row["record_json"])

    def reflections(self) -> tuple[DailyReflection, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM daily_reflections "
                "ORDER BY period_start, reflection_sequence"
            ).fetchall()
        return tuple(DailyReflection.model_validate_json(row["record_json"]) for row in rows)

    def by_experience_id(self, experience_id: str) -> tuple[DailyReflection, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT reflections.record_json
                FROM daily_reflections AS reflections
                JOIN reflection_sources AS sources
                  ON sources.reflection_id = reflections.reflection_id
                WHERE sources.experience_id = ?
                ORDER BY reflections.period_start, reflections.reflection_sequence
                """,
                (experience_id,),
            ).fetchall()
        return tuple(DailyReflection.model_validate_json(row["record_json"]) for row in rows)

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
