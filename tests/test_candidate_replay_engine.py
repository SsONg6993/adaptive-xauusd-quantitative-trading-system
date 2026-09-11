from __future__ import annotations

import pytest
from candidate_replay_test_support import fixture_ref, persisted_candidate_replay

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayRequest,
    ControlledMetricValue,
)
from axq.reflection.candidate_replay_engine import ControlledReplayFixtureEngine
from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.execution_adapter import canonical_record_bytes


def test_engine_emits_only_exact_preregistered_scope_keys_in_causal_order(tmp_path) -> None:
    proposal, candidate, plan, fixtures, request = persisted_candidate_replay(
        tmp_path / "evaluation.sqlite3",
        include_development=True,
    )
    output = ControlledReplayFixtureEngine().execute(
        request,
        proposal,
        candidate,
        plan,
        fixtures,
    )

    assert [item.scope for item in output.artifacts] == [
        MetricScope.DEVELOPMENT,
        MetricScope.VALIDATION,
    ]
    assert [item.series[0].metric_key for item in output.artifacts] == [
        "development_expectancy",
        "validation_expectancy",
    ]
    assert all(item.series[0].values == (-0.1, 0.3) for item in output.artifacts)
    assert output.artifact_bytes == tuple(
        canonical_record_bytes(item) for item in output.artifacts
    )


def test_engine_rejects_missing_extra_or_wrong_linkage(tmp_path) -> None:
    proposal, candidate, plan, fixtures, request = persisted_candidate_replay(
        tmp_path / "evaluation.sqlite3"
    )
    fixture = fixtures[0]
    missing = fixture.model_copy(
        update={
            "observations": tuple(
                item.model_copy(
                    update={
                        "metric_values": (
                            ControlledMetricValue(metric_key="wrong", value=0.0),
                        )
                    }
                )
                for item in fixture.observations
            )
        }
    )
    extra = fixture.model_copy(
        update={
            "observations": tuple(
                item.model_copy(
                    update={
                        "metric_values": (
                            *item.metric_values,
                            ControlledMetricValue(metric_key="undeclared", value=1.0),
                        )
                    }
                )
                for item in fixture.observations
            )
        }
    )
    engine = ControlledReplayFixtureEngine()
    def matching_request(value):
        return CandidateReplayRequest(
            **request.model_dump(exclude={"request_id", "input_artifact_refs"}),
            input_artifact_refs=(fixture_ref(value),),
        )
    with pytest.raises(ValueError, match="metric keys"):
        engine.execute(matching_request(missing), proposal, candidate, plan, (missing,))
    with pytest.raises(ValueError, match="metric keys"):
        engine.execute(matching_request(extra), proposal, candidate, plan, (extra,))
    with pytest.raises(ValueError, match="linkage"):
        engine.execute(
            request,
            proposal,
            candidate,
            plan,
            (fixture.model_copy(update={"candidate_id": "wrong"}),),
        )


def test_engine_outputs_are_byte_identical_for_equivalent_inputs(tmp_path) -> None:
    proposal, candidate, plan, fixtures, request = persisted_candidate_replay(
        tmp_path / "evaluation.sqlite3"
    )
    engine = ControlledReplayFixtureEngine()
    first = engine.execute(request, proposal, candidate, plan, fixtures)
    second = engine.execute(request, proposal, candidate, plan, tuple(reversed(fixtures)))
    assert second.artifacts == first.artifacts
    assert second.artifact_bytes == first.artifact_bytes
