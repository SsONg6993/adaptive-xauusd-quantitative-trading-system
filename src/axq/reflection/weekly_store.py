"""Append-only persistence and fail-closed replay for weekly knowledge."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from axq.database import Database
from axq.reflection.contracts import ReflectionModel
from axq.reflection.weekly_contracts import (
    FailurePattern,
    KnowledgeStatus,
    Pattern,
    PatternStatusTransition,
    PatternType,
    SuccessPattern,
    WeeklyReflection,
    WeeklyReflectionPolicy,
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


def _pattern_from_json(payload: str) -> Pattern:
    data = json.loads(payload)
    model = SuccessPattern if data["pattern_type"] == PatternType.SUCCESS.value else FailurePattern
    return model.model_validate(data)


class SQLiteWeeklyReflectionStore:
    """Store immutable weekly observations and explicit lifecycle actions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)

    def append_policy(self, policy: WeeklyReflectionPolicy) -> bool:
        payload = _payload(policy)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM weekly_reflection_policies WHERE policy_id = ?",
                (policy.policy_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("weekly policy ID already exists with different content")
            connection.execute(
                """
                INSERT INTO weekly_reflection_policies(
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

    @staticmethod
    def _append_semantic(
        connection: object,
        table: str,
        id_column: str,
        semantic_id: str,
        record: ReflectionModel,
        insert_sql: str,
        values: tuple[object, ...],
    ) -> None:
        payload = _payload(record)
        row = connection.execute(  # type: ignore[attr-defined]
            f"SELECT record_json FROM {table} WHERE {id_column} = ?", (semantic_id,)
        ).fetchone()
        if row is not None:
            if str(row["record_json"]) != payload:
                raise ValueError(f"{id_column} already exists with different content")
            return
        connection.execute(insert_sql, (*values, canonical_hash(json.loads(payload)), payload))  # type: ignore[attr-defined]

    def append(self, reflection: WeeklyReflection) -> bool:
        payload = _payload(reflection)
        with self._database.transaction() as connection:
            policy = connection.execute(
                "SELECT 1 FROM weekly_reflection_policies WHERE policy_id = ?",
                (reflection.weekly_policy_id,),
            ).fetchone()
            if policy is None:
                raise ValueError("weekly reflection policy is not persisted")
            existing = connection.execute(
                "SELECT record_json FROM weekly_reflections WHERE reflection_id = ?",
                (reflection.reflection_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("weekly reflection ID already exists with different content")
            latest = connection.execute(
                """
                SELECT reflection_id FROM weekly_reflections
                WHERE week_start = ? AND weekly_policy_id = ?
                ORDER BY reflection_sequence DESC LIMIT 1
                """,
                (reflection.week_start.isoformat(), reflection.weekly_policy_id),
            ).fetchone()
            if latest is None:
                if reflection.supersedes_weekly_reflection_id is not None:
                    raise ValueError("first weekly reflection cannot supersede another record")
            elif reflection.supersedes_weekly_reflection_id != str(latest["reflection_id"]):
                raise ValueError("revised weekly reflection must supersede latest record")
            connection.execute(
                """
                INSERT INTO weekly_reflections(
                    reflection_id, schema_version, weekly_policy_id, daily_policy_id,
                    week_start, week_end, available_at, complete,
                    supersedes_reflection_id, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reflection.reflection_id,
                    reflection.schema_version,
                    reflection.weekly_policy_id,
                    reflection.daily_policy_id,
                    reflection.week_start.isoformat(),
                    reflection.week_end.isoformat(),
                    reflection.available_at.isoformat(),
                    int(not reflection.missing_daily_periods),
                    reflection.supersedes_weekly_reflection_id,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
            for pattern in (*reflection.success_patterns, *reflection.failure_patterns):
                self._append_semantic(
                    connection,
                    "weekly_patterns",
                    "pattern_id",
                    pattern.pattern_id,
                    pattern,
                    """
                    INSERT INTO weekly_patterns(
                        pattern_id, pattern_key, pattern_type, knowledge_status,
                        week_start, payload_hash, record_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pattern.pattern_id,
                        pattern.pattern_key,
                        pattern.pattern_type.value,
                        pattern.knowledge_status.value,
                        pattern.week_start.isoformat(),
                    ),
                )
                connection.execute(
                    "INSERT INTO weekly_reflection_patterns"
                    "(reflection_id, pattern_id) VALUES (?, ?)",
                    (reflection.reflection_id, pattern.pattern_id),
                )
            for guard in reflection.sample_guards:
                self._append_semantic(
                    connection,
                    "weekly_sample_guards",
                    "guard_id",
                    guard.guard_id,
                    guard,
                    """
                    INSERT INTO weekly_sample_guards(
                        guard_id, guard_kind, status, payload_hash, record_json
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (guard.guard_id, guard.guard_kind.value, guard.status.value),
                )
                connection.execute(
                    "INSERT INTO weekly_reflection_guards(reflection_id, guard_id) VALUES (?, ?)",
                    (reflection.reflection_id, guard.guard_id),
                )
            sources = (
                *(("DAILY_REFLECTION", item) for item in reflection.input_daily_reflection_ids),
                *(("EXPERIENCE", item) for item in reflection.input_experience_ids),
                *(
                    ("FINDING", finding_id)
                    for pattern in (*reflection.success_patterns, *reflection.failure_patterns)
                    for finding_id in pattern.supporting_finding_ids
                ),
            )
            connection.executemany(
                """
                INSERT INTO weekly_reflection_sources(
                    reflection_id, source_kind, source_semantic_id
                ) VALUES (?, ?, ?)
                """,
                (
                    (reflection.reflection_id, source_kind, source_id)
                    for source_kind, source_id in sorted(set(sources))
                ),
            )
        return True

    def reflections(self) -> tuple[WeeklyReflection, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM weekly_reflections "
                "ORDER BY week_start, reflection_sequence"
            ).fetchall()
        return tuple(WeeklyReflection.model_validate_json(row["record_json"]) for row in rows)

    def latest(self, week_start: datetime, policy_id: str) -> WeeklyReflection | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT record_json FROM weekly_reflections
                WHERE week_start = ? AND weekly_policy_id = ?
                ORDER BY reflection_sequence DESC LIMIT 1
                """,
                (week_start.isoformat(), policy_id),
            ).fetchone()
        return None if row is None else WeeklyReflection.model_validate_json(row["record_json"])

    def by_experience_id(self, experience_id: str) -> tuple[WeeklyReflection, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT reflections.record_json
                FROM weekly_reflections AS reflections
                JOIN weekly_reflection_sources AS sources
                  ON sources.reflection_id = reflections.reflection_id
                WHERE sources.source_kind = 'EXPERIENCE'
                  AND sources.source_semantic_id = ?
                ORDER BY reflections.week_start, reflections.reflection_sequence
                """,
                (experience_id,),
            ).fetchall()
        return tuple(WeeklyReflection.model_validate_json(row["record_json"]) for row in rows)

    def pattern(self, pattern_id: str) -> Pattern | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM weekly_patterns WHERE pattern_id = ?",
                (pattern_id,),
            ).fetchone()
        return None if row is None else _pattern_from_json(str(row["record_json"]))

    def append_transition(self, transition: PatternStatusTransition) -> bool:
        payload = _payload(transition)
        with self._database.transaction() as connection:
            pattern_row = connection.execute(
                "SELECT pattern_key FROM weekly_patterns WHERE pattern_id = ?",
                (transition.pattern_id,),
            ).fetchone()
            if pattern_row is None:
                raise ValueError("pattern is not persisted")
            if str(pattern_row["pattern_key"]) != transition.pattern_key:
                raise ValueError("transition pattern key does not match persisted pattern")
            existing = connection.execute(
                "SELECT record_json FROM pattern_status_transitions WHERE transition_id = ?",
                (transition.transition_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("transition ID already exists with different content")
            latest = connection.execute(
                """
                SELECT transition_id, to_status, effective_at
                FROM pattern_status_transitions
                WHERE pattern_id = ? ORDER BY transition_sequence DESC LIMIT 1
                """,
                (transition.pattern_id,),
            ).fetchone()
            current = (
                KnowledgeStatus.OBSERVATION
                if latest is None
                else KnowledgeStatus(str(latest["to_status"]))
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
                INSERT INTO pattern_status_transitions(
                    transition_id, pattern_id, pattern_key, from_status, to_status,
                    effective_at, previous_transition_id, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transition.transition_id,
                    transition.pattern_id,
                    transition.pattern_key,
                    transition.from_status.value,
                    transition.to_status.value,
                    transition.effective_at.isoformat(),
                    transition.previous_transition_id,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def transition_history(self, pattern_id: str) -> tuple[PatternStatusTransition, ...]:
        if self.pattern(pattern_id) is None:
            raise ValueError("pattern is not persisted")
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM pattern_status_transitions "
                "WHERE pattern_id = ? ORDER BY transition_sequence",
                (pattern_id,),
            ).fetchall()
        transitions = tuple(
            PatternStatusTransition.model_validate_json(row["record_json"]) for row in rows
        )
        current = KnowledgeStatus.OBSERVATION
        previous: str | None = None
        for transition in transitions:
            if transition.from_status is not current:
                raise ValueError("stored transition chain has stale current status")
            if transition.previous_transition_id != previous:
                raise ValueError("stored transition chain has invalid predecessor")
            current = transition.to_status
            previous = transition.transition_id
        return transitions

    def current_status(self, pattern_id: str) -> KnowledgeStatus:
        history = self.transition_history(pattern_id)
        return KnowledgeStatus.OBSERVATION if not history else history[-1].to_status

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
