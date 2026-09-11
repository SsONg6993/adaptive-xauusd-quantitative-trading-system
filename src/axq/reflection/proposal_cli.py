"""CLI handlers for advisory improvement proposals."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from axq.experience.store import SQLiteExperienceStore
from axq.reflection.proposal_contracts import (
    ImprovementProposal,
    ImprovementProposalPolicy,
    ProposalStatus,
    ProposalStatusTransition,
)
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.proposals import build_improvement_proposals
from axq.reflection.store import SQLiteReflectionStore
from axq.reflection.weekly_contracts import TransitionActionKind
from axq.reflection.weekly_store import SQLiteWeeklyReflectionStore


def register_proposal_commands(commands: Any) -> None:
    build = commands.add_parser("build-improvement-proposals")
    build.add_argument("--experience-store", type=Path, required=True)
    build.add_argument("--daily-store", type=Path, required=True)
    build.add_argument("--weekly-store", type=Path, required=True)
    build.add_argument("--proposal-store", type=Path, required=True)
    build.add_argument("--policy", type=Path)

    show = commands.add_parser("show-improvement-proposal")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--proposal-id", required=True)

    summary = commands.add_parser("proposal-summary")
    summary.add_argument("--store", type=Path, required=True)

    transition = commands.add_parser("transition-proposal")
    transition.add_argument("--store", type=Path, required=True)
    transition.add_argument("--proposal-id", required=True)
    transition.add_argument("--proposal-key", required=True)
    transition.add_argument("--from-status", choices=list(ProposalStatus), required=True)
    transition.add_argument("--to-status", choices=list(ProposalStatus), required=True)
    transition.add_argument("--effective-at", type=datetime.fromisoformat, required=True)
    transition.add_argument("--action-kind", choices=list(TransitionActionKind), required=True)
    transition.add_argument("--actor-id", required=True)
    transition.add_argument("--action-id", required=True)
    transition.add_argument("--reason-code", required=True)
    transition.add_argument("--evaluation-id", action="append", default=[])
    transition.add_argument("--previous-transition-id")

    history = commands.add_parser("show-proposal-history")
    history.add_argument("--store", type=Path, required=True)
    history.add_argument("--proposal-id", required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _policy(path: Path | None) -> ImprovementProposalPolicy:
    return (
        ImprovementProposalPolicy()
        if path is None
        else ImprovementProposalPolicy.model_validate_json(path.read_text(encoding="utf-8"))
    )


def _semantic_payload(proposal: ImprovementProposal) -> dict[str, object]:
    return proposal.model_dump(
        mode="json", exclude={"proposal_id", "supersedes_proposal_id"}
    )


def _latest(store: SQLiteImprovementProposalStore) -> tuple[ImprovementProposal, ...]:
    records: dict[tuple[str, str], ImprovementProposal] = {}
    for proposal in store.proposals():
        records[(proposal.proposal_key, proposal.policy_id)] = proposal
    return tuple(sorted(records.values(), key=lambda item: (item.proposal_key, item.policy_id)))


def _build(args: argparse.Namespace) -> int:
    policy = _policy(args.policy)
    weekly_store = SQLiteWeeklyReflectionStore(args.weekly_store)
    weekly = weekly_store.reflections()
    statuses = {
        pattern.pattern_id: weekly_store.current_status(pattern.pattern_id)
        for reflection in weekly
        for pattern in (*reflection.success_patterns, *reflection.failure_patterns)
    }
    result = build_improvement_proposals(
        weekly,
        SQLiteReflectionStore(args.daily_store).reflections(),
        SQLiteExperienceStore(args.experience_store).experiences(),
        policy,
        statuses,
    )
    store = SQLiteImprovementProposalStore(args.proposal_store)
    store.append_policy(policy)
    created = 0
    reused = 0
    superseded = 0
    records: list[ImprovementProposal] = []
    for draft in result.proposals:
        latest = store.latest(draft.proposal_key, policy.policy_id)
        if latest is not None and _semantic_payload(latest) == _semantic_payload(draft):
            record = latest
            reused += 1
        else:
            record = draft
            if latest is not None:
                record = ImprovementProposal(
                    **draft.model_dump(
                        exclude={"proposal_id", "proposal_key", "supersedes_proposal_id"}
                    ),
                    supersedes_proposal_id=latest.proposal_id,
                )
                superseded += 1
            store.append(record)
            created += 1
        records.append(record)
    store.sync()
    _emit(
        {
            "assessed_pattern_keys": result.assessed_pattern_keys,
            "created": created,
            "eligible_pattern_keys": result.eligible_pattern_keys,
            "evidence_guard_count": sum(len(item.evidence_guards) for item in records),
            "insufficient_pattern_keys": result.insufficient_pattern_keys,
            "policy_id": policy.policy_id,
            "proposal_ids": [item.proposal_id for item in records],
            "reused": reused,
            "superseded": superseded,
            "target_counts": dict(
                sorted(Counter(item.target_component.value for item in records).items())
            ),
        }
    )
    return 0


def _show(args: argparse.Namespace) -> int:
    proposal = SQLiteImprovementProposalStore(args.store).proposal(args.proposal_id)
    if proposal is None:
        raise SystemExit("improvement proposal not found")
    _emit(proposal.model_dump(mode="json"))
    return 0


def _summary(args: argparse.Namespace) -> int:
    store = SQLiteImprovementProposalStore(args.store)
    all_proposals = store.proposals()
    proposals = _latest(store)
    _emit(
        {
            "category_counts": dict(
                sorted(Counter(item.category.value for item in proposals).items())
            ),
            "evidence_guard_count": sum(len(item.evidence_guards) for item in proposals),
            "proposal_ids": [item.proposal_id for item in proposals],
            "proposals": len(proposals),
            "source_counts": {
                "daily_reflections": sum(
                    len(item.supporting_daily_reflection_ids) for item in proposals
                ),
                "experiences": sum(len(item.supporting_experience_ids) for item in proposals),
                "findings": sum(len(item.supporting_finding_ids) for item in proposals),
                "weekly_patterns": sum(len(item.supporting_pattern_ids) for item in proposals),
                "weekly_reflections": sum(
                    len(item.supporting_weekly_reflection_ids) for item in proposals
                ),
            },
            "status_counts": dict(
                sorted(
                    Counter(
                        store.current_status(item.proposal_id).value for item in proposals
                    ).items()
                )
            ),
            "superseding_proposals": sum(
                item.supersedes_proposal_id is not None for item in all_proposals
            ),
            "target_counts": dict(
                sorted(Counter(item.target_component.value for item in proposals).items())
            ),
            "transitions": sum(
                len(store.transition_history(item.proposal_id)) for item in all_proposals
            ),
        }
    )
    return 0


def _transition(args: argparse.Namespace) -> int:
    store = SQLiteImprovementProposalStore(args.store)
    transition = ProposalStatusTransition(
        proposal_id=args.proposal_id,
        proposal_key=args.proposal_key,
        from_status=ProposalStatus(args.from_status),
        to_status=ProposalStatus(args.to_status),
        effective_at=args.effective_at,
        action_kind=TransitionActionKind(args.action_kind),
        actor_id=args.actor_id,
        action_id=args.action_id,
        reason_code=args.reason_code,
        supporting_evaluation_ids=tuple(args.evaluation_id),
        previous_transition_id=args.previous_transition_id,
    )
    inserted = store.append_transition(transition)
    store.sync()
    _emit(
        {
            "current_status": store.current_status(transition.proposal_id).value,
            "inserted": inserted,
            "transition_id": transition.transition_id,
        }
    )
    return 0


def _history(args: argparse.Namespace) -> int:
    store = SQLiteImprovementProposalStore(args.store)
    proposal = store.proposal(args.proposal_id)
    if proposal is None:
        raise SystemExit("improvement proposal not found")
    history = store.transition_history(args.proposal_id)
    _emit(
        {
            "current_status": store.current_status(args.proposal_id).value,
            "proposal": proposal.model_dump(mode="json"),
            "transitions": [item.model_dump(mode="json") for item in history],
        }
    )
    return 0


def handle_proposal_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "build-improvement-proposals": _build,
        "show-improvement-proposal": _show,
        "proposal-summary": _summary,
        "transition-proposal": _transition,
        "show-proposal-history": _history,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
