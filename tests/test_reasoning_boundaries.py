"""Executable isolation and mutation-safety audit for Phase 9 Task 1."""

from __future__ import annotations

import ast
import json
import os
import sqlite3
import subprocess
import sys
from collections.abc import Iterable
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

from axq.reasoning.cli import _parser
from axq.reasoning.contracts import (
    BoundedReasoningContextItem,
    LLMGenerationPolicy,
    LLMReusePolicy,
    ProviderModelIdentity,
    ReasoningSourceKind,
    ReasoningSourceReference,
    ReflectionExplanationInput,
)
from axq.reasoning.ollama import OllamaHTTPTransport
from axq.reasoning.provider import ProviderAttemptControls, ProviderCompletion
from axq.reasoning.service import run_reflection_explanation
from axq.reasoning.store import SQLiteReasoningAuditStore
from axq.reflection.contracts import DailyReflection, ReflectionPolicy
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.weekly_contracts import WeeklyReflection, WeeklyReflectionPolicy
from axq.versioning import canonical_hash
from tests.evaluation_execution_test_support import persist_controlled_plan
from tests.reasoning_test_support import provider_identity, utc
from tests.test_reflection_contracts import END as DAILY_END
from tests.test_reflection_contracts import START as DAILY_START
from tests.test_reflection_contracts import _finding, _guard
from tests.test_weekly_reflection_contracts import END as WEEK_END
from tests.test_weekly_reflection_contracts import START as WEEK_START
from tests.test_weekly_reflection_contracts import _completeness, _pattern

_ROOT = Path(__file__).parents[1]
_REASONING = _ROOT / "src" / "axq" / "reasoning"
_AXQ = _ROOT / "src" / "axq"

_FORBIDDEN_IMPORT_PREFIXES = {
    "MetaTrader5",
    "axq.agents",
    "axq.discipline",
    "axq.execution_boundary",
    "axq.master",
    "axq.mt5",
    "axq.orchestration",
    "axq.position_actions",
    "axq.position_management",
    "axq.quant",
    "axq.replay_validation",
    "axq.risk_boundary",
    "axq.runtime",
    "axq.tools",
    "chromadb",
    "faiss",
    "httpx",
    "importlib",
    "langchain",
    "openai",
    "requests",
    "sentence_transformers",
    "socket",
    "subprocess",
}
_FAST_PATH_PACKAGES = {
    "agents",
    "discipline",
    "execution_boundary",
    "master",
    "mt5",
    "orchestration",
    "position_actions",
    "position_management",
    "replay_validation",
    "risk_boundary",
    "runtime",
    "tools",
}
_FORBIDDEN_IDENTIFIERS = {
    "append_transition",
    "deploy",
    "embedding",
    "embeddings",
    "exec",
    "final_oos",
    "import_module",
    "order_send",
    "plugin",
    "promote",
    "rag",
    "run_system_replay",
    "train_quant_model",
    "vector_store",
}


def _modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return tuple(modules)


def _matches_prefix(value: str, prefixes: Iterable[str]) -> bool:
    return any(value == prefix or value.startswith(f"{prefix}.") for prefix in prefixes)


def _identifiers(tree: ast.AST) -> set[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            values.add(node.id.casefold())
        elif isinstance(node, ast.Attribute):
            values.add(node.attr.casefold())
    return values


def test_reasoning_imports_exclude_runtime_governance_and_research_dependencies() -> None:
    violations: list[str] = []
    for path in sorted(_REASONING.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module in _modules(tree):
            if _matches_prefix(module, _FORBIDDEN_IMPORT_PREFIXES):
                violations.append(f"{path.name}: forbidden import {module}")
            if module.startswith("urllib") and path.name != "ollama.py":
                violations.append(f"{path.name}: network import outside Ollama adapter")
        forbidden_names = _identifiers(tree) & _FORBIDDEN_IDENTIFIERS
        if forbidden_names:
            violations.append(f"{path.name}: forbidden identifiers {sorted(forbidden_names)}")
    assert violations == []


def test_only_ollama_adapter_owns_network_call_and_rejects_non_loopback() -> None:
    network_calls: list[str] = []
    for path in sorted(_REASONING.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if "urlopen" in _identifiers(tree):
            network_calls.append(path.name)
    assert network_calls == ["ollama.py"]

    for endpoint in ("https://example.com", "http://192.168.1.2:11434"):
        try:
            OllamaHTTPTransport(endpoint)
        except ValueError:
            pass
        else:
            raise AssertionError("non-loopback network endpoint was accepted")


def test_fast_path_packages_do_not_import_reasoning() -> None:
    violations: list[str] = []
    for package in sorted(_FAST_PATH_PACKAGES):
        for path in sorted((_AXQ / package).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for module in _modules(tree):
                if module == "axq.reasoning" or module.startswith("axq.reasoning."):
                    violations.append(f"{path.relative_to(_ROOT)} imports {module}")
    assert violations == []


def test_importing_reasoning_does_not_perform_network_io() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src"
    script = (
        "import urllib.request\n"
        "def forbidden(*args, **kwargs): raise RuntimeError('network called during import')\n"
        "urllib.request.urlopen = forbidden\n"
        "import axq.reasoning\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_cli_has_no_forbidden_runtime_research_or_governance_arguments() -> None:
    destinations: set[str] = set()
    pending = [_parser()]
    while pending:
        parser = pending.pop()
        for action in parser._actions:
            destinations.add(action.dest.casefold())
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict):
                pending.extend(choices.values())
    assert not destinations & {
        "broker",
        "credentials",
        "deployment",
        "embedding",
        "final_oos",
        "mt5",
        "plugin",
        "prompt",
        "proposal_transition",
        "rag",
        "replay",
        "runtime_config",
        "tool",
        "training",
        "vector_store",
    }


class _MutationSafetyProvider:
    def __init__(self, raw_content: str) -> None:
        self.raw_content = raw_content

    def verify_identity(
        self,
        expected: ProviderModelIdentity,
        *,
        timeout_seconds: float,
    ) -> ProviderModelIdentity:
        return expected

    def complete(
        self,
        request: object,
        prompt: object,
        *,
        controls: ProviderAttemptControls,
    ) -> ProviderCompletion:
        raw = self.raw_content.encode("utf-8")
        return ProviderCompletion(
            raw_content=self.raw_content,
            raw_response_digest=sha256(raw).hexdigest(),
            raw_response_bytes=len(raw),
        )


def _phase8_table_counts(path: Path) -> dict[str, int]:
    tables = (
        "improvement_proposals",
        "proposal_status_transitions",
        "evaluation_candidate_specs",
        "proposal_evaluation_plans",
        "proposal_evaluation_results",
        "operator_evaluation_decisions",
        "paired_evaluation_results",
        "paired_evaluation_reviews",
        "proposal_transition_authorizations",
    )
    with sqlite3.connect(path) as connection:
        return {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in tables
        }


def test_reasoning_run_leaves_referenced_phase8_records_byte_identical(tmp_path: Path) -> None:
    phase8_path = tmp_path / "phase8.sqlite3"
    proposal, candidate, plan = persist_controlled_plan(phase8_path)
    daily = DailyReflection(
        period_start=DAILY_START,
        period_end=DAILY_END,
        available_at=DAILY_END,
        policy_id=ReflectionPolicy().policy_id,
        input_experience_ids=("exp-1", "exp-2"),
        findings=(_finding(),),
        sample_guards=(_guard(),),
    )
    pattern = _pattern()
    weekly = WeeklyReflection(
        week_start=WEEK_START,
        week_end=WEEK_END,
        available_at=WEEK_END,
        weekly_policy_id=WeeklyReflectionPolicy(daily_policy_id=daily.policy_id).policy_id,
        daily_policy_id=daily.policy_id,
        present_daily_periods=tuple(
            WEEK_START.date() + timedelta(days=index) for index in range(7)
        ),
        missing_daily_periods=(),
        input_daily_reflection_ids=tuple(f"daily-{index}" for index in range(7)),
        input_experience_ids=("experience-1",),
        sample_guards=(_completeness(complete=True),),
        failure_patterns=(pattern,),
    )
    records = (daily, weekly, pattern, proposal, candidate, plan)
    before_bytes = tuple(canonical_record_bytes(item) for item in records)
    before_status = SQLiteImprovementProposalStore(phase8_path).current_status(
        proposal.proposal_id
    )
    before_counts = _phase8_table_counts(phase8_path)
    SQLiteImprovementProposalStore(phase8_path).sync()
    SQLiteProposalEvaluationStore(phase8_path).sync()
    phase8_database_bytes = phase8_path.read_bytes()

    source_records = (daily, weekly, pattern, proposal)
    source_ids = (
        daily.reflection_id,
        weekly.reflection_id,
        pattern.pattern_id,
        proposal.proposal_id,
    )
    source_kinds = (
        ReasoningSourceKind.DAILY_REFLECTION,
        ReasoningSourceKind.WEEKLY_REFLECTION,
        ReasoningSourceKind.PATTERN,
        ReasoningSourceKind.IMPROVEMENT_PROPOSAL,
    )
    references = tuple(
        ReasoningSourceReference(
            source_kind=kind,
            source_id=source_id,
            source_digest=sha256(canonical_record_bytes(record)).hexdigest(),
        )
        for kind, source_id, record in zip(
            source_kinds,
            source_ids,
            source_records,
            strict=True,
        )
    )
    context = tuple(
        BoundedReasoningContextItem(
            context_id=f"context-{index}",
            source=reference,
            context_kind="PHASE8_IMMUTABLE_RECORD",
            content={"source_id": reference.source_id, "summary": "Immutable audit fixture."},
            content_digest=canonical_hash(
                {"source_id": reference.source_id, "summary": "Immutable audit fixture."}
            ),
        )
        for index, reference in enumerate(references)
    )
    output = json.dumps(
        {
            "schema_version": "1.0",
            "explanation": "The immutable Phase 8 evidence supports offline investigation.",
            "cited_evidence_ids": [item.source_id for item in references],
            "hypothesis": "The measured pattern may recur under the same guarded conditions.",
            "uncertainty": {
                "schema_version": "1.0",
                "level": "HIGH",
                "basis": "This controlled fixture is not independent validation.",
            },
            "suggested_next_investigation": "Evaluate another immutable development period.",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    run_reflection_explanation(
        input_record=ReflectionExplanationInput(
            source_references=references,
            context=context,
            generation=LLMGenerationPolicy(),
        ),
        expected_provider_model=provider_identity(),
        provider=_MutationSafetyProvider(output),
        store=SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3"),
        attempt_key="mutation-safety-001",
        reuse_policy=LLMReusePolicy.NEVER_REUSE,
        requested_at=utc("2026-09-12T00:00:00Z"),
        started_at=utc("2026-09-12T00:00:00Z"),
        completed_at=utc("2026-09-12T00:00:00Z"),
        timeout_seconds=30.0,
        endpoint="http://127.0.0.1:11434",
        local_elapsed_ms=0.0,
    )

    assert tuple(canonical_record_bytes(item) for item in records) == before_bytes
    assert phase8_path.read_bytes() == phase8_database_bytes
    assert _phase8_table_counts(phase8_path) == before_counts
    assert SQLiteImprovementProposalStore(phase8_path).current_status(
        proposal.proposal_id
    ) is before_status
