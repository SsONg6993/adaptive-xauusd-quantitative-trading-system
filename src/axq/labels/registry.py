from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from axq.labels.base import LabelDefinition, LabelKind
from axq.labels.direction import direction_labels
from axq.labels.manifest import LabelManifest
from axq.labels.returns import forward_return_labels
from axq.labels.triple_barrier import triple_barrier_labels


@dataclass(frozen=True)
class LabelResult:
    frame: pd.DataFrame
    manifest: LabelManifest


def generate_labels(
    frame: pd.DataFrame,
    definition: LabelDefinition,
    *,
    lower_timeframe: pd.DataFrame | None = None,
) -> LabelResult:
    missing = set(definition.required_source_columns) - set(frame.columns)
    if missing:
        raise ValueError(f"Label {definition.name} missing columns: {sorted(missing)}")
    if definition.kind == LabelKind.DIRECTION:
        output = direction_labels(frame, definition)
    elif definition.kind in {LabelKind.FORWARD_RETURN, LabelKind.ATR_ADJUSTED_RETURN}:
        output = forward_return_labels(frame, definition)
    else:
        output = triple_barrier_labels(
            frame, definition, lower_timeframe=lower_timeframe
        )
    targets = [str(column) for column in output if str(column).startswith("target_")]
    metadata = [str(column) for column in output if str(column).startswith("label_")]
    if len(targets) != 1:
        raise ValueError("Each label definition must emit exactly one target column")
    manifest = LabelManifest(
        definition=definition,
        target_columns=targets,
        metadata_columns=metadata,
    )
    return LabelResult(output, manifest)
