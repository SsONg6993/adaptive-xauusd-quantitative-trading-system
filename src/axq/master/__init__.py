"""Deterministic Master evidence-fusion boundary."""

from axq.master.contracts import (
    EvidenceDisposition,
    FusionPolicy,
    FusionReason,
    MasterProposal,
    SpecialistContribution,
    SpecialistWeight,
)
from axq.master.fusion import default_fusion_policy, fuse_evidence

__all__ = [
    "EvidenceDisposition",
    "FusionPolicy",
    "FusionReason",
    "MasterProposal",
    "SpecialistContribution",
    "SpecialistWeight",
    "default_fusion_policy",
    "fuse_evidence",
]
