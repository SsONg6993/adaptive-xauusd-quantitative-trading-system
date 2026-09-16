"""CLI registration and handlers for deterministic weekly reflection."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from axq.experience.store import SQLiteExperienceStore
from axq.reflection.store import SQLiteReflectionStore
from axq.reflection.weekly import build_weekly_reflection
from axq.reflection.weekly_contracts import (
    KnowledgeStatus,
    PatternStatusTransition,
    TransitionActionKind,
    WeeklyReflection,
    WeeklyReflectionPolicy,
)
from axq.reflection.weekly_store import SQLiteWeeklyReflectionStore


def register_weekly_commands(commands: Any) -> None:
    build = commands.add_parser("build-weekly-reflections")
    build.add_argument("--experience-store", type=Path, required=True)
    build.add_argument("--daily-store", type=Path, required=True)
    build.add_argument("--weekly-store", type=Path, required=True)
    build.add_argument("--daily-policy-id", required=True)
    build.add_argument("--start-week", type=date.fromisoformat, required=True)
    build.add_argument("--through-week", type=date.fromisoformat, required=True)
    build.add_argument("--policy", type=Path)

    show = commands.add_parser("show-weekly-reflection")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--week-start", type=date.fromisoformat, required=True)
    show.add_argument("--policy-id")

    summary = commands.add_parser("weekly-summary")
    summary.add_argument("--store", type=Path, required=True)

    transition = commands.add_parser("transition-pattern")
    transition.add_argument("--store", type=Path, required=True)
    transition.add_argument("--pattern-id", required=True)
    transition.add_argument("--pattern-key", required=True)
    transition.add_argument("--from-status", choices=list(KnowledgeStatus), required=True)
    transition.add_argument("--to-status", choices=list(KnowledgeStatus), required=True)
    transition.add_argument("--effective-at", type=datetime.fromisoformat, required=True)
    transition.add_argument("--action-kind", choices=list(TransitionActionKind), required=True)
    transition.add_argument("--actor-id", required=True)
    transition.add_argument("--action-id", required=True)
    transition.add_argument("--reason-code", required=True)
    transition.add_argument("--evaluation-id", action="append", default=[])
    transition.add_argument("--previous-transition-id")

    history = commands.add_parser("show-pattern-history")
    history.add_argument("--store", type=Path, required=True)
    history.add_argument("--pattern-id", required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _week_dates(start: date, through: date) -> tuple[date, ...]:
    if start.weekday() != 0 or through.weekday() != 0:
        raise ValueError("weekly start and through dates must be Mondays")
    if through < start:
        raise ValueError("through-week cannot be before start-week")
    return tuple(
        start + timedelta(days=offset)
        for offset in range(0, (through - start).days + 1, 7)
    )


def _policy(path: Path | None, daily_policy_id: str) -> WeeklyReflectionPolicy:
    policy = (
        WeeklyReflectionPolicy(daily_policy_id=daily_policy_id)
        if path is None
        else WeeklyReflectionPolicy.model_validate_json(path.read_text(encoding="utf-8"))
    )
    if policy.daily_policy_id != daily_policy_id:
        raise ValueError("weekly policy does not bind requested daily policy")
    return policy


def _semantic_payload(reflection: WeeklyReflection) -> dict[str, object]:
    return reflection.model_dump(
        mode="json",
        exclude={"reflection_id", "supersedes_weekly_reflection_id"},
    )


def _latest(store: SQLiteWeeklyReflectionStore) -> tuple[WeeklyReflection, ...]:
    records: dict[tuple[datetime, str], WeeklyReflection] = {}
    for reflection in store.reflections():
        records[(reflection.week_start, reflection.weekly_policy_id)] = reflection
    return tuple(
        sorted(records.values(), key=lambda item: (item.week_start, item.weekly_policy_id))
    )


def _build(args: argparse.Namespace) -> int:
    policy = _policy(args.policy, args.daily_policy_id)
    daily = SQLiteReflectionStore(args.daily_store).reflections()
    experiences = SQLiteExperienceStore(args.experience_store).experiences()
    store = SQLiteWeeklyReflectionStore(args.weekly_store)
    store.append_policy(policy)
    created = 0
    reused = 0
    records: list[WeeklyReflection] = []
    for week in _week_dates(args.start_week, args.through_week):
        draft = build_weekly_reflection(daily, experiences, week, policy)
        latest = store.latest(draft.week_start, policy.policy_id)
        if latest is not None and _semantic_payload(latest) == _semantic_payload(draft):
            record = latest
            reused += 1
        else:
            record = (
                draft
                if latest is None
                else build_weekly_reflection(
                    daily,
                    experiences,
                    week,
                    policy,
                    supersedes_weekly_reflection_id=latest.reflection_id,
                )
            )
            store.append(record)
            created += 1
        records.append(record)
    store.sync()
    _emit(
        {
            "complete_weeks": sum(not item.missing_daily_periods for item in records),
            "created": created,
            "failure_patterns": sum(len(item.failure_patterns) for item in records),
            "incomplete_weeks": sum(bool(item.missing_daily_periods) for item in records),
            "policy_id": policy.policy_id,
            "reflection_ids": [item.reflection_id for item in records],
            "reused": reused,
            "success_patterns": sum(len(item.success_patterns) for item in records),
        }
    )
    return 0


def _show(args: argparse.Namespace) -> int:
    records = tuple(
        item
        for item in _latest(SQLiteWeeklyReflectionStore(args.store))
        if item.week_start.date() == args.week_start
        and (args.policy_id is None or item.weekly_policy_id == args.policy_id)
    )
    if not records:
        raise SystemExit("no weekly reflection found")
    if len(records) > 1:
        raise SystemExit("multiple weekly policies found; specify --policy-id")
    _emit(records[0].model_dump(mode="json"))
    return 0


def _summary(args: argparse.Namespace) -> int:
    store = SQLiteWeeklyReflectionStore(args.store)
    records = _latest(store)
    patterns = tuple(
        pattern
        for reflection in records
        for pattern in (*reflection.success_patterns, *reflection.failure_patterns)
    )
    guards = Counter(
        guard.status.value for reflection in records for guard in reflection.sample_guards
    )
    statuses = Counter(store.current_status(pattern.pattern_id).value for pattern in patterns)
    _emit(
        {
            "complete_weeks": sum(not item.missing_daily_periods for item in records),
            "failure_patterns": sum(len(item.failure_patterns) for item in records),
            "guard_status_counts": dict(sorted(guards.items())),
            "incomplete_weeks": sum(bool(item.missing_daily_periods) for item in records),
            "knowledge_status_counts": dict(sorted(statuses.items())),
            "reflection_ids": [item.reflection_id for item in records],
            "success_patterns": sum(len(item.success_patterns) for item in records),
            "weeks": len(records),
        }
    )
    return 0


def _transition(args: argparse.Namespace) -> int:
    store = SQLiteWeeklyReflectionStore(args.store)
    transition = PatternStatusTransition(
        pattern_id=args.pattern_id,
        pattern_key=args.pattern_key,
        from_status=KnowledgeStatus(args.from_status),
        to_status=KnowledgeStatus(args.to_status),
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
            "current_status": store.current_status(transition.pattern_id).value,
            "inserted": inserted,
            "transition_id": transition.transition_id,
        }
    )
    return 0


def _history(args: argparse.Namespace) -> int:
    store = SQLiteWeeklyReflectionStore(args.store)
    pattern = store.pattern(args.pattern_id)
    if pattern is None:
        raise SystemExit("pattern not found")
    history = store.transition_history(args.pattern_id)
    _emit(
        {
            "current_status": store.current_status(args.pattern_id).value,
            "pattern": pattern.model_dump(mode="json"),
            "transitions": [item.model_dump(mode="json") for item in history],
        }
    )
    return 0


def handle_weekly_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "build-weekly-reflections": _build,
        "show-weekly-reflection": _show,
        "weekly-summary": _summary,
        "transition-pattern": _transition,
        "show-pattern-history": _history,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
