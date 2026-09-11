"""Command-line interface for deterministic Phase 8 daily reflection."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

from axq.experience.store import SQLiteExperienceStore
from axq.reflection.contracts import DailyReflection, ReflectionPolicy
from axq.reflection.daily import build_daily_reflection
from axq.reflection.proposal_cli import handle_proposal_command, register_proposal_commands
from axq.reflection.store import SQLiteReflectionStore
from axq.reflection.weekly_cli import handle_weekly_command, register_weekly_commands


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build-daily-reflections")
    build.add_argument("--experience-store", type=Path, required=True)
    build.add_argument("--reflection-store", type=Path, required=True)
    build.add_argument("--start-date", type=date.fromisoformat, required=True)
    build.add_argument("--through-date", type=date.fromisoformat, required=True)
    build.add_argument("--policy", type=Path)

    show = commands.add_parser("show-daily-reflection")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--date", type=date.fromisoformat, required=True)
    show.add_argument("--policy-id")

    report = commands.add_parser("report")
    report.add_argument("--store", type=Path, required=True)
    register_weekly_commands(commands)
    register_proposal_commands(commands)
    return parser


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _load_policy(path: Path | None) -> ReflectionPolicy:
    return (
        ReflectionPolicy()
        if path is None
        else ReflectionPolicy.model_validate_json(path.read_text(encoding="utf-8"))
    )


def _semantic_payload(reflection: DailyReflection) -> dict[str, object]:
    return reflection.model_dump(
        mode="json",
        exclude={"reflection_id", "supersedes_reflection_id"},
    )


def _days(start: date, through: date) -> tuple[date, ...]:
    if through < start:
        raise ValueError("through-date cannot be before start-date")
    return tuple(start + timedelta(days=offset) for offset in range((through - start).days + 1))


def _latest_records(store: SQLiteReflectionStore) -> tuple[DailyReflection, ...]:
    latest: dict[tuple[object, str], DailyReflection] = {}
    for reflection in store.reflections():
        latest[(reflection.period_start, reflection.policy_id)] = reflection
    return tuple(sorted(latest.values(), key=lambda item: (item.period_start, item.policy_id)))


def _build(args: argparse.Namespace) -> int:
    policy = _load_policy(args.policy)
    experiences = SQLiteExperienceStore(args.experience_store).experiences()
    store = SQLiteReflectionStore(args.reflection_store)
    store.append_policy(policy)
    created = 0
    reused = 0
    reflections: list[DailyReflection] = []
    for day in _days(args.start_date, args.through_date):
        draft = build_daily_reflection(experiences, day, policy)
        latest = store.latest(draft.period_start, policy.policy_id)
        if latest is not None and _semantic_payload(latest) == _semantic_payload(draft):
            reflection = latest
            reused += 1
        else:
            reflection = (
                draft
                if latest is None
                else build_daily_reflection(
                    experiences,
                    day,
                    policy,
                    supersedes_reflection_id=latest.reflection_id,
                )
            )
            store.append(reflection)
            created += 1
        reflections.append(reflection)
    store.sync()
    _emit(
        {
            "created": created,
            "finding_count": sum(len(item.findings) for item in reflections),
            "guard_count": sum(len(item.sample_guards) for item in reflections),
            "policy_id": policy.policy_id,
            "reflection_ids": [item.reflection_id for item in reflections],
            "reused": reused,
            "start_date": args.start_date.isoformat(),
            "through_date": args.through_date.isoformat(),
        }
    )
    return 0


def _show(args: argparse.Namespace) -> int:
    records = tuple(
        item
        for item in _latest_records(SQLiteReflectionStore(args.store))
        if item.period_start.date() == args.date
        and (args.policy_id is None or item.policy_id == args.policy_id)
    )
    if not records:
        raise SystemExit("no daily reflection found")
    if len(records) > 1:
        raise SystemExit("multiple policies found; specify --policy-id")
    _emit(records[0].model_dump(mode="json"))
    return 0


def _report(args: argparse.Namespace) -> int:
    records = _latest_records(SQLiteReflectionStore(args.store))
    finding_categories = Counter(
        finding.category.value for reflection in records for finding in reflection.findings
    )
    finding_reasons = Counter(
        finding.reason_code for reflection in records for finding in reflection.findings
    )
    finding_signals = Counter(
        finding.signal.value for reflection in records for finding in reflection.findings
    )
    guard_statuses = Counter(
        guard.status.value for reflection in records for guard in reflection.sample_guards
    )
    _emit(
        {
            "days": len(records),
            "finding_category_counts": dict(sorted(finding_categories.items())),
            "finding_count": sum(finding_categories.values()),
            "finding_reason_counts": dict(sorted(finding_reasons.items())),
            "finding_signal_counts": dict(sorted(finding_signals.items())),
            "guard_count": sum(guard_statuses.values()),
            "guard_status_counts": dict(sorted(guard_statuses.items())),
            "reflection_ids": [item.reflection_id for item in records],
        }
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    weekly_result = handle_weekly_command(args)
    if weekly_result is not None:
        return weekly_result
    proposal_result = handle_proposal_command(args)
    if proposal_result is not None:
        return proposal_result
    if args.command == "build-daily-reflections":
        return _build(args)
    if args.command == "show-daily-reflection":
        return _show(args)
    if args.command == "report":
        return _report(args)
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
