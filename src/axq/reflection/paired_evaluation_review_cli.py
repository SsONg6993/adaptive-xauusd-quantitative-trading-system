"""CLI handlers for append-only operator review of paired evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from axq.reflection.paired_evaluation_review_contracts import PairedEvaluationReview
from axq.reflection.paired_evaluation_review_store import SQLitePairedEvaluationReviewStore


def register_paired_evaluation_review_commands(commands: Any) -> None:
    record = commands.add_parser("record-paired-evaluation-review")
    record.add_argument("--store", type=Path, required=True)
    record.add_argument("--review", type=Path, required=True)

    show = commands.add_parser("show-paired-evaluation-review")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--review-id", required=True)

    history = commands.add_parser("show-paired-evaluation-review-history")
    history.add_argument("--store", type=Path, required=True)
    history.add_argument("--result-id", required=True)

    summary = commands.add_parser("paired-evaluation-review-summary")
    summary.add_argument("--store", type=Path, required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _record(args: argparse.Namespace) -> int:
    review = PairedEvaluationReview.model_validate_json(args.review.read_bytes())
    store = SQLitePairedEvaluationReviewStore(args.store)
    appended = store.append(review)
    store.sync()
    _emit({"appended": appended, "review_id": review.review_id})
    return 0


def _show(args: argparse.Namespace) -> int:
    review = SQLitePairedEvaluationReviewStore(args.store).review(args.review_id)
    if review is None:
        raise SystemExit("paired evaluation review not found")
    _emit(review.model_dump(mode="json"))
    return 0


def _history(args: argparse.Namespace) -> int:
    history = SQLitePairedEvaluationReviewStore(args.store).history(args.result_id)
    _emit(
        {
            "current_review_id": None if not history else history[-1].review_id,
            "result_id": args.result_id,
            "review_ids": [item.review_id for item in history],
            "reviews": [item.model_dump(mode="json") for item in history],
        }
    )
    return 0


def _summary(args: argparse.Namespace) -> int:
    store = SQLitePairedEvaluationReviewStore(args.store)
    reviews = store.reviews()
    grouped: dict[str, list[PairedEvaluationReview]] = {}
    for review in reviews:
        grouped.setdefault(review.result_id, []).append(review)
    current = tuple(
        terminal
        for result_id in sorted(grouped)
        if (terminal := store.current(result_id)) is not None
    )
    _emit(
        {
            "current_decision_counts": dict(
                sorted(Counter(item.decision.value for item in current).items())
            ),
            "decision_counts": dict(
                sorted(Counter(item.decision.value for item in reviews).items())
            ),
            "review_count": len(reviews),
            "reviewed_result_count": len(grouped),
        }
    )
    return 0


def handle_paired_evaluation_review_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "record-paired-evaluation-review": _record,
        "show-paired-evaluation-review": _show,
        "show-paired-evaluation-review-history": _history,
        "paired-evaluation-review-summary": _summary,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
