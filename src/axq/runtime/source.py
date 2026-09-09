"""Deterministically ordered runtime-event sources."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Protocol

from axq.runtime.events import RuntimeEvent


class EventSource(Protocol):
    """Source of events already ordered for causal reduction."""

    def events(self) -> Iterator[RuntimeEvent]:
        """Yield events in canonical availability order."""


class InMemoryEventSource:
    """Small deterministic source used by replay and contract tests."""

    def __init__(self, events: Iterable[RuntimeEvent]) -> None:
        self._events = tuple(sorted(events, key=lambda event: event.ordering_key))

    def events(self) -> Iterator[RuntimeEvent]:
        return iter(self._events)
