"""Validation-only probability calibration without OOS access."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]


@dataclass
class ProbabilityCalibrator:
    method: str
    classes: np.ndarray
    sigmoid: LogisticRegression | None = None
    isotonic: list[IsotonicRegression] | None = None
    fit_row_count: int = 0

    @classmethod
    def fit(
        cls, method: str, probabilities: np.ndarray, target: np.ndarray, classes: np.ndarray
    ) -> ProbabilityCalibrator:
        result = cls(method=method, classes=np.asarray(classes), fit_row_count=len(target))
        if method == "none":
            return result
        if len(np.unique(target)) < 2:
            raise ValueError("Calibration requires at least two validation classes")
        clipped = np.clip(probabilities, 1e-12, 1.0)
        if method == "sigmoid":
            result.sigmoid = LogisticRegression(max_iter=300).fit(np.log(clipped), target)
        elif method == "isotonic":
            result.isotonic = []
            for index, label in enumerate(classes):
                model = IsotonicRegression(out_of_bounds="clip")
                model.fit(clipped[:, index], (target == label).astype(float))
                result.isotonic.append(model)
        else:
            raise ValueError(f"Unsupported calibration method: {method}")
        return result

    def transform(self, probabilities: np.ndarray) -> np.ndarray:
        clipped = np.clip(np.asarray(probabilities, dtype=float), 1e-12, 1.0)
        if self.method == "none":
            output = clipped
        elif self.method == "sigmoid" and self.sigmoid is not None:
            partial = self.sigmoid.predict_proba(np.log(clipped))
            output = np.zeros_like(clipped)
            for source, label in enumerate(self.sigmoid.classes_):
                matches = np.flatnonzero(self.classes == label)
                if len(matches):
                    output[:, matches[0]] = partial[:, source]
        elif self.method == "isotonic" and self.isotonic is not None:
            output = np.column_stack(
                [model.predict(clipped[:, i]) for i, model in enumerate(self.isotonic)]
            )
        else:
            raise RuntimeError("Calibration artifact is incomplete")
        totals = output.sum(axis=1, keepdims=True)
        if np.any(totals <= 0):
            raise ValueError("Calibrator produced invalid probabilities")
        return np.asarray(output / totals, dtype=float)
