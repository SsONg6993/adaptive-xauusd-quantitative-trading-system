"""Advisory Champion/Challenger evidence contract."""

from __future__ import annotations

from typing import Any


def evaluate_challenger_evidence(
    evidence: dict[str, Any], *, minimum_sample_size: int, minimum_folds: int
) -> dict[str, Any]:
    requirements = {
        "minimum_sample_size": int(evidence.get("sample_size", 0)) >= minimum_sample_size,
        "multiple_walk_forward_folds": int(evidence.get("walk_forward_folds", 0))
        >= minimum_folds,
        "beats_simple_baseline": evidence.get("beats_simple_baseline") is True,
        "acceptable_calibration": evidence.get("calibration_acceptable") is True,
        "temporal_stability": evidence.get("temporally_stable") is True,
        "no_frequency_collapse": evidence.get("frequency_collapse") is False,
        "reproducible": evidence.get("reproducible") is True,
    }
    unmet = [name for name, passed in requirements.items() if not passed]
    return {
        "requirements": requirements,
        "unmet_requirements": unmet,
        "eligible_for_review": not unmet,
        "automatic_promotion": False,
        "registry_transition_performed": False,
    }
