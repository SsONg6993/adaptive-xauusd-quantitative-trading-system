"""Append-only SQLite provenance store for offline reasoning records."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from sqlite3 import Connection, Row

from pydantic import BaseModel

from axq.database import Database
from axq.reasoning.contracts import (
    LLMAttemptStatus,
    LLMExecutionAttemptAudit,
    LLMRequestEnvelope,
    LLMStructuredResponseArtifact,
    canonical_reasoning_bytes,
)

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"
def _payload(model: BaseModel) -> tuple[str, str]:
    value = canonical_reasoning_bytes(model)
    return value.decode("ascii"), sha256(value).hexdigest()


def _validate_payload[ModelT: BaseModel](row: Row, model_type: type[ModelT]) -> ModelT:
    record_json = str(row["record_json"])
    encoded = record_json.encode("ascii")
    if sha256(encoded).hexdigest() != str(row["payload_hash"]):
        raise ValueError("stored reasoning payload digest does not match canonical bytes")
    model = model_type.model_validate_json(record_json)
    if canonical_reasoning_bytes(model) != encoded:
        raise ValueError("stored reasoning payload is not canonical JSON")
    return model


class SQLiteReasoningAuditStore:
    """Persist immutable requests, structured responses, and execution attempts."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)

    def append_request(self, request: LLMRequestEnvelope) -> bool:
        request = LLMRequestEnvelope.model_validate(request.model_dump())
        payload, digest = _payload(request)
        with self._database.transaction() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM llm_reasoning_requests WHERE request_id = ?",
                (request.request_id,),
            ).fetchone()
            if existing is not None:
                self._request_from_row(existing)
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("request ID already exists with different content")
            connection.execute(
                """
                INSERT INTO llm_reasoning_requests(
                    request_id, task, provider_kind, model_name, model_digest,
                    prompt_template_digest, response_schema_digest, schema_version,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.task.value,
                    request.provider_model.provider.value,
                    request.provider_model.resolved_model_name,
                    request.provider_model.model_digest,
                    request.prompt.template_digest,
                    request.prompt.response_schema_digest,
                    request.schema_version,
                    digest,
                    payload,
                ),
            )
        return True

    def append_response(self, response: LLMStructuredResponseArtifact) -> bool:
        response = LLMStructuredResponseArtifact.model_validate(response.model_dump())
        payload, digest = _payload(response)
        with self._database.transaction() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM llm_reasoning_responses WHERE response_id = ?",
                (response.response_id,),
            ).fetchone()
            if existing is not None:
                persisted = self._response_from_row(existing)
                self._validate_response_link(connection, persisted)
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("response ID already exists with different content")
            request = self._request_in(connection, response.request_id)
            if request is None:
                raise ValueError("response request is not persisted")
            expected = LLMStructuredResponseArtifact.from_request(
                request=request,
                output=response.output,
            )
            if expected != response:
                raise ValueError("response does not match exact request/provider linkage")
            connection.execute(
                """
                INSERT INTO llm_reasoning_responses(
                    response_id, request_id, provider_kind, model_digest,
                    structured_response_digest, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response.response_id,
                    response.request_id,
                    response.provider_model.provider.value,
                    response.provider_model.model_digest,
                    response.structured_response_digest,
                    response.schema_version,
                    digest,
                    payload,
                ),
            )
        return True

    def append_attempt(self, attempt: LLMExecutionAttemptAudit) -> bool:
        attempt = LLMExecutionAttemptAudit.model_validate(attempt.model_dump())
        payload, digest = _payload(attempt)
        with self._database.transaction() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM llm_reasoning_attempts WHERE attempt_id = ?",
                (attempt.attempt_id,),
            ).fetchone()
            if existing is not None:
                persisted = self._attempt_from_row(existing)
                self._validate_attempt_link(connection, persisted)
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("attempt ID already exists with different content")
            keyed = connection.execute(
                """
                SELECT * FROM llm_reasoning_attempts
                WHERE request_id = ? AND attempt_key = ?
                """,
                (attempt.request_id, attempt.attempt_key),
            ).fetchone()
            if keyed is not None:
                persisted = self._attempt_from_row(keyed)
                self._validate_attempt_link(connection, persisted)
                if str(keyed["record_json"]) == payload:
                    return False
                raise ValueError("attempt key already exists with different content")
            request = self._request_in(connection, attempt.request_id)
            if request is None:
                raise ValueError("attempt request is not persisted")
            if request.provider_model != attempt.provider_model:
                raise ValueError("attempt provider does not match exact request linkage")
            response: LLMStructuredResponseArtifact | None = None
            if attempt.response_id is not None:
                response = self._response_in(connection, attempt.response_id)
                if response is None:
                    raise ValueError("attempt response is not persisted")
                if response.request_id != attempt.request_id:
                    raise ValueError("attempt response has invalid request linkage")
                if response.provider_model != attempt.provider_model:
                    raise ValueError("attempt response has invalid provider linkage")
            successful = attempt.status in {
                LLMAttemptStatus.COMPLETED,
                LLMAttemptStatus.REUSED,
            }
            if successful != (response is not None):
                raise ValueError("attempt terminal status has invalid response linkage")
            connection.execute(
                """
                INSERT INTO llm_reasoning_attempts(
                    attempt_id, request_id, attempt_key, status, response_id, failure_code,
                    requested_at, started_at, completed_at, schema_version,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt.attempt_id,
                    attempt.request_id,
                    attempt.attempt_key,
                    attempt.status.value,
                    attempt.response_id,
                    None if attempt.failure is None else attempt.failure.code.value,
                    attempt.requested_at.isoformat(),
                    attempt.started_at.isoformat(),
                    attempt.completed_at.isoformat(),
                    attempt.schema_version,
                    digest,
                    payload,
                ),
            )
        return True

    def request(self, request_id: str) -> LLMRequestEnvelope | None:
        with self._database.connect() as connection:
            return self._request_in(connection, request_id)

    def response(self, response_id: str) -> LLMStructuredResponseArtifact | None:
        with self._database.connect() as connection:
            response = self._response_in(connection, response_id)
            if response is not None:
                self._validate_response_link(connection, response)
            return response

    def attempt(self, attempt_id: str) -> LLMExecutionAttemptAudit | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM llm_reasoning_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                return None
            attempt = self._attempt_from_row(row)
            self._validate_attempt_link(connection, attempt)
            return attempt

    def attempts(self, request_id: str) -> tuple[LLMExecutionAttemptAudit, ...]:
        with self._database.connect() as connection:
            if self._request_in(connection, request_id) is None:
                raise ValueError("request is not persisted")
            rows = connection.execute(
                """
                SELECT * FROM llm_reasoning_attempts
                WHERE request_id = ? ORDER BY attempt_sequence
                """,
                (request_id,),
            ).fetchall()
            attempts = tuple(self._attempt_from_row(row) for row in rows)
            for attempt in attempts:
                self._validate_attempt_link(connection, attempt)
            return attempts

    def first_completed_response(
        self,
        request_id: str,
    ) -> LLMStructuredResponseArtifact | None:
        attempts = self.attempts(request_id)
        first = next(
            (item for item in attempts if item.status is LLMAttemptStatus.COMPLETED),
            None,
        )
        return None if first is None else self.response(str(first.response_id))

    def requests(self) -> tuple[LLMRequestEnvelope, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM llm_reasoning_requests ORDER BY request_sequence"
            ).fetchall()
            return tuple(self._request_from_row(row) for row in rows)

    def responses(self) -> tuple[LLMStructuredResponseArtifact, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM llm_reasoning_responses ORDER BY response_sequence"
            ).fetchall()
            responses = tuple(self._response_from_row(row) for row in rows)
            for response in responses:
                self._validate_response_link(connection, response)
            return responses

    def all_attempts(self) -> tuple[LLMExecutionAttemptAudit, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM llm_reasoning_attempts ORDER BY attempt_sequence"
            ).fetchall()
            attempts = tuple(self._attempt_from_row(row) for row in rows)
            for attempt in attempts:
                self._validate_attempt_link(connection, attempt)
            return attempts

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")

    def _request_in(self, connection: Connection, request_id: str) -> LLMRequestEnvelope | None:
        row = connection.execute(
            "SELECT * FROM llm_reasoning_requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        return None if row is None else self._request_from_row(row)

    def _response_in(
        self,
        connection: Connection,
        response_id: str,
    ) -> LLMStructuredResponseArtifact | None:
        row = connection.execute(
            "SELECT * FROM llm_reasoning_responses WHERE response_id = ?",
            (response_id,),
        ).fetchone()
        return None if row is None else self._response_from_row(row)

    @staticmethod
    def _request_from_row(row: Row) -> LLMRequestEnvelope:
        request = _validate_payload(row, LLMRequestEnvelope)
        indexed = (
            request.request_id,
            request.task.value,
            request.provider_model.provider.value,
            request.provider_model.resolved_model_name,
            request.provider_model.model_digest,
            request.prompt.template_digest,
            request.prompt.response_schema_digest,
            request.schema_version,
        )
        stored = tuple(
            str(row[name])
            for name in (
                "request_id",
                "task",
                "provider_kind",
                "model_name",
                "model_digest",
                "prompt_template_digest",
                "response_schema_digest",
                "schema_version",
            )
        )
        if indexed != stored:
            raise ValueError("stored request indexed columns do not match record")
        return request

    @staticmethod
    def _response_from_row(row: Row) -> LLMStructuredResponseArtifact:
        response = _validate_payload(row, LLMStructuredResponseArtifact)
        indexed = (
            response.response_id,
            response.request_id,
            response.provider_model.provider.value,
            response.provider_model.model_digest,
            response.structured_response_digest,
            response.schema_version,
        )
        stored = tuple(
            str(row[name])
            for name in (
                "response_id",
                "request_id",
                "provider_kind",
                "model_digest",
                "structured_response_digest",
                "schema_version",
            )
        )
        if indexed != stored:
            raise ValueError("stored response indexed columns do not match record")
        return response

    @staticmethod
    def _attempt_from_row(row: Row) -> LLMExecutionAttemptAudit:
        attempt = _validate_payload(row, LLMExecutionAttemptAudit)
        indexed = (
            attempt.attempt_id,
            attempt.request_id,
            attempt.attempt_key,
            attempt.status.value,
            attempt.response_id,
            None if attempt.failure is None else attempt.failure.code.value,
            attempt.requested_at.isoformat(),
            attempt.started_at.isoformat(),
            attempt.completed_at.isoformat(),
            attempt.schema_version,
        )
        stored = tuple(
            row[name]
            for name in (
                "attempt_id",
                "request_id",
                "attempt_key",
                "status",
                "response_id",
                "failure_code",
                "requested_at",
                "started_at",
                "completed_at",
                "schema_version",
            )
        )
        if indexed != stored:
            raise ValueError("stored attempt indexed columns do not match record")
        return attempt

    def _validate_response_link(
        self,
        connection: Connection,
        response: LLMStructuredResponseArtifact,
    ) -> None:
        request = self._request_in(connection, response.request_id)
        if request is None:
            raise ValueError("stored response request linkage is missing")
        expected = LLMStructuredResponseArtifact.from_request(
            request=request,
            output=response.output,
        )
        if expected != response:
            raise ValueError("stored response has invalid exact request linkage")

    def _validate_attempt_link(
        self,
        connection: Connection,
        attempt: LLMExecutionAttemptAudit,
    ) -> None:
        request = self._request_in(connection, attempt.request_id)
        if request is None or request.provider_model != attempt.provider_model:
            raise ValueError("stored attempt has invalid exact request linkage")
        if attempt.response_id is None:
            return
        response = self._response_in(connection, attempt.response_id)
        if response is None:
            raise ValueError("stored attempt response linkage is missing")
        self._validate_response_link(connection, response)
        if response.request_id != attempt.request_id:
            raise ValueError("stored attempt response has invalid request linkage")
