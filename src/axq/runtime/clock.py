"""UTC clocks shared by live processing and deterministic replay."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


def ensure_utc(value: datetime) -> datetime:
    """Reject naive timestamps and return a normalized UTC timestamp."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


class RuntimeClock(Protocol):
    """Clock contract used outside the pure reducer."""

    def now(self) -> datetime:
        """Return the current instant in UTC."""


class SystemUTCClock:
    """Live clock backed by the host system clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class ReplayClock:
    """Explicitly advanced deterministic replay clock."""

    def __init__(self, initial_time: datetime) -> None:
        self._current = ensure_utc(initial_time)

    def now(self) -> datetime:
        return self._current

    def advance_to(self, value: datetime) -> None:
        next_time = ensure_utc(value)
        if next_time < self._current:
            raise ValueError("replay clock cannot move backwards")
        self._current = next_time
