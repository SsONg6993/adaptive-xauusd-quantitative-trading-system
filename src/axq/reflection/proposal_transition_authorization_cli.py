"""CLI handlers for governed proposal-transition authorization."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from axq.reflection.proposal_transition_authorization_contracts import (
    ProposalTransitionAuthorization,
)
from axq.reflection.proposal_transition_authorization_store import (
    SQLiteProposalTransitionAuthorizationStore,
)


def register_proposal_transition_authorization_commands(commands: Any) -> None:
    record = commands.add_parser("record-proposal-transition-authorization")
    record.add_argument("--store", type=Path, required=True)
    record.add_argument("--authorization", type=Path, required=True)

    show = commands.add_parser("show-proposal-transition-authorization")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--authorization-id", required=True)

    history = commands.add_parser("show-proposal-transition-authorization-history")
    history.add_argument("--store", type=Path, required=True)
    history.add_argument("--proposal-id", required=True)

    summary = commands.add_parser("proposal-transition-authorization-summary")
    summary.add_argument("--store", type=Path, required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _record(args: argparse.Namespace) -> int:
    authorization = ProposalTransitionAuthorization.model_validate_json(
        args.authorization.read_bytes()
    )
    store = SQLiteProposalTransitionAuthorizationStore(args.store)
    appended = store.append(authorization)
    store.sync()
    _emit(
        {
            "appended": appended,
            "authorization_id": authorization.authorization_id,
        }
    )
    return 0


def _show(args: argparse.Namespace) -> int:
    authorization = SQLiteProposalTransitionAuthorizationStore(args.store).authorization(
        args.authorization_id
    )
    if authorization is None:
        raise SystemExit("proposal transition authorization not found")
    _emit(authorization.model_dump(mode="json"))
    return 0


def _history(args: argparse.Namespace) -> int:
    history = SQLiteProposalTransitionAuthorizationStore(args.store).history(args.proposal_id)
    _emit(
        {
            "authorization_ids": [item.authorization_id for item in history],
            "authorizations": [item.model_dump(mode="json") for item in history],
            "current_authorization_id": (None if not history else history[-1].authorization_id),
            "proposal_id": args.proposal_id,
        }
    )
    return 0


def _transition_key(authorization: ProposalTransitionAuthorization) -> str:
    return f"{authorization.from_status.value}->{authorization.to_status.value}"


def _summary(args: argparse.Namespace) -> int:
    store = SQLiteProposalTransitionAuthorizationStore(args.store)
    authorizations = store.authorizations()
    proposal_ids = sorted({item.proposal_id for item in authorizations})
    current = tuple(
        authorization
        for proposal_id in proposal_ids
        if (authorization := store.current(proposal_id)) is not None
    )
    _emit(
        {
            "authorization_count": len(authorizations),
            "authorized_proposal_count": len(proposal_ids),
            "current_transition_counts": dict(
                sorted(Counter(_transition_key(item) for item in current).items())
            ),
            "transition_counts": dict(
                sorted(Counter(_transition_key(item) for item in authorizations).items())
            ),
        }
    )
    return 0


def handle_proposal_transition_authorization_command(
    args: argparse.Namespace,
) -> int | None:
    handlers = {
        "record-proposal-transition-authorization": _record,
        "show-proposal-transition-authorization": _show,
        "show-proposal-transition-authorization-history": _history,
        "proposal-transition-authorization-summary": _summary,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
