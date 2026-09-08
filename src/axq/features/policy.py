"""Feature availability and missing-value policy contracts."""

from __future__ import annotations

from enum import StrEnum


class MissingValueReason(StrEnum):
    MATHEMATICALLY_UNAVAILABLE = "mathematically_unavailable"
    INSUFFICIENT_HISTORY = "insufficient_history"
    MISSING_MARKET_DATA = "missing_market_data"
    MISSING_BROKER_DATA = "missing_broker_data"
    OPTIONAL_UNAVAILABLE = "optional_unavailable"


MISSING_VALUE_POLICY: dict[MissingValueReason, str] = {
    MissingValueReason.MATHEMATICALLY_UNAVAILABLE: "retain NaN; never coerce division by zero",
    MissingValueReason.INSUFFICIENT_HISTORY: "retain NaN until the declared valid-from row",
    MissingValueReason.MISSING_MARKET_DATA: (
        "retain NaN and report timestamp gap; do not impute OHLC"
    ),
    MissingValueReason.MISSING_BROKER_DATA: "retain NaN and report source column/provider",
    MissingValueReason.OPTIONAL_UNAVAILABLE: (
        "retain NaN or disable the feature explicitly in manifest"
    ),
}
