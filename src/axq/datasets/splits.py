"""Deterministic chronological, purged, embargoed split definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from axq.versioning import canonical_hash


class IndexRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    start: int = Field(ge=0)
    stop: int = Field(ge=0)

    @property
    def size(self) -> int:
        return max(0, self.stop - self.start)


class SplitFold(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    fold: int
    train: IndexRange
    validation: IndexRange
    oos: IndexRange
    purged_train_rows: int
    purged_validation_rows: int
    embargoed_validation_rows: int
    embargoed_oos_rows: int


class SplitManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    kind: str
    row_count: int
    label_horizon_bars: int
    purge_bars: int
    embargo_bars: int
    policy: dict[str, Any]
    folds: list[SplitFold]

    @property
    def manifest_id(self) -> str:
        return f"sm-{canonical_hash(self.model_dump(mode='json'))[:16]}"

    def write(self, path: str | Path) -> None:
        target = Path(path)
        target.write_text(
            json.dumps(
                self.model_dump(mode="json") | {"manifest_id": self.manifest_id},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )


def chronological_split(
    row_count: int,
    *,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
    label_horizon_bars: int,
    purge_bars: int = 0,
    embargo_bars: int = 0,
) -> SplitManifest:
    if row_count < 3:
        raise ValueError("At least three rows are required")
    if not 0.0 < train_fraction < 1.0 or not 0.0 < validation_fraction < 1.0:
        raise ValueError("Split fractions must be between zero and one")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("Train plus validation fraction must be below one")
    train_boundary = int(row_count * train_fraction)
    validation_boundary = int(row_count * (train_fraction + validation_fraction))
    effective_purge = max(purge_bars, label_horizon_bars)
    fold = SplitFold(
        fold=0,
        train=IndexRange(start=0, stop=max(0, train_boundary - effective_purge)),
        validation=IndexRange(
            start=min(row_count, train_boundary + embargo_bars),
            stop=max(train_boundary + embargo_bars, validation_boundary - effective_purge),
        ),
        oos=IndexRange(
            start=min(row_count, validation_boundary + embargo_bars),
            stop=row_count,
        ),
        purged_train_rows=min(effective_purge, train_boundary),
        purged_validation_rows=min(effective_purge, validation_boundary - train_boundary),
        embargoed_validation_rows=min(embargo_bars, validation_boundary - train_boundary),
        embargoed_oos_rows=min(embargo_bars, row_count - validation_boundary),
    )
    if min(fold.train.size, fold.validation.size, fold.oos.size) <= 0:
        raise ValueError("Purge/embargo leaves an empty split")
    return SplitManifest(
        kind="chronological",
        row_count=row_count,
        label_horizon_bars=label_horizon_bars,
        purge_bars=effective_purge,
        embargo_bars=embargo_bars,
        policy={
            "train_fraction": train_fraction,
            "validation_fraction": validation_fraction,
            "oos_fraction": 1.0 - train_fraction - validation_fraction,
        },
        folds=[fold],
    )


def walk_forward_splits(
    row_count: int,
    *,
    mode: Literal["expanding", "rolling"],
    train_length: int,
    validation_length: int,
    oos_length: int,
    step_size: int,
    label_horizon_bars: int,
    purge_bars: int = 0,
    embargo_bars: int = 0,
) -> SplitManifest:
    values = (train_length, validation_length, oos_length, step_size, label_horizon_bars)
    if any(value <= 0 for value in values):
        raise ValueError("Window lengths, step, and horizon must be positive")
    effective_purge = max(purge_bars, label_horizon_bars)
    folds: list[SplitFold] = []
    train_stop = train_length
    fold_number = 0
    while train_stop + validation_length + oos_length <= row_count:
        train_start = 0 if mode == "expanding" else train_stop - train_length
        validation_start = train_stop
        validation_stop = validation_start + validation_length
        oos_start = validation_stop
        folds.append(
            SplitFold(
                fold=fold_number,
                train=IndexRange(
                    start=train_start, stop=max(train_start, train_stop - effective_purge)
                ),
                validation=IndexRange(
                    start=validation_start + embargo_bars,
                    stop=max(
                        validation_start + embargo_bars,
                        validation_stop - effective_purge,
                    ),
                ),
                oos=IndexRange(
                    start=oos_start + embargo_bars, stop=oos_start + oos_length
                ),
                purged_train_rows=effective_purge,
                purged_validation_rows=effective_purge,
                embargoed_validation_rows=embargo_bars,
                embargoed_oos_rows=embargo_bars,
            )
        )
        train_stop += step_size
        fold_number += 1
    if not folds or any(
        min(fold.train.size, fold.validation.size, fold.oos.size) <= 0 for fold in folds
    ):
        raise ValueError("No non-empty walk-forward fold fits the policy")
    return SplitManifest(
        kind=f"walk_forward_{mode}",
        row_count=row_count,
        label_horizon_bars=label_horizon_bars,
        purge_bars=effective_purge,
        embargo_bars=embargo_bars,
        policy={
            "mode": mode,
            "train_length": train_length,
            "validation_length": validation_length,
            "oos_length": oos_length,
            "step_size": step_size,
        },
        folds=folds,
    )
