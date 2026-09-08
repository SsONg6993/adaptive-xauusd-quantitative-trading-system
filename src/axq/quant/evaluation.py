"""Reproduce frozen split metrics without fitting or retraining."""

from __future__ import annotations

from typing import Any, Literal

from axq.quant.dataset import load_training_dataset
from axq.quant.inference import QuantAgent
from axq.quant.metrics import evaluate_predictions


def evaluate_saved_run(
    run_dir: str,
    dataset_dir: str,
    *,
    split: Literal["train", "validation", "oos"] = "oos",
) -> dict[str, Any]:
    agent = QuantAgent(run_dir)
    dataset = load_training_dataset(dataset_dir)
    if dataset.manifest.dataset_id != agent.manifest.dataset_id:
        raise ValueError("Evaluation dataset does not match model manifest")
    frames = dict(zip(("train", "validation", "oos"), dataset.split_frames(), strict=True))
    frame = frames[split]
    probability = agent.calibration.transform(
        agent.model.predict_proba(agent.preprocessing.transform(frame))
    )
    return evaluate_predictions(
        frame[agent.manifest.target_column],
        probability,
        agent.model.classes_,
        minimum_confidence=agent.minimum_confidence,
        explicit_neutral_class=agent.explicit_neutral_class,
        metadata=frame[dataset.manifest.label_metadata_columns].reset_index(drop=True),
    )
