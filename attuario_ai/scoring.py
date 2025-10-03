"""Heuristic scoring for actuarial content quality."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, Mapping

from .extraction import PageMetrics


@dataclass
class ScoreWeights:
    """Configurable weights for the composite scoring system.

    These weights determine how much each component contributes to the
    final composite score. The weights are normalized to sum to 1.0.

    Attributes:
        accuracy: Weight for numerical accuracy component (default: 0.4).
        transparency: Weight for citation transparency component (default: 0.2).
        completeness: Weight for content completeness component (default: 0.2).
        freshness: Weight for content freshness component (default: 0.1).
        clarity: Weight for content clarity component (default: 0.1).
    """

    accuracy: float = 0.4
    transparency: float = 0.2
    completeness: float = 0.2
    freshness: float = 0.1
    clarity: float = 0.1

    def normalize(self) -> "ScoreWeights":
        """Normalize weights to sum to 1.0.

        Returns:
            New ScoreWeights instance with normalized values.

        Raises:
            ValueError: If all weights sum to zero.
        """
        total = (
            self.accuracy + self.transparency + self.completeness + self.freshness + self.clarity
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
        """Convert weights to a dictionary.

        Returns:
            Dictionary mapping component names to their weight values.
        """
        return {
            "accuracy": self.accuracy,
            "transparency": self.transparency,
            "completeness": self.completeness,
            "freshness": self.freshness,
            "clarity": self.clarity,
        }

    @classmethod
    def from_dict(cls, values: Mapping[str, float]) -> "ScoreWeights":
        """Create ScoreWeights from a dictionary.

        Args:
            values: Dictionary mapping component names to weight values.

        Returns:
            New ScoreWeights instance with the specified values.
        """
        return cls(
            accuracy=float(values.get("accuracy", cls.accuracy)),
            transparency=float(values.get("transparency", cls.transparency)),
            completeness=float(values.get("completeness", cls.completeness)),
            freshness=float(values.get("freshness", cls.freshness)),
            clarity=float(values.get("clarity", cls.clarity)),
        )


@dataclass
class PageScore:
    """Scoring result for a single page.

    Attributes:
        url: The URL of the scored page.
        composite: Overall composite score (0-100).
        components: Dictionary mapping component names to their individual scores.
        classification: Quality classification based on composite score.
    """

    url: str
    composite: float
    components: Dict[str, float]
    classification: str


FRESHNESS_DECAY_DAYS = 365


def score_page(metrics: PageMetrics, metadata: Dict[str, str], weights: ScoreWeights) -> PageScore:
    """Calculate a comprehensive quality score for a page.

    Computes individual component scores and combines them using the provided
    weights to produce a final composite score with quality classification.

    Args:
        metrics: PageMetrics object containing extracted page features.
        metadata: Dictionary containing page metadata (including URL).
        weights: ScoreWeights specifying how to combine component scores.

    Returns:
        PageScore object containing composite score, components, and classification.
    """
    components = compute_components(metrics, metadata)
    composite = apply_weights(components, weights)
    classification = _classify(composite)
    return PageScore(
        url=metadata.get("url", ""),
        composite=round(composite, 2),
        components={key: round(value, 2) for key, value in components.items()},
        classification=classification,
    )


def compute_components(metrics: PageMetrics, metadata: Dict[str, str]) -> Dict[str, float]:
    """Compute individual scoring components from metrics.

    Args:
        metrics: PageMetrics object containing extracted page features.
        metadata: Dictionary containing page metadata (dates, etc.).

    Returns:
        Dictionary mapping component names to their scores (0-100).
    """
    return {
        "accuracy": _score_accuracy(metrics),
        "transparency": _score_transparency(metrics),
        "completeness": _score_completeness(metrics),
        "freshness": _score_freshness(metadata.get("modified") or metadata.get("published")),
        "clarity": _score_clarity(metrics),
    }


def apply_weights(components: Dict[str, float], weights: ScoreWeights) -> float:
    """Combine component scores using normalized weights.

    Args:
        components: Dictionary mapping component names to their scores.
        weights: ScoreWeights specifying how to combine the components.

    Returns:
        Weighted composite score (0-100).
    """
    normalized = weights.normalize()
    return (
        components.get("accuracy", 0.0) * normalized.accuracy
        + components.get("transparency", 0.0) * normalized.transparency
        + components.get("completeness", 0.0) * normalized.completeness
        + components.get("freshness", 0.0) * normalized.freshness
        + components.get("clarity", 0.0) * normalized.clarity
    )


def _score_accuracy(metrics: PageMetrics) -> float:
    """Score the numerical accuracy aspect of the content.

    Based on the presence of numeric tokens and mathematical formulas.

    Args:
        metrics: PageMetrics object.

    Returns:
        Accuracy score (0-100).
    """
    if metrics.numeric_tokens == 0:
        return 40.0
    ratio = min(metrics.numeric_tokens / max(metrics.word_count, 1), 0.2)
    base = 60.0 + ratio * 200
    if metrics.has_formula:
        base += 10
    return min(base, 100.0)


def _score_transparency(metrics: PageMetrics) -> float:
    """Score the transparency aspect based on regulatory citations.

    Args:
        metrics: PageMetrics object.

    Returns:
        Transparency score (0-100).
    """
    if metrics.citation_matches == 0:
        return 30.0
    return min(30 + metrics.citation_matches * 15, 100.0)


def _score_completeness(metrics: PageMetrics) -> float:
    """Score the completeness based on structural elements and terminology.

    Args:
        metrics: PageMetrics object.

    Returns:
        Completeness score (0-100).
    """
    bonus = 0
    if metrics.has_table:
        bonus += 20
    if metrics.has_list:
        bonus += 10
    if metrics.actuarial_terms:
        bonus += min(len(metrics.actuarial_terms) * 5, 30)
    return min(40 + bonus, 100.0)


def _score_freshness(timestamp: str | None) -> float:
    """Score content freshness based on publication/modification date.

    Args:
        timestamp: ISO format timestamp string or None.

    Returns:
        Freshness score (0-100), higher for more recent content.
    """
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
    """Score content clarity based on text-to-numbers ratio.

    Args:
        metrics: PageMetrics object.

    Returns:
        Clarity score (0-100).
    """
    if metrics.word_count == 0:
        return 40.0
    avg_numbers = metrics.numeric_tokens / metrics.word_count
    if avg_numbers > 0.15:
        return 65.0
    return 80.0


def _classify(score: float) -> str:
    """Classify a score into a quality category.

    Args:
        score: Composite score (0-100).

    Returns:
        Quality classification string in Italian.
    """
    if score >= 85:
        return "Eccellente"
    if score >= 70:
        return "Buono"
    if score >= 50:
        return "Discreto"
    return "Criticità"
