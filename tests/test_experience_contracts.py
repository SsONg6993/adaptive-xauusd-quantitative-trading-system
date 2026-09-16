from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from axq.experience import (
    AttributionStatus,
    CounterfactualExperience,
    DecisionExperience,
    ExperienceProvenance,
    TradeExperience,
)
from axq.schemas import Signal

T0 = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _provenance() -> ExperienceProvenance:
    return ExperienceProvenance(
        runtime_event_ids=("ev-2", "ev-1", "ev-1"),
        evidence_bundle_ids=("bundle-1",),
        master_proposal_ids=("mp-1",),
    )


def _decision(**updates: object) -> DecisionExperience:
    values: dict[str, object] = {
        "occurred_at": T0,
        "available_at": T0,
        "symbol": "XAUUSD",
        "outcome": "HOLD",
        "provenance": _provenance(),
        "master_proposal_id": "mp-1",
        "evidence_bundle_id": "bundle-1",
        "decision": Signal.HOLD,
        "actionable": False,
        "master_confidence": 0.0,
        "disagreement": 0.0,
        "contradiction": 0.0,
    }
    values.update(updates)
    return DecisionExperience.model_validate(values)


def _trade(**updates: object) -> TradeExperience:
    values: dict[str, object] = {
        "occurred_at": T0,
        "available_at": T0,
        "symbol": "XAUUSD",
        "setup_id": "setup-1",
        "thesis_id": "thesis-1",
        "scenario_id": "scenario-1",
        "session": "LONDON",
        "outcome": "PROTECTIVE_STOP",
        "provenance": ExperienceProvenance(
            execution_intent_ids=("xi-1",),
            execution_result_ids=("xr-1",),
            replay_fill_ids=("rfill-1",),
            replay_trade_ids=("rtrade-1",),
        ),
        "replay_trade_id": "rtrade-1",
        "execution_intent_id": "xi-1",
        "execution_result_id": "xr-1",
        "replay_fill_id": "rfill-1",
        "position_id": "rpos-1",
        "direction": Signal.BUY,
        "entry_time": T0,
        "exit_time": T0,
        "entry_price": 2500.0,
        "exit_price": 2499.0,
        "volume_lots": 0.1,
        "realized_pnl": 0.0,
        "r_outcome": None,
        "mfe_points": 0.0,
        "mae_points": 100.0,
        "holding_seconds": 0.0,
        "exit_cause": "PROTECTIVE_STOP",
        "stop_triggered": True,
        "explicit_position_exit": False,
    }
    values.update(updates)
    return TradeExperience.model_validate(values)


def test_equivalent_decision_content_has_deterministic_identity() -> None:
    first = _decision()
    second = _decision()

    assert first.experience_id == second.experience_id
    assert first.experience_id.startswith("exp-decision-")
    assert first.provenance.runtime_event_ids == ("ev-1", "ev-2")
    assert DecisionExperience.model_validate_json(first.model_dump_json()) == first


def test_experience_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="UTC|timezone"):
        _decision(occurred_at=datetime(2026, 8, 10, 10, 0))


def test_trade_preserves_none_separately_from_numeric_zero() -> None:
    trade = _trade()
    payload = trade.model_dump(mode="json")

    assert payload["realized_pnl"] == 0.0
    assert payload["mfe_points"] == 0.0
    assert payload["r_outcome"] is None


def test_actual_trade_cannot_be_marked_simulated() -> None:
    with pytest.raises(ValidationError):
        _trade(simulated=True)


def test_counterfactual_is_separate_and_requires_explicit_assumptions() -> None:
    counterfactual = CounterfactualExperience(
        occurred_at=T0,
        available_at=T0,
        symbol="XAUUSD",
        outcome="SIMULATED_WIN",
        provenance=ExperienceProvenance(master_proposal_ids=("mp-1",)),
        source_proposal_id="mp-1",
        counterfactual_method="NEXT_M5_OPEN",
        counterfactual_method_version="1.0.0",
        assumptions=("fixed spread", "unchanged stop"),
        confidence=0.5,
        simulated_outcome=125.0,
        attribution_status=AttributionStatus.COMPLETE,
    )

    assert counterfactual.simulated is True
    assert counterfactual.experience_id.startswith("exp-counterfactual-")
    with pytest.raises(ValidationError):
        CounterfactualExperience.model_validate(
            counterfactual.model_dump(mode="python") | {"assumptions": ()}
        )
