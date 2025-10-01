"""Convenient re-exports for the :mod:`attuario_ai` package."""

from __future__ import annotations

from .crawler import CrawlResult, Crawler
from .extraction import PageMetrics, extract_metrics
from .parser import PageParser, ParsedPage
from .pipeline import EvaluationPipeline, EvaluationResult as PipelineEvaluationResult
from .scoring import (
    PageScore,
    ScoreWeights,
    apply_weights,
    compute_components,
    score_page,
)
from .learning import Learner, EvaluationResult as LearningEvaluationResult

__all__ = [
    "CrawlResult",
    "Crawler",
    "PageMetrics",
    "extract_metrics",
    "PageParser",
    "ParsedPage",
    "EvaluationPipeline",
    "PipelineEvaluationResult",
    "PageScore",
    "ScoreWeights",
    "apply_weights",
    "compute_components",
    "score_page",
    "Learner",
    "LearningEvaluationResult",
]
