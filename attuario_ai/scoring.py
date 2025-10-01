"""Heuristic scoring for actuarial content quality."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, Mapping

from .extraction import PageMetrics


@dataclass
class ScoreWeights:
    accuracy: float = 0.4
    transparency: float = 0.2
    completeness: float = 0.2
    freshness: float = 0.1
    clarity: float = 0.1

    def normalize(self) -> "ScoreWeights":
        total = (
            self.accuracy
            + self.transparency
            + self.completeness
            + self.freshness
            + self.clarity
        )
        if not total:
            raise ValueError("Weights sum to zero")
        return ScoreWeights(
            accuracy=self.accuracy / total,
            transparency=self.transparency / total,
            completeness=self.completeness / total,
            freshness=self.freshness / total,
            clarity=self.clarity / total,
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "accuracy": self.accuracy,
            "transparency": self.transparency,
            "completeness": self.completeness,
            "freshness": self.freshness,
            "clarity": self.clarity,
        }

    @classmethod
    def from_dict(cls, values: Mapping[str, float]) -> "ScoreWeights":
        return cls(
            accuracy=float(values.get("accuracy", cls.accuracy)),
            transparency=float(values.get("transparency", cls.transparency)),
            completeness=float(values.get("completeness", cls.completeness)),
            freshness=float(values.get("freshness", cls.freshness)),
            clarity=float(values.get("clarity", cls.clarity)),
        )


@dataclass
class PageScore:
    url: str
    composite: float
    components: Dict[str, float]
    classification: str


FRESHNESS_DECAY_DAYS = 365


def score_page(
    metrics: PageMetrics, metadata: Dict[str, str], weights: ScoreWeights
) -> PageScore:
    components = compute_components(metrics, metadata)
    composite = apply_weights(components, weights)
    classification = _classify(composite)
    return PageScore(
        url=metadata.get("url", ""),
        composite=round(composite, 2),
        components={key: round(value, 2) for key, value in components.items()},
        classification=classification,
    )


def compute_components(
    metrics: PageMetrics, metadata: Dict[str, str]
) -> Dict[str, float]:
    return {
        "accuracy": _score_accuracy(metrics),
        "transparency": _score_transparency(metrics),
        "completeness": _score_completeness(metrics),
        "freshness": _score_freshness(
            metadata.get("modified") or metadata.get("published")
        ),
        "clarity": _score_clarity(metrics),
    }


def apply_weights(components: Dict[str, float], weights: ScoreWeights) -> float:
    normalized = weights.normalize()
    return (
        components.get("accuracy", 0.0) * normalized.accuracy
        + components.get("transparency", 0.0) * normalized.transparency
        + components.get("completeness", 0.0) * normalized.completeness
        + components.get("freshness", 0.0) * normalized.freshness
        + components.get("clarity", 0.0) * normalized.clarity
    )


def _score_accuracy(metrics: PageMetrics) -> float:
    if metrics.numeric_tokens == 0:
        return 40.0
    ratio = min(metrics.numeric_tokens / max(metrics.word_count, 1), 0.2)
    base = 60.0 + ratio * 200
    if metrics.has_formula:
        base += 10
    return min(base, 100.0)


def _score_transparency(metrics: PageMetrics) -> float:
    if metrics.citation_matches == 0:
        return 30.0
    return min(30 + metrics.citation_matches * 15, 100.0)


def _score_completeness(metrics: PageMetrics) -> float:
    bonus = 0
    if metrics.has_table:
        bonus += 20
    if metrics.has_list:
        bonus += 10
    if metrics.actuarial_terms:
        bonus += min(len(metrics.actuarial_terms) * 5, 30)
    return min(40 + bonus, 100.0)


def _score_freshness(timestamp: str | None) -> float:
    if not timestamp:
        return 50.0
    try:
        parsed = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return 60.0
    now = dt.datetime.now(dt.timezone.utc)
    delta = now - parsed
    if delta.days < 0:
        return 80.0
    decay = min(delta.days / FRESHNESS_DECAY_DAYS, 1.0)
    return max(20.0, 100.0 * (1 - decay))


def _score_clarity(metrics: PageMetrics) -> float:
    if metrics.word_count == 0:
        return 40.0
    avg_numbers = metrics.numeric_tokens / metrics.word_count
    if avg_numbers > 0.15:
        return 65.0
    return 80.0


def _classify(score: float) -> str:
    if score >= 85:
        return "Eccellente"
    if score >= 70:
        return "Buono"
    if score >= 50:
        return "Discreto"
    return "Criticità"
