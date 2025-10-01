"""Attuario AI content quality assessment toolkit."""

from .crawler import Crawler, CrawlResult
from .parser import PageParser, ParsedPage
from .extraction import extract_metrics
from .scoring import (
    ScoreWeights,
    score_page,
    PageScore,
    compute_components,
    apply_weights,
)
from .pipeline import EvaluationPipeline
from .learning import TrainingSample, WeightLearner, samples_from_results

__all__ = [
    "Crawler",
    "CrawlResult",
    "PageParser",
    "ParsedPage",
    "extract_metrics",
    "ScoreWeights",
    "score_page",
    "PageScore",
    "compute_components",
    "apply_weights",
    "EvaluationPipeline",
    "TrainingSample",
    "WeightLearner",
    "samples_from_results",
]
