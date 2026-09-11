"""Immutable composition policy set for the shared Phase 6/7 replay kernel."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from axq.agents import ScenarioPolicy
from axq.discipline import DisciplinePolicy, default_demo_discipline_policy
from axq.execution_boundary import ExecutionPolicy, default_execution_policy
from axq.master import FusionPolicy, default_fusion_policy
from axq.position_actions import PositionActionPolicy, default_position_action_policy
from axq.position_management import (
    PositionManagementPolicy,
    default_demo_position_management_policy,
)
from axq.risk_boundary import RiskPolicy, default_demo_risk_policy
from axq.versioning import canonical_hash


class SharedKernelPolicySet(BaseModel):
    """Complete reviewed policy composition for one shared-kernel replay."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    policy_set_id: str = ""
    fusion_policy: FusionPolicy
    discipline_policy: DisciplinePolicy
    risk_policy: RiskPolicy
    execution_policy: ExecutionPolicy
    position_management_policy: PositionManagementPolicy
    position_action_policy: PositionActionPolicy
    scenario_policy: ScenarioPolicy

    @model_validator(mode="after")
    def bind_identity(self) -> SharedKernelPolicySet:
        identity = self.model_dump(mode="json", exclude={"policy_set_id"})
        expected = f"shared-kernel-policy-set-{canonical_hash(identity)[:20]}"
        if self.policy_set_id and self.policy_set_id != expected:
            raise ValueError("policy_set_id does not match shared-kernel policies")
        object.__setattr__(self, "policy_set_id", expected)
        return self

    def with_master_fusion(self, policy: FusionPolicy) -> SharedKernelPolicySet:
        """Return a new set with only the reviewed Master-fusion policy replaced."""
        return type(self).model_validate(
            self.model_dump(mode="python", exclude={"policy_set_id", "fusion_policy"})
            | {"fusion_policy": policy}
        )


def default_shared_kernel_policy_set() -> SharedKernelPolicySet:
    """Reproduce the exact policy composition used by Phase 7 system replay."""
    return SharedKernelPolicySet(
        fusion_policy=default_fusion_policy(),
        discipline_policy=default_demo_discipline_policy(),
        risk_policy=default_demo_risk_policy(),
        execution_policy=default_execution_policy(),
        position_management_policy=default_demo_position_management_policy(),
        position_action_policy=default_position_action_policy(),
        scenario_policy=ScenarioPolicy(ttl_seconds=900, max_m5_bars=3),
    )
