"""Append-only SQLite persistence for normalized experience objects."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from axq.database import Database
from axq.experience.contracts import (
    EXPERIENCE_MODELS,
    AttributionStatus,
    Experience,
    ExperienceBase,
    ExperienceType,
)
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _canonical_payload(experience: ExperienceBase) -> str:
    return json.dumps(
        experience.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


class SQLiteExperienceStore:
    """Durable semantic records; sequence numbers never participate in identity."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)

    def append(self, experience: Experience) -> bool:
        payload = _canonical_payload(experience)
        payload_hash = canonical_hash(json.loads(payload))
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM experience_records WHERE experience_id = ?",
                (experience.experience_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("experience ID already exists with different content")
            try:
                connection.execute(
                    """
                    INSERT INTO experience_records(
                        experience_id, experience_type, schema_version,
                        occurred_at, available_at, symbol, setup_id, thesis_id,
                        scenario_id, regime, session, specialist, outcome,
                        attribution_complete, payload_hash, record_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        experience.experience_id,
                        experience.experience_type.value,
                        experience.schema_version,
                        experience.occurred_at.isoformat(),
                        experience.available_at.isoformat(),
                        experience.symbol,
                        experience.setup_id,
                        experience.thesis_id,
                        experience.scenario_id,
                        experience.regime,
                        experience.session,
                        experience.specialist,
                        experience.outcome,
                        int(experience.attribution_status is AttributionStatus.COMPLETE),
                        payload_hash,
                        payload,
                    ),
                )
            except sqlite3.IntegrityError:
                concurrent = connection.execute(
                    "SELECT record_json FROM experience_records WHERE experience_id = ?",
                    (experience.experience_id,),
                ).fetchone()
                if concurrent is not None and str(concurrent["record_json"]) == payload:
                    return False
                raise
            connection.executemany(
                """
                INSERT INTO experience_sources(
                    experience_id, source_kind, source_semantic_id
                ) VALUES (?, ?, ?)
                """,
                (
                    (experience.experience_id, source_kind, source_id)
                    for source_kind, source_id in experience.provenance.source_links()
                ),
            )
        return True

    def append_many(self, experiences: Iterable[Experience]) -> int:
        return sum(self.append(experience) for experience in experiences)

    @staticmethod
    def _decode(record_json: str, experience_type: str) -> Experience:
        model = EXPERIENCE_MODELS[ExperienceType(experience_type)]
        return model.model_validate_json(record_json)  # type: ignore[return-value]

    def experiences(
        self,
        experience_type: ExperienceType | None = None,
    ) -> tuple[Experience, ...]:
        query = "SELECT experience_type, record_json FROM experience_records"
        parameters: tuple[str, ...] = ()
        if experience_type is not None:
            query += " WHERE experience_type = ?"
            parameters = (experience_type.value,)
        query += " ORDER BY occurred_at, experience_id"
        with self._database.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(
            self._decode(str(row["record_json"]), str(row["experience_type"]))
            for row in rows
        )

    def by_source_id(self, source_semantic_id: str) -> tuple[Experience, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT records.experience_type, records.record_json
                FROM experience_records AS records
                JOIN experience_sources AS sources
                  ON sources.experience_id = records.experience_id
                WHERE sources.source_semantic_id = ?
                ORDER BY records.occurred_at, records.experience_id
                """,
                (source_semantic_id,),
            ).fetchall()
        return tuple(
            self._decode(str(row["record_json"]), str(row["experience_type"]))
            for row in rows
        )

    def counts(self) -> dict[ExperienceType, int]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT experience_type, COUNT(*) AS count "
                "FROM experience_records GROUP BY experience_type ORDER BY experience_type"
            ).fetchall()
        return {ExperienceType(str(row["experience_type"])): int(row["count"]) for row in rows}

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
