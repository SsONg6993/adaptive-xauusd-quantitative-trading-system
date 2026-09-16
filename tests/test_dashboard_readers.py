"""Read-only data-boundary tests for the operator dashboard."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from axq.agents import DirectionalBias
from axq.dashboard.contracts import ComponentState
from axq.dashboard.readers import (
    load_performance_snapshot,
    load_reasoning_snapshot,
    load_runtime_performance,
    load_runtime_snapshot,
    read_ollama_status,
)
from axq.dashboard.views import is_agent_room_setup
from axq.interaction import SpecialistInteractionImpact, build_evidence_bound_interaction
from axq.master import default_fusion_policy, fuse_evidence
from axq.mt5.symbols import GoldSymbolConfiguration, resolve_gold_instrument
from axq.orchestration.performance import RuntimePerformanceSnapshot
from axq.reasoning.contracts import (
    LLMAttemptStatus,
    LLMExecutionAttemptAudit,
    LLMStructuredResponseArtifact,
    ReflectionExplanation,
    ReflectionExplanationInput,
    UncertaintyAssessment,
    UncertaintyLevel,
)
from axq.reasoning.service import build_reflection_explanation_request
from axq.reasoning.store import SQLiteReasoningAuditStore
from axq.runtime.journal import SQLiteRuntimeJournal
from axq.runtime.shadow import LiveMarketStatus, ShadowCycleStage, ShadowMarketAvailability
from tests.reasoning_test_support import provider_identity, utc
from tests.test_master_fusion import _bundle, _evidence
from tests.test_shadow_persistence import insert_preserved_interaction_v1_record


def _reasoning_database(path: Path) -> tuple[str, str]:
    input_record = ReflectionExplanationInput.model_validate_json(
        Path("tests/fixtures/reasoning/reflection_explanation_input.json").read_bytes()
    )
    request = build_reflection_explanation_request(
        input_record=input_record,
        provider_model=provider_identity(),
    )
    response = LLMStructuredResponseArtifact.from_request(
        request=request,
        output=ReflectionExplanation(
            explanation="The cited weekly evidence describes repeated London-session losses.",
            cited_evidence_ids=("context-weekly-summary",),
            hypothesis="The weakness is conditional on the London-session context.",
            uncertainty=UncertaintyAssessment(
                level=UncertaintyLevel.MEDIUM,
                basis="The controlled fixture is deliberately small.",
            ),
            suggested_next_investigation="Compare guarded London and non-London samples offline.",
        ),
    )
    attempt = LLMExecutionAttemptAudit(
        request_id=request.request_id,
        attempt_key="dashboard-fixture",
        status=LLMAttemptStatus.COMPLETED,
        provider_model=request.provider_model,
        response_id=response.response_id,
        requested_at=utc("2026-09-12T00:00:00Z"),
        started_at=utc("2026-09-12T00:00:00Z"),
        completed_at=utc("2026-09-12T00:00:01Z"),
        timeout_seconds=30.0,
        endpoint="http://127.0.0.1:11434",
        prompt_token_count=120,
        output_token_count=42,
        provider_total_duration_ns=4_000_000,
        local_elapsed_ms=0.0,
    )
    store = SQLiteReasoningAuditStore(path)
    store.append_request(request)
    store.append_response(response)
    store.append_attempt(attempt)
    return request.request_id, response.response_id


def test_reasoning_reader_is_read_only_and_returns_recent_attempts(tmp_path: Path) -> None:
    path = tmp_path / "reasoning.sqlite3"
    request_id, response_id = _reasoning_database(path)
    before = sha256(path.read_bytes()).hexdigest()

    snapshot = load_reasoning_snapshot(path, limit=5)

    assert snapshot.component.state is ComponentState.AVAILABLE
    assert snapshot.component.detail == "1 reasoning attempt available"
    assert len(snapshot.attempts) == 1
    assert snapshot.attempts[0].attempt.attempt_key == "dashboard-fixture"
    assert snapshot.attempts[0].request.request_id == request_id
    assert snapshot.attempts[0].response is not None
    assert snapshot.attempts[0].response.response_id == response_id
    assert snapshot.attempts[0].request.prompt.template_name == "REFLECTION_EXPLANATION_V2"
    assert sha256(path.read_bytes()).hexdigest() == before


def test_reasoning_reader_rejects_nonpositive_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="limit"):
        load_reasoning_snapshot(tmp_path / "unused.sqlite3", limit=0)


def test_missing_and_unconfigured_sources_are_explicit(tmp_path: Path) -> None:
    assert load_reasoning_snapshot(None).component.state is ComponentState.NOT_CONFIGURED
    assert load_runtime_snapshot(None).component.state is ComponentState.NOT_CONFIGURED
    assert load_performance_snapshot(None).component.state is ComponentState.NOT_CONFIGURED
    assert load_runtime_performance(None).component.state is ComponentState.NOT_CONFIGURED
    missing = tmp_path / "missing.sqlite3"
    assert load_reasoning_snapshot(missing).component.state is ComponentState.UNAVAILABLE
    assert load_runtime_snapshot(missing).component.state is ComponentState.UNAVAILABLE


def test_runtime_performance_reader_is_bounded_and_typed(tmp_path: Path) -> None:
    path = tmp_path / "runtime-performance.json"
    value = RuntimePerformanceSnapshot(
        observed_at=utc("2026-09-16T12:00:00Z"),
        poll_count=10,
        idle_poll_count=9,
        expensive_cycle_count=1,
        latest_poll_latency_ms=0.8,
        latest_cycle_latency_ms=12.3,
        m15_cache_hits=1,
        m15_cache_misses=1,
        cpu_percent=0.4,
        memory_rss_bytes=100_000_000,
    )
    path.write_text(value.model_dump_json(), encoding="utf-8")

    snapshot = load_runtime_performance(path)

    assert snapshot.component.state is ComponentState.AVAILABLE
    assert snapshot.metrics == value


def test_runtime_projection_preserves_canonical_and_resolved_symbol_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    journal = SQLiteRuntimeJournal(path)

    class Gateway:
        def symbol_info(self, symbol: str) -> dict[str, object] | None:
            return {"name": symbol, "point": 0.01}

    resolved = resolve_gold_instrument(
        Gateway(),
        GoldSymbolConfiguration.single("XAUUSD.sc"),
        resolved_at=utc("2026-09-12T00:00:00Z"),
    )
    availability = ShadowMarketAvailability(
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id=resolved.resolution_id,
        observed_at=utc("2026-09-12T00:01:00Z"),
        available_at=utc("2026-09-12T00:01:00Z"),
        broker_tick_at=utc("2026-09-11T23:56:57Z"),
        status=LiveMarketStatus.STALE_QUOTE,
        reason_code="STALE_QUOTE",
    )
    journal.append_semantic(resolved, event_id=None)
    journal.append_semantic(availability, event_id=None)

    snapshot = load_runtime_snapshot(path, now=utc("2026-09-12T00:01:01Z"))

    assert snapshot.instrument_resolution == resolved
    assert snapshot.market_availability == availability
    assert snapshot.instrument_resolution.canonical_instrument.value == "XAUUSD"
    assert snapshot.instrument_resolution.resolved_broker_symbol == "XAUUSD.sc"


def test_runtime_projection_reads_preserved_interaction_v1_without_mutation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    SQLiteRuntimeJournal(path)
    insert_preserved_interaction_v1_record(path)
    before = sha256(path.read_bytes()).hexdigest()

    snapshot = load_runtime_snapshot(path, now=utc("2026-09-14T11:31:00Z"))

    assert snapshot.component.state is ComponentState.ONLINE
    assert snapshot.latest_shadow_cycle is not None
    assert snapshot.latest_shadow_cycle.cycle_id == "scycle-03d3c2acb8ab10687716"
    assert snapshot.latest_shadow_cycle.stage is ShadowCycleStage.QUIET
    assert is_agent_room_setup(snapshot) is False
    assert sha256(path.read_bytes()).hexdigest() == before


def test_performance_reader_reports_known_range_and_metrics(tmp_path: Path) -> None:
    path = tmp_path / "metrics.json"
    path.write_text(
        json.dumps(
            {
                "artifact_id": "replay-abc",
                "input": {
                    "start": "2026-08-10T09:05:00+08:00",
                    "end": "2026-09-09T01:40:00+08:00",
                    "rows": 5966,
                },
                "decisions": {"cycles": 5966, "BUY": 480, "SELL": 492, "HOLD": 4994},
                "trades": {
                    "completed": 166,
                    "realized_pnl": -860.14,
                    "win_rate": 0.4337,
                    "average_r": -0.1249,
                    "expectancy_usd": -5.18,
                    "profit_factor": 0.5404,
                    "max_drawdown": 1032.55,
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    snapshot = load_performance_snapshot(path)

    assert snapshot.component.state is ComponentState.AVAILABLE
    assert snapshot.range_start == "2026-08-10T09:05:00+08:00"
    assert snapshot.range_end == "2026-09-09T01:40:00+08:00"
    assert snapshot.rows == 5966
    assert snapshot.completed_trades == 166
    assert snapshot.realized_pnl == -860.14
    assert snapshot.equity_curve is None


class _FakeOllamaTransport:
    def request(
        self,
        method: str,
        path: str,
        *,
        payload: object,
        timeout_seconds: float,
        response_byte_limit: int,
    ) -> bytes:
        assert method == "GET"
        assert payload is None
        if path == "/api/version":
            return b'{"version":"0.12.6"}'
        if path == "/api/tags":
            return json.dumps(
                {"models": [{"name": "llama3.2:latest", "digest": "a" * 64}]},
                separators=(",", ":"),
            ).encode()
        raise AssertionError(path)


def test_ollama_status_is_online_only_when_loopback_probe_succeeds() -> None:
    status = read_ollama_status(
        "http://127.0.0.1:11434",
        model_name="llama3.2:latest",
        transport=_FakeOllamaTransport(),
    )

    assert status.state is ComponentState.ONLINE
    assert status.metadata["server_version"] == "0.12.6"
    assert status.metadata["model_digest"] == "a" * 64


def test_ollama_status_rejects_non_loopback_endpoint() -> None:
    status = read_ollama_status("http://example.com:11434", model_name=None)
    assert status.state is ComponentState.ERROR
    assert "loopback" in status.detail.casefold()


def test_runtime_reader_exactly_links_latest_master_to_its_evidence_bundle(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH, confidence=0.85),
            "quant": _evidence("quant", DirectionalBias.BULLISH, confidence=0.75),
        }
    )
    proposal = fuse_evidence(bundle, default_fusion_policy())
    journal = SQLiteRuntimeJournal(path)
    journal.append_semantic(bundle, event_id=bundle.event_id)
    journal.append_semantic(proposal, event_id=proposal.event_id)

    snapshot = load_runtime_snapshot(path, now=proposal.as_of)

    assert snapshot.latest_master == proposal
    assert snapshot.latest_evidence_bundle == bundle
    assert snapshot.latest_execution_intent is None


def test_runtime_reader_projects_only_persisted_interaction_turns(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH, confidence=0.9),
            "quant": _evidence("quant", DirectionalBias.BEARISH, confidence=0.9),
        }
    )
    policy = default_fusion_policy()
    proposal = fuse_evidence(bundle, policy)
    interaction = build_evidence_bound_interaction(
        bundle=bundle,
        proposal=proposal,
        policy=policy,
        scan_id="scan-dashboard-interaction",
        available_at=proposal.as_of,
    )
    assert interaction.round is not None and interaction.resolution is not None
    journal = SQLiteRuntimeJournal(path)
    journal.append_semantic(bundle, event_id=bundle.event_id)
    journal.append_semantic(proposal, event_id=proposal.event_id)
    journal.append_semantic(interaction.assessment, event_id=bundle.event_id)
    journal.append_semantic(interaction.round, event_id=bundle.event_id)
    for turn in interaction.turns:
        journal.append_semantic(turn, event_id=bundle.event_id)
    journal.append_semantic(interaction.resolution, event_id=bundle.event_id)
    impact = SpecialistInteractionImpact(
        discussion_id=interaction.round.round_id,
        resolution_id=interaction.resolution.resolution_id,
        event_id=bundle.event_id,
        master_before_id=proposal.proposal_id,
        master_after_id=proposal.proposal_id,
        confidence_before=proposal.confidence,
        confidence_after=proposal.confidence,
        confidence_delta=0.0,
        stance_before=proposal.decision,
        stance_after=proposal.decision,
        stance_changed=False,
        final_reason="Evidence remained unchanged.",
        as_of=proposal.as_of,
        available_at=proposal.as_of,
    )
    journal.append_semantic(impact, event_id=bundle.event_id)

    snapshot = load_runtime_snapshot(path, now=proposal.as_of)

    assert snapshot.latest_interaction_assessment == interaction.assessment
    assert snapshot.latest_interaction_round == interaction.round
    assert snapshot.latest_interaction_turns == interaction.turns
    assert snapshot.latest_interaction_resolution == interaction.resolution
    assert snapshot.latest_interaction_impact == impact
