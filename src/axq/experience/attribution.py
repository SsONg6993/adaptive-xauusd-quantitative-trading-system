"""Exact-link deterministic reconstruction of normalized Phase 8 experiences."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from axq.agents import AgentEvidence, AgentStatus
from axq.discipline import DisciplineOutcome, DisciplineResult
from axq.execution_boundary import (
    ExecutionIntent,
    ExecutionResult,
    ExecutionResultStatus,
    ReconciliationKind,
    ReconciliationReport,
    ResumeReadiness,
    ResumeStatus,
)
from axq.execution_boundary.recovery_contracts import ExecutionTransition
from axq.experience.contracts import (
    AgentContributionExperience,
    AttributionStatus,
    DecisionExperience,
    Experience,
    ExperienceProvenance,
    ExperienceType,
    PositionManagementExperience,
    RejectedDecisionExperience,
    RejectionLayer,
    RuntimeAnomalyExperience,
    SpecialistDecisionFact,
    TradeExperience,
)
from axq.master import MasterProposal
from axq.position_actions import (
    PositionActionIntent,
    PositionActionSafetyOutcome,
    PositionActionSafetyResult,
)
from axq.position_actions.transport import (
    PositionActionTransportResult,
    PositionActionTransportTransition,
)
from axq.position_management import PositionManagementOutcome
from axq.replay_validation.outcomes import ReplayOutcomeArtifact
from axq.risk_boundary import RiskOutcome, RiskResult
from axq.runtime import RuntimeEvent
from axq.runtime.journal import JournalRecord
from axq.schemas import Signal
from axq.versioning import canonical_hash


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, StrEnum) else str(value)


def _reason_values(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(_enum_value(value) for value in values)


def _index[T](values: Iterable[T], field_name: str) -> dict[str, T]:
    result: dict[str, T] = {}
    for value in values:
        semantic_id = str(getattr(value, field_name))
        previous = result.get(semantic_id)
        if previous is not None and previous != value:
            raise ValueError(f"conflicting source semantic ID: {semantic_id}")
        result[semantic_id] = value
    return result


def _status(missing: list[str]) -> tuple[AttributionStatus, tuple[str, ...]]:
    normalized = tuple(sorted(set(missing)))
    return (
        AttributionStatus.INCOMPLETE if normalized else AttributionStatus.COMPLETE,
        normalized,
    )


@dataclass(frozen=True)
class AttributionSources:
    runtime_events: tuple[RuntimeEvent, ...] = ()
    masters: tuple[MasterProposal, ...] = ()
    disciplines: tuple[DisciplineOutcome, ...] = ()
    risks: tuple[RiskOutcome, ...] = ()
    execution_intents: tuple[ExecutionIntent, ...] = ()
    execution_results: tuple[ExecutionResult, ...] = ()
    agent_evidence: tuple[AgentEvidence, ...] = ()
    position_management: tuple[PositionManagementOutcome, ...] = ()
    position_action_safety: tuple[PositionActionSafetyOutcome, ...] = ()
    position_action_intents: tuple[PositionActionIntent, ...] = ()
    position_action_results: tuple[PositionActionTransportResult, ...] = ()
    reconciliations: tuple[ReconciliationReport, ...] = ()
    readiness: tuple[ResumeReadiness, ...] = ()
    replay_outcomes: ReplayOutcomeArtifact | None = None

    @classmethod
    def from_paths(
        cls,
        *,
        runtime_journal_path: str | Path,
        execution_ledger_path: str | Path,
        position_action_ledger_path: str | Path,
        replay_outcomes_path: str | Path,
    ) -> AttributionSources:
        decoded: list[BaseModel] = []
        with _read_only(runtime_journal_path) as connection:
            rows = connection.execute(
                "SELECT record_json FROM runtime_journal ORDER BY journal_sequence"
            ).fetchall()
        for row in rows:
            decoded.append(JournalRecord.model_validate_json(row[0]).decode())

        with _read_only(execution_ledger_path) as connection:
            execution_rows = connection.execute(
                "SELECT transition_json FROM execution_transitions "
                "ORDER BY transition_sequence"
            ).fetchall()
        execution_transitions = tuple(
            ExecutionTransition.model_validate_json(row[0]) for row in execution_rows
        )

        with _read_only(position_action_ledger_path) as connection:
            action_rows = connection.execute(
                "SELECT transition_json FROM position_action_transport_transitions "
                "ORDER BY transition_sequence"
            ).fetchall()
        action_transitions = tuple(
            PositionActionTransportTransition.model_validate_json(row[0])
            for row in action_rows
        )

        runtime_intents = tuple(value for value in decoded if isinstance(value, ExecutionIntent))
        ledger_intents = tuple(
            value.intent for value in execution_transitions if value.intent is not None
        )
        runtime_results = tuple(value for value in decoded if isinstance(value, ExecutionResult))
        ledger_results = tuple(
            value.result for value in execution_transitions if value.result is not None
        )
        return cls(
            runtime_events=tuple(value for value in decoded if isinstance(value, RuntimeEvent)),
            masters=tuple(value for value in decoded if isinstance(value, MasterProposal)),
            disciplines=tuple(value for value in decoded if isinstance(value, DisciplineOutcome)),
            risks=tuple(value for value in decoded if isinstance(value, RiskOutcome)),
            execution_intents=_deduplicate(
                (*runtime_intents, *ledger_intents),
                "intent_id",
            ),
            execution_results=_deduplicate(
                (*runtime_results, *ledger_results),
                "result_id",
            ),
            agent_evidence=tuple(value for value in decoded if isinstance(value, AgentEvidence)),
            position_management=tuple(
                value for value in decoded if isinstance(value, PositionManagementOutcome)
            ),
            position_action_safety=tuple(
                value for value in decoded if isinstance(value, PositionActionSafetyOutcome)
            ),
            position_action_intents=tuple(
                value for value in decoded if isinstance(value, PositionActionIntent)
            ),
            position_action_results=_deduplicate(
                tuple(
                    value.result for value in action_transitions if value.result is not None
                ),
                "result_id",
            ),
            reconciliations=tuple(
                value for value in decoded if isinstance(value, ReconciliationReport)
            ),
            readiness=tuple(value for value in decoded if isinstance(value, ResumeReadiness)),
            replay_outcomes=ReplayOutcomeArtifact.read(replay_outcomes_path),
        )


def _read_only(path: str | Path) -> sqlite3.Connection:
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    connection = sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _deduplicate[T](values: Iterable[T], field_name: str) -> tuple[T, ...]:
    indexed = _index(values, field_name)
    return tuple(indexed[key] for key in sorted(indexed))


class ExperienceBuild(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1.0"
    build_id: str = ""
    experiences: tuple[Experience, ...]

    @model_validator(mode="after")
    def bind_identity(self) -> ExperienceBuild:
        ordered = tuple(
            sorted(
                self.experiences,
                key=lambda item: (
                    item.occurred_at,
                    item.experience_type.value,
                    item.experience_id,
                ),
            )
        )
        object.__setattr__(self, "experiences", ordered)
        expected = f"experience-build-{canonical_hash([x.experience_id for x in ordered])[:20]}"
        if self.build_id and self.build_id != expected:
            raise ValueError("build_id does not match experience IDs")
        object.__setattr__(self, "build_id", expected)
        return self

    def of_type(self, experience_type: ExperienceType) -> tuple[Experience, ...]:
        return tuple(
            item for item in self.experiences if item.experience_type is experience_type
        )


class OutcomeAttributionBuilder:
    """Build experiences with exact semantic joins and explicit missing-link markers."""

    def build(self, sources: AttributionSources) -> ExperienceBuild:
        indexes = _SourceIndexes(sources)
        experiences: list[Experience] = []
        experiences.extend(self._decisions(indexes))
        experiences.extend(self._rejections(indexes))
        experiences.extend(self._position_management(indexes))
        experiences.extend(self._agent_contributions(indexes))
        experiences.extend(self._trades(indexes))
        experiences.extend(self._anomalies(indexes))
        return ExperienceBuild(experiences=tuple(experiences))

    def _decisions(self, values: _SourceIndexes) -> list[DecisionExperience]:
        result: list[DecisionExperience] = []
        for master in values.masters.values():
            discipline = values.discipline_by_master.get(master.proposal_id)
            risk = values.risk_by_master.get(master.proposal_id)
            intent = values.intent_by_master.get(master.proposal_id)
            missing: list[str] = []
            if discipline is None:
                missing.append(f"DISCIPLINE_OUTCOME:{master.proposal_id}")
            if risk is None:
                missing.append(f"RISK_OUTCOME:{master.proposal_id}")
            specialists = tuple(
                self._specialist_fact(item, values.evidence) for item in master.contributions
            )
            missing.extend(
                f"AGENT_EVIDENCE:{item.evidence_id}"
                for item in master.contributions
                if item.evidence_id not in values.evidence
            )
            status, missing_links = _status(missing)
            event = values.events.get(master.event_id)
            context = values.event_contexts.get(master.event_id)
            symbol = _symbol(event, risk, intent)
            if symbol is None:
                missing.append(f"RUNTIME_EVENT_SYMBOL:{master.event_id}")
                status, missing_links = _status(missing)
            setup_id, thesis_id, scenario_id = _identity_context(discipline, risk, intent)
            result.append(
                DecisionExperience(
                    occurred_at=master.as_of,
                    available_at=master.as_of,
                    symbol=symbol,
                    setup_id=setup_id,
                    thesis_id=thesis_id,
                    scenario_id=scenario_id,
                    regime=context.regime if context else None,
                    session=context.session if context else None,
                    outcome=master.decision.value,
                    attribution_status=status,
                    missing_links=missing_links,
                    provenance=_provenance(
                        event_ids=(master.event_id,),
                        bundle_ids=(master.bundle_id,),
                        evidence_ids=tuple(item.evidence_id for item in master.contributions),
                        master_ids=(master.proposal_id,),
                        discipline_ids=(discipline.outcome_id,) if discipline else (),
                        risk_ids=(risk.outcome_id,) if risk else (),
                        intent_ids=(intent.intent_id,) if intent else (),
                    ),
                    master_proposal_id=master.proposal_id,
                    evidence_bundle_id=master.bundle_id,
                    decision=master.decision,
                    actionable=master.actionable,
                    master_confidence=master.confidence,
                    disagreement=master.disagreement,
                    contradiction=master.contradiction,
                    specialists=specialists,
                    discipline_outcome_id=discipline.outcome_id if discipline else None,
                    discipline_result=discipline.result.value if discipline else None,
                    risk_outcome_id=risk.outcome_id if risk else None,
                    risk_result=risk.result.value if risk else None,
                    execution_intent_id=intent.intent_id if intent else None,
                    progressed_to=_progressed_to(master, discipline, risk, intent),
                )
            )
        return result

    @staticmethod
    def _specialist_fact(
        contribution: Any,
        evidence_by_id: dict[str, AgentEvidence],
    ) -> SpecialistDecisionFact:
        evidence = evidence_by_id.get(contribution.evidence_id)
        return SpecialistDecisionFact(
            specialist=contribution.agent_name,
            agent_evidence_id=contribution.evidence_id,
            status=contribution.status,
            direction=contribution.direction,
            confidence=evidence.confidence if evidence else None,
            uncertainty=contribution.uncertainty,
            evidence_quality=evidence.evidence_quality if evidence else None,
        )

    def _rejections(self, values: _SourceIndexes) -> list[RejectedDecisionExperience]:
        result: list[RejectedDecisionExperience] = []
        for discipline in values.disciplines.values():
            if discipline.result not in {DisciplineResult.REJECT, DisciplineResult.PAUSE}:
                continue
            master = values.masters.get(discipline.master_proposal_id)
            if master is None:
                continue
            result.append(
                _rejection_experience(
                    master,
                    RejectionLayer.DISCIPLINE,
                    discipline.outcome_id,
                    _reason_values(discipline.reason_codes),
                    discipline,
                    None,
                    values,
                )
            )
        for risk in values.risks.values():
            if risk.result not in {RiskResult.REJECT, RiskResult.EMERGENCY_STOP}:
                continue
            master = values.masters.get(risk.master_proposal_id)
            if master is None:
                continue
            linked_discipline = values.disciplines.get(risk.discipline_outcome_id)
            result.append(
                _rejection_experience(
                    master,
                    RejectionLayer.RISK,
                    risk.outcome_id,
                    _reason_values(risk.reason_codes),
                    linked_discipline,
                    risk,
                    values,
                )
            )
        for safety in values.safety.values():
            if safety.result not in {
                PositionActionSafetyResult.REJECT,
                PositionActionSafetyResult.EMERGENCY_BLOCK,
            }:
                continue
            management = values.management.get(safety.position_management_outcome_id)
            if management is None:
                continue
            source_intent_id = management.original_execution_intent_id
            intent = values.intents.get(source_intent_id) if source_intent_id else None
            if intent is None:
                continue
            master = values.masters.get(intent.master_proposal_id) if intent else None
            if master is None:
                continue
            context = values.event_contexts.get(master.event_id)
            status, missing_links = _status([])
            result.append(
                RejectedDecisionExperience(
                    occurred_at=safety.as_of,
                    available_at=safety.available_at,
                    symbol=intent.symbol,
                    setup_id=management.setup_id,
                    thesis_id=management.thesis_id,
                    scenario_id=management.scenario_id,
                    regime=context.regime if context else None,
                    session=context.session if context else None,
                    outcome=safety.result.value,
                    attribution_status=status,
                    missing_links=missing_links,
                    provenance=_provenance(
                        event_ids=(master.event_id,),
                        bundle_ids=(master.bundle_id,),
                        master_ids=(master.proposal_id,),
                        intent_ids=(intent.intent_id,),
                        management_ids=(management.outcome_id,),
                        safety_ids=(safety.safety_outcome_id,),
                    ),
                    rejection_layer=RejectionLayer.POSITION_ACTION_SAFETY,
                    source_proposal_id=management.outcome_id,
                    source_outcome_id=safety.safety_outcome_id,
                    reason_codes=_reason_values(safety.reason_codes),
                    master_confidence=master.confidence,
                    relevant_safety_state_ids=(safety.context_id,),
                )
            )
        return result

    def _position_management(
        self, values: _SourceIndexes
    ) -> list[PositionManagementExperience]:
        result: list[PositionManagementExperience] = []
        for management in values.management.values():
            safety = values.safety_by_management.get(management.outcome_id)
            action = values.action_by_management.get(management.outcome_id)
            action_id = action.intent_id if action else None
            transport = values.action_result_by_intent.get(action_id) if action_id else None
            applied = values.action_application_by_intent.get(action_id) if action_id else None
            source_intent_id = management.original_execution_intent_id
            source_intent = (
                values.intents.get(source_intent_id) if source_intent_id else None
            )
            missing: list[str] = []
            if source_intent is None:
                missing.append(f"EXECUTION_INTENT:{management.original_execution_intent_id}")
            if (
                management.original_execution_result_id is None
                or management.original_execution_result_id not in values.results
            ):
                missing.append(f"EXECUTION_RESULT:{management.original_execution_result_id}")
            status, missing_links = _status(missing)
            symbol = source_intent.symbol if source_intent else None
            result.append(
                PositionManagementExperience(
                    occurred_at=management.as_of,
                    available_at=management.available_at,
                    symbol=symbol,
                    setup_id=management.setup_id,
                    thesis_id=management.thesis_id,
                    scenario_id=management.scenario_id,
                    outcome=management.result.value,
                    attribution_status=status,
                    missing_links=missing_links,
                    provenance=_provenance(
                        intent_ids=(management.original_execution_intent_id,)
                        if management.original_execution_intent_id
                        else (),
                        result_ids=(management.original_execution_result_id,)
                        if management.original_execution_result_id
                        else (),
                        management_ids=(management.outcome_id,),
                        safety_ids=(safety.safety_outcome_id,) if safety else (),
                        action_ids=(action.intent_id,) if action else (),
                        action_result_ids=(transport.result_id,) if transport else (),
                    ),
                    position_management_outcome_id=management.outcome_id,
                    position_id=management.position_id,
                    original_execution_intent_id=management.original_execution_intent_id,
                    original_execution_result_id=management.original_execution_result_id,
                    management_result=management.result.value,
                    reason_codes=_reason_values(management.reason_codes),
                    current_thesis_lifecycle=management.current_thesis_lifecycle,
                    position_action_safety_outcome_id=(
                        safety.safety_outcome_id if safety else None
                    ),
                    position_action_intent_id=action.intent_id if action else None,
                    position_action_transport_result_id=(
                        transport.result_id if transport else None
                    ),
                    protection_reached_transport=bool(applied or transport),
                )
            )
        return result

    def _agent_contributions(
        self, values: _SourceIndexes
    ) -> list[AgentContributionExperience]:
        result: list[AgentContributionExperience] = []
        traded_master_ids = {
            intent.master_proposal_id
            for trade in values.trades
            if (intent := values.intents.get(trade.source_execution_intent_id)) is not None
        }
        rejected_master_ids = {
            item.master_proposal_id
            for item in values.disciplines.values()
            if item.result in {DisciplineResult.REJECT, DisciplineResult.PAUSE}
        } | {
            item.master_proposal_id
            for item in values.risks.values()
            if item.result in {RiskResult.REJECT, RiskResult.EMERGENCY_STOP}
        }
        for master in values.masters.values():
            context = values.event_contexts.get(master.event_id)
            symbol = _symbol(
                values.events.get(master.event_id),
                values.risk_by_master.get(master.proposal_id),
                values.intent_by_master.get(master.proposal_id),
            )
            symbol_missing = (
                [f"RUNTIME_EVENT_SYMBOL:{master.event_id}"] if symbol is None else []
            )
            discipline = values.discipline_by_master.get(master.proposal_id)
            risk = values.risk_by_master.get(master.proposal_id)
            setup_id, thesis_id, scenario_id = _identity_context(discipline, risk, None)
            for contribution in master.contributions:
                evidence = values.evidence.get(contribution.evidence_id)
                missing = (
                    symbol_missing
                    if evidence is not None
                    else [*symbol_missing, f"AGENT_EVIDENCE:{contribution.evidence_id}"]
                )
                status, missing_links = _status(missing)
                tool_ids = (
                    tuple(item.tool_result_id for item in evidence.tool_inputs)
                    if evidence
                    else ()
                )
                result.append(
                    AgentContributionExperience(
                        occurred_at=master.as_of,
                        available_at=master.as_of,
                        symbol=symbol,
                        setup_id=setup_id,
                        thesis_id=thesis_id,
                        scenario_id=scenario_id,
                        regime=context.regime if context else None,
                        session=context.session if context else None,
                        specialist=contribution.agent_name,
                        outcome=master.decision.value,
                        attribution_status=status,
                        missing_links=missing_links,
                        provenance=_provenance(
                            event_ids=(master.event_id,),
                            bundle_ids=(master.bundle_id,),
                            evidence_ids=(contribution.evidence_id,),
                            master_ids=(master.proposal_id,),
                            tool_ids=tool_ids,
                        ),
                        agent_evidence_id=contribution.evidence_id,
                        hypothesis_id=evidence.hypothesis_id if evidence else None,
                        hypothesis=evidence.hypothesis if evidence else None,
                        direction=evidence.direction if evidence else contribution.direction,
                        lifecycle=evidence.hypothesis_status if evidence else None,
                        status=contribution.status,
                        confidence=evidence.confidence if evidence else None,
                        uncertainty=contribution.uncertainty,
                        evidence_quality=evidence.evidence_quality if evidence else None,
                        evidence_for_count=len(evidence.evidence_for) if evidence else None,
                        evidence_against_count=len(evidence.evidence_against) if evidence else None,
                        tool_result_ids=tool_ids,
                        master_proposal_id=master.proposal_id,
                        master_decision=master.decision,
                        downstream_outcome=(
                            "TRADE_COMPLETED"
                            if master.proposal_id in traded_master_ids
                            else "REJECTED"
                            if master.proposal_id in rejected_master_ids
                            else None
                        ),
                    )
                )
        return result

    def _trades(self, values: _SourceIndexes) -> list[TradeExperience]:
        result: list[TradeExperience] = []
        for trade in values.trades:
            intent = values.intents.get(trade.source_execution_intent_id)
            fill = values.fill_by_intent.get(trade.source_execution_intent_id)
            execution_result = values.results.get(fill.execution_result_id) if fill else None
            master = values.masters.get(intent.master_proposal_id) if intent else None
            context = values.event_contexts.get(master.event_id) if master else None
            missing: list[str] = []
            if intent is None:
                missing.append(f"EXECUTION_INTENT:{trade.source_execution_intent_id}")
            if fill is None:
                missing.append(f"REPLAY_FILL:{trade.source_execution_intent_id}")
            elif execution_result is None:
                missing.append(f"EXECUTION_RESULT:{fill.execution_result_id}")
            if master is None:
                missing.append(
                    f"MASTER_PROPOSAL:{intent.master_proposal_id if intent else 'UNKNOWN'}"
                )
            status, missing_links = _status(missing)
            point_size = intent.point_size if intent else 0.01
            signed = 1.0 if trade.direction.value == Signal.BUY.value else -1.0
            pnl_points = (trade.exit_price - trade.entry_price) / point_size * signed
            initial_risk_points = abs(trade.entry_price - trade.initial_stop_loss) / point_size
            evidence_ids = (
                tuple(item.evidence_id for item in master.contributions) if master else ()
            )
            result_id = fill.execution_result_id if fill else None
            fill_id = fill.replay_fill_id if fill else None
            symbol = intent.symbol if intent else None
            result.append(
                TradeExperience(
                    occurred_at=trade.closed_at,
                    available_at=trade.closed_at,
                    symbol=symbol,
                    setup_id=intent.setup_id if intent else None,
                    thesis_id=intent.thesis_id if intent else None,
                    scenario_id=intent.scenario_id if intent else None,
                    regime=context.regime if context else None,
                    session=context.session if context else None,
                    outcome=trade.exit_reason,
                    attribution_status=status,
                    missing_links=missing_links,
                    provenance=_provenance(
                        event_ids=(master.event_id,) if master else (),
                        bundle_ids=(intent.evidence_bundle_id,) if intent else (),
                        evidence_ids=evidence_ids,
                        master_ids=(master.proposal_id,) if master else (),
                        discipline_ids=(intent.discipline_outcome_id,) if intent else (),
                        risk_ids=(intent.risk_outcome_id,) if intent else (),
                        intent_ids=(trade.source_execution_intent_id,),
                        result_ids=(result_id,) if result_id else (),
                        action_ids=(trade.source_position_action_intent_id,)
                        if trade.source_position_action_intent_id
                        else (),
                        replay_fill_ids=(fill_id,) if fill_id else (),
                        replay_trade_ids=(trade.replay_trade_id,),
                    ),
                    replay_trade_id=trade.replay_trade_id,
                    execution_intent_id=trade.source_execution_intent_id,
                    execution_result_id=result_id,
                    replay_fill_id=fill_id,
                    position_id=trade.position_id,
                    direction=Signal(trade.direction.value),
                    entry_time=trade.opened_at,
                    exit_time=trade.closed_at,
                    entry_price=trade.entry_price,
                    exit_price=trade.exit_price,
                    volume_lots=trade.volume_lots,
                    realized_pnl=pnl_points * trade.volume_lots,
                    r_outcome=(
                        pnl_points / initial_risk_points if initial_risk_points > 0 else None
                    ),
                    mfe_points=trade.mfe_points,
                    mae_points=trade.mae_points,
                    holding_seconds=(trade.closed_at - trade.opened_at).total_seconds(),
                    exit_cause=trade.exit_reason,
                    stop_triggered=trade.exit_reason == "PROTECTIVE_STOP",
                    explicit_position_exit=trade.exit_reason == "POSITION_ACTION_CLOSE",
                    source_position_action_intent_id=trade.source_position_action_intent_id,
                    master_confidence=master.confidence if master else None,
                    disagreement=master.disagreement if master else None,
                    contradiction=master.contradiction if master else None,
                    specialist_evidence_ids=evidence_ids,
                )
            )
        return result

    def _anomalies(self, values: _SourceIndexes) -> list[RuntimeAnomalyExperience]:
        result: list[RuntimeAnomalyExperience] = []
        for evidence in values.evidence.values():
            if evidence.status is AgentStatus.ERROR:
                result.append(
                    _anomaly(
                        anomaly_type="AGENT_ERROR",
                        source_id=evidence.evidence_id,
                        at=evidence.available_at,
                        symbol=None,
                        reason_codes=("AGENT_ERROR",),
                        provenance=_provenance(evidence_ids=(evidence.evidence_id,)),
                    )
                )
        for execution_result in values.results.values():
            if execution_result.status in {
                ExecutionResultStatus.UNKNOWN,
                ExecutionResultStatus.FAILED,
            }:
                result.append(
                    _anomaly(
                        anomaly_type=f"EXECUTION_{execution_result.status.value}",
                        source_id=execution_result.result_id,
                        at=execution_result.available_at,
                        symbol=execution_result.symbol,
                        reason_codes=(
                            execution_result.reason_code.value
                            if execution_result.reason_code
                            else execution_result.status.value,
                        ),
                        provenance=_provenance(
                            intent_ids=(execution_result.execution_intent_id,),
                            result_ids=(execution_result.result_id,),
                        ),
                    )
                )
        for report in values.reconciliations.values():
            for finding in report.findings:
                if finding.kind is ReconciliationKind.MATCHED:
                    continue
                result.append(
                    _anomaly(
                        anomaly_type=f"RECONCILIATION_{finding.kind.value}",
                        source_id=finding.finding_id,
                        at=report.available_at,
                        symbol=None,
                        reason_codes=(finding.reason_code,),
                        reconciliation_id=report.report_id,
                    )
                )
        for readiness in values.readiness.values():
            if readiness.status is not ResumeStatus.BLOCKED:
                continue
            result.append(
                _anomaly(
                    anomaly_type="UNSAFE_READINESS",
                    source_id=readiness.readiness_id,
                    at=readiness.as_of,
                    symbol=None,
                    reason_codes=_reason_values(readiness.reason_codes),
                    readiness_id=readiness.readiness_id,
                )
            )
        return result


class _SourceIndexes:
    def __init__(self, sources: AttributionSources) -> None:
        self.events = _index(sources.runtime_events, "event_id")
        self.masters = _index(sources.masters, "proposal_id")
        self.disciplines = _index(sources.disciplines, "outcome_id")
        self.risks = _index(sources.risks, "outcome_id")
        self.intents = _index(sources.execution_intents, "intent_id")
        self.results = _index(sources.execution_results, "result_id")
        self.evidence = _index(sources.agent_evidence, "evidence_id")
        self.management = _index(sources.position_management, "outcome_id")
        self.safety = _index(sources.position_action_safety, "safety_outcome_id")
        self.actions = _index(sources.position_action_intents, "intent_id")
        self.action_results = _index(sources.position_action_results, "result_id")
        self.reconciliations = _index(sources.reconciliations, "report_id")
        self.readiness = _index(sources.readiness, "readiness_id")
        self.discipline_by_master = {
            item.master_proposal_id: item for item in self.disciplines.values()
        }
        self.risk_by_master = {item.master_proposal_id: item for item in self.risks.values()}
        self.intent_by_master = {item.master_proposal_id: item for item in self.intents.values()}
        self.safety_by_management = {
            item.position_management_outcome_id: item for item in self.safety.values()
        }
        self.action_by_management = {
            item.position_management_outcome_id: item for item in self.actions.values()
        }
        self.action_result_by_intent = {
            item.position_action_intent_id: item for item in self.action_results.values()
        }
        outcome = sources.replay_outcomes
        self.trades = outcome.trades if outcome else ()
        self.fill_by_intent = {
            item.execution_intent_id: item for item in (outcome.fills if outcome else ())
        }
        self.event_contexts = {
            item.runtime_event_id: item for item in (outcome.event_contexts if outcome else ())
        }
        self.action_application_by_intent = {
            item.position_action_intent_id: item
            for item in (outcome.action_applications if outcome else ())
        }


def _symbol(
    event: RuntimeEvent | None,
    risk: RiskOutcome | None,
    intent: ExecutionIntent | None,
) -> str | None:
    if event and event.symbol:
        return event.symbol
    if risk:
        return risk.symbol
    return intent.symbol if intent else None


def _identity_context(
    discipline: DisciplineOutcome | None,
    risk: RiskOutcome | None,
    intent: ExecutionIntent | None,
) -> tuple[str | None, str | None, str | None]:
    for value in (intent, risk, discipline):
        if value is not None:
            return value.setup_id, value.thesis_id, value.scenario_id
    return None, None, None


def _progressed_to(
    master: MasterProposal,
    discipline: DisciplineOutcome | None,
    risk: RiskOutcome | None,
    intent: ExecutionIntent | None,
) -> str:
    if master.decision is Signal.HOLD:
        return "MASTER_HOLD"
    if discipline is None:
        return "MASTER"
    if discipline.result is not DisciplineResult.PASS:
        return f"DISCIPLINE_{discipline.result.value}"
    if risk is None:
        return "DISCIPLINE_PASS"
    if risk.result is not RiskResult.PASS:
        return f"RISK_{risk.result.value}"
    return "EXECUTION_INTENT" if intent else "RISK_PASS"


def _rejection_experience(
    master: MasterProposal,
    layer: RejectionLayer,
    source_outcome_id: str,
    reason_codes: tuple[str, ...],
    discipline: DisciplineOutcome | None,
    risk: RiskOutcome | None,
    values: _SourceIndexes,
) -> RejectedDecisionExperience:
    event = values.events.get(master.event_id)
    context = values.event_contexts.get(master.event_id)
    symbol = _symbol(event, risk, None)
    missing = [f"RUNTIME_EVENT_SYMBOL:{master.event_id}"] if symbol is None else []
    status, missing_links = _status(missing)
    setup_id, thesis_id, scenario_id = _identity_context(discipline, risk, None)
    return RejectedDecisionExperience(
        occurred_at=(risk.as_of if risk else discipline.as_of if discipline else master.as_of),
        available_at=(
            risk.available_at
            if risk
            else discipline.available_at
            if discipline
            else master.as_of
        ),
        symbol=symbol,
        setup_id=setup_id,
        thesis_id=thesis_id,
        scenario_id=scenario_id,
        regime=context.regime if context else None,
        session=context.session if context else None,
        outcome=layer.value,
        attribution_status=status,
        missing_links=missing_links,
        provenance=_provenance(
            event_ids=(master.event_id,),
            bundle_ids=(master.bundle_id,),
            evidence_ids=tuple(item.evidence_id for item in master.contributions),
            master_ids=(master.proposal_id,),
            discipline_ids=(discipline.outcome_id,) if discipline else (),
            risk_ids=(risk.outcome_id,) if risk else (),
        ),
        rejection_layer=layer,
        source_proposal_id=master.proposal_id,
        source_outcome_id=source_outcome_id,
        reason_codes=reason_codes,
        master_confidence=master.confidence,
    )


def _anomaly(
    *,
    anomaly_type: str,
    source_id: str,
    at: Any,
    symbol: str | None,
    reason_codes: tuple[str, ...],
    provenance: ExperienceProvenance | None = None,
    reconciliation_id: str | None = None,
    readiness_id: str | None = None,
) -> RuntimeAnomalyExperience:
    actual_provenance = provenance or _provenance(
        reconciliation_ids=(reconciliation_id,) if reconciliation_id else (),
        readiness_ids=(readiness_id,) if readiness_id else (),
    )
    return RuntimeAnomalyExperience(
        occurred_at=at,
        available_at=at,
        symbol=symbol,
        outcome=anomaly_type,
        provenance=actual_provenance,
        anomaly_type=anomaly_type,
        severity="ERROR" if "ERROR" in anomaly_type or "UNKNOWN" in anomaly_type else "WARNING",
        source_semantic_id=source_id,
        reason_codes=reason_codes,
    )


def _provenance(
    *,
    event_ids: tuple[str, ...] = (),
    bundle_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    master_ids: tuple[str, ...] = (),
    discipline_ids: tuple[str, ...] = (),
    risk_ids: tuple[str, ...] = (),
    intent_ids: tuple[str, ...] = (),
    result_ids: tuple[str, ...] = (),
    management_ids: tuple[str, ...] = (),
    safety_ids: tuple[str, ...] = (),
    action_ids: tuple[str, ...] = (),
    action_result_ids: tuple[str, ...] = (),
    replay_fill_ids: tuple[str, ...] = (),
    replay_trade_ids: tuple[str, ...] = (),
    tool_ids: tuple[str, ...] = (),
    reconciliation_ids: tuple[str, ...] = (),
    readiness_ids: tuple[str, ...] = (),
) -> ExperienceProvenance:
    return ExperienceProvenance(
        runtime_event_ids=event_ids,
        evidence_bundle_ids=bundle_ids,
        agent_evidence_ids=evidence_ids,
        master_proposal_ids=master_ids,
        discipline_outcome_ids=discipline_ids,
        risk_outcome_ids=risk_ids,
        execution_intent_ids=intent_ids,
        execution_result_ids=result_ids,
        position_management_outcome_ids=management_ids,
        position_action_safety_outcome_ids=safety_ids,
        position_action_intent_ids=action_ids,
        position_action_transport_result_ids=action_result_ids,
        replay_fill_ids=replay_fill_ids,
        replay_trade_ids=replay_trade_ids,
        tool_result_ids=tool_ids,
        reconciliation_report_ids=reconciliation_ids,
        resume_readiness_ids=readiness_ids,
    )
