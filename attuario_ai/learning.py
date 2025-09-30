"""Utilities to learn scoring weights from human feedback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np

from .scoring import ScoreWeights, apply_weights, compute_components


COMPONENT_KEYS = ("accuracy", "transparency", "completeness", "freshness", "clarity")


@dataclass
class TrainingSample:
    """Represents a manually reviewed page used to calibrate weights."""

    url: str
    components: Dict[str, float]
    target_score: float


class WeightLearner:
    """Fit ``ScoreWeights`` using least squares on feedback samples."""

    def __init__(self, *, min_samples: int = 2) -> None:
        self.min_samples = min_samples

    def fit(self, samples: Sequence[TrainingSample]) -> ScoreWeights:
        if len(samples) < self.min_samples:
            raise ValueError(f"At least {self.min_samples} samples are required to fit weights")

        matrix = np.array([[sample.components.get(key, 0.0) for key in COMPONENT_KEYS] for sample in samples], dtype=float)
        targets = np.array([sample.target_score for sample in samples], dtype=float)

        solution, *_ = np.linalg.lstsq(matrix, targets, rcond=None)
        solution = np.clip(solution, 0.0, None)

        if not solution.any():
            return ScoreWeights()

        total = solution.sum()
        if total <= 0:
            return ScoreWeights()

        normalized = solution / total
        return ScoreWeights(
            accuracy=float(normalized[0]),
            transparency=float(normalized[1]),
            completeness=float(normalized[2]),
            freshness=float(normalized[3]),
            clarity=float(normalized[4]),
        )

    def evaluate(self, samples: Sequence[TrainingSample], weights: ScoreWeights) -> Dict[str, float]:
        predictions = [apply_weights(sample.components, weights) for sample in samples]
        errors = [prediction - sample.target_score for prediction, sample in zip(predictions, samples)]
        absolute_errors = [abs(error) for error in errors]
        if not errors:
            return {"count": 0, "mae": 0.0, "mse": 0.0}
        mae = sum(absolute_errors) / len(absolute_errors)
        mse = sum(error ** 2 for error in errors) / len(errors)
        return {"count": len(errors), "mae": round(mae, 2), "mse": round(mse, 2)}


def samples_from_results(
    results: Iterable["EvaluationResult"],
    targets: Mapping[str, float],
) -> List[TrainingSample]:
    from .pipeline import EvaluationResult  # Local import to avoid circular dependency

    lookup = {normalize_url(url): score for url, score in targets.items()}
    samples: List[TrainingSample] = []
    for result in results:
        if not isinstance(result, EvaluationResult):
            continue
        normalized_url = normalize_url(result.page.url)
        if normalized_url not in lookup:
            continue
        metadata = dict(result.page.metadata)
        metadata["url"] = result.page.url
        components = {key: float(value) for key, value in compute_components(result.metrics, metadata).items()}
        samples.append(
            TrainingSample(
                url=result.page.url,
                components=components,
                target_score=float(lookup[normalized_url]),
            )
        )
    return samples


def normalize_url(url: str) -> str:
    return url.rstrip("/")
