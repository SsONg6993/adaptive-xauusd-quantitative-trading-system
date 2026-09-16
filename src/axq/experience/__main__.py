"""Command-line interface for deterministic Phase 8 experience reconstruction."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from axq.experience.analytics import summarize_experiences
from axq.experience.attribution import AttributionSources, OutcomeAttributionBuilder
from axq.experience.contracts import ExperienceType
from axq.experience.store import SQLiteExperienceStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build-experiences")
    build.add_argument("--runtime-journal", type=Path, required=True)
    build.add_argument("--execution-ledger", type=Path, required=True)
    build.add_argument("--position-action-ledger", type=Path, required=True)
    build.add_argument("--replay-outcomes", type=Path, required=True)
    build.add_argument("--store", type=Path, required=True)
    build.add_argument("--expected-trades", type=int)

    show = commands.add_parser("show-experiences")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--type", choices=[item.value for item in ExperienceType])
    show.add_argument("--limit", type=int, default=100)

    summary = commands.add_parser("summary")
    summary.add_argument("--store", type=Path, required=True)
    return parser


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    store = SQLiteExperienceStore(args.store)
    if args.command == "build-experiences":
        sources = AttributionSources.from_paths(
            runtime_journal_path=args.runtime_journal,
            execution_ledger_path=args.execution_ledger,
            position_action_ledger_path=args.position_action_ledger,
            replay_outcomes_path=args.replay_outcomes,
        )
        build = OutcomeAttributionBuilder().build(sources)
        trade_count = len(build.of_type(ExperienceType.TRADE))
        if args.expected_trades is not None and trade_count != args.expected_trades:
            raise SystemExit(
                f"trade reconciliation failed: expected {args.expected_trades}, got {trade_count}"
            )
        inserted = store.append_many(build.experiences)
        store.sync()
        _emit(
            {
                "build_id": build.build_id,
                "inserted": inserted,
                "total": len(build.experiences),
                "trade_count": trade_count,
                "counts": {
                    key.value: value for key, value in sorted(store.counts().items())
                },
            }
        )
        return 0
    if args.command == "show-experiences":
        kind = ExperienceType(args.type) if args.type else None
        records = store.experiences(kind)
        _emit([item.model_dump(mode="json") for item in records[: args.limit]])
        return 0
    if args.command == "summary":
        _emit(summarize_experiences(store.experiences()).model_dump(mode="json"))
        return 0
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
