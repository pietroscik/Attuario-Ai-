"""High level orchestration for the evaluation workflow."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Literal, Optional

from .crawler import Crawler
from .extraction import PageMetrics, extract_metrics
from .parser import PageParser, ParsedPage
from .scoring import PageScore, ScoreWeights, score_page

ScoringMode = Literal["heuristic", "ml", "hybrid"]


@dataclass
class EvaluationResult:
    """Results from evaluating a single page.

    Attributes:
        page: ParsedPage object containing the page content and metadata.
        metrics: PageMetrics object containing extracted features.
        score: PageScore object containing the quality assessment.
    """

    page: ParsedPage
    metrics: PageMetrics
    score: PageScore


class EvaluationPipeline:
    """End-to-end pipeline that crawls, parses and scores pages.

    This pipeline orchestrates the entire evaluation workflow by:
    1. Crawling pages from a domain
    2. Parsing HTML into structured content
    3. Extracting relevant metrics
    4. Calculating quality scores
    5. Generating reports in various formats

    Attributes:
        base_url: The starting URL for crawling.
        crawler: Crawler instance for fetching pages.
        parser: PageParser instance for parsing HTML.
        weights: ScoreWeights for calculating composite scores.
        mode: Scoring mode (heuristic, ml, or hybrid).
        ml_predictor: MLPredictor instance for ML-based scoring (if mode is ml or hybrid).
    """

    def __init__(
        self,
        base_url: str,
        *,
        max_pages: int = 25,
        max_depth: int = 1,
        delay_seconds: float = 0.2,
        weights: Optional[ScoreWeights] = None,
        mode: ScoringMode = "heuristic",
        model_dir: Optional[Path] = None,
    ) -> None:
        """Initialize the evaluation pipeline.

        Args:
            base_url: Starting URL for the crawl.
            max_pages: Maximum number of pages to crawl (default: 25).
            max_depth: Maximum link depth from start URL (default: 1).
            delay_seconds: Delay between requests in seconds (default: 0.2).
            weights: Optional custom ScoreWeights for scoring.
            mode: Scoring mode - 'heuristic', 'ml', or 'hybrid' (default: 'heuristic').
            model_dir: Directory containing trained ML model (required if mode is 'ml' or 'hybrid').
        """
        self.base_url = base_url
        self.crawler = Crawler(
            base_url,
            max_pages=max_pages,
            max_depth=max_depth,
            delay_seconds=delay_seconds,
        )
        self.parser = PageParser()
        self.weights = weights or ScoreWeights()
        self.mode = mode
        self.ml_predictor = None

        if mode in ("ml", "hybrid"):
            try:
                from ml.predictor import MLPredictor

                self.ml_predictor = MLPredictor(model_dir=model_dir)
            except ImportError:
                raise ImportError("ML module not found. Ensure ml/ package is in the Python path.")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize ML predictor: {e}")

    def run(self, seeds: Optional[Iterable[str]] = None) -> List[EvaluationResult]:
        """Run the complete evaluation pipeline.

        Args:
            seeds: Optional list of seed URLs to start from. If None, uses base_url.

        Returns:
            List of EvaluationResult objects for each successfully evaluated page.
        """
        results: List[EvaluationResult] = []
        for crawled in self.crawler.crawl(seeds=seeds):
            if crawled.error or not crawled.html:
                continue
            parsed = self.parser.parse(crawled.url, crawled.html, crawled.fetched_at)
            metrics = extract_metrics(parsed.text, parsed.html)
            metadata = {**parsed.metadata, "url": parsed.url}

            # Score based on mode
            if self.mode == "heuristic":
                score = score_page(metrics, metadata, self.weights)
            elif self.mode == "ml":
                score = self.ml_predictor.score_page(parsed.text, metrics, metadata)
            elif self.mode == "hybrid":
                # Hybrid: average of heuristic and ML scores
                heuristic_score = score_page(metrics, metadata, self.weights)
                ml_score = self.ml_predictor.score_page(parsed.text, metrics, metadata)
                composite = (heuristic_score.composite + ml_score.composite) / 2
                # Merge components
                components = heuristic_score.components.copy()
                components["ml_score"] = ml_score.composite
                # Re-classify based on hybrid score
                if composite >= 85:
                    classification = "Eccellente"
                elif composite >= 70:
                    classification = "Buono"
                elif composite >= 50:
                    classification = "Discreto"
                else:
                    classification = "Criticità"
                score = PageScore(
                    url=metadata.get("url", ""),
                    composite=round(composite, 2),
                    components={k: round(v, 2) for k, v in components.items()},
                    classification=classification,
                )
            else:
                raise ValueError(f"Invalid scoring mode: {self.mode}")

            results.append(EvaluationResult(page=parsed, metrics=metrics, score=score))
        return results

    def export_csv(self, results: Iterable[EvaluationResult], path: Path) -> None:
        """Export evaluation results to a CSV file.

        Args:
            results: Iterable of EvaluationResult objects to export.
            path: Path where the CSV file should be written.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "url",
                    "title",
                    "score",
                    "classification",
                    "accuracy",
                    "transparency",
                    "completeness",
                    "freshness",
                    "clarity",
                    "word_count",
                    "numeric_tokens",
                    "has_formula",
                    "has_table",
                    "has_list",
                    "citation_matches",
                    "actuarial_terms",
                ],
            )
            writer.writeheader()
            for result in results:
                row = {
                    "url": result.page.url,
                    "title": result.page.title,
                    "score": result.score.composite,
                    "classification": result.score.classification,
                    "accuracy": result.score.components["accuracy"],
                    "transparency": result.score.components["transparency"],
                    "completeness": result.score.components["completeness"],
                    "freshness": result.score.components["freshness"],
                    "clarity": result.score.components["clarity"],
                    "word_count": result.metrics.word_count,
                    "numeric_tokens": result.metrics.numeric_tokens,
                    "has_formula": result.metrics.has_formula,
                    "has_table": result.metrics.has_table,
                    "has_list": result.metrics.has_list,
                    "citation_matches": result.metrics.citation_matches,
                    "actuarial_terms": "; ".join(
                        f"{term}:{count}"
                        for term, count in sorted(result.metrics.actuarial_terms.items())
                    ),
                }
                writer.writerow(row)

    def export_json(self, results: Iterable[EvaluationResult], path: Path) -> None:
        """Export evaluation results to a JSON file.

        Args:
            results: Iterable of EvaluationResult objects to export.
            path: Path where the JSON file should be written.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        serializable = [
            {
                "page": {
                    "url": result.page.url,
                    "title": result.page.title,
                    "metadata": result.page.metadata,
                    "fetched_at": result.page.fetched_at.isoformat(),
                },
                "metrics": result.metrics.to_dict(),
                "score": asdict(result.score),
            }
            for result in results
        ]
        path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")

    def summary(self, results: Iterable[EvaluationResult]) -> dict:
        """Generate summary statistics from evaluation results.

        Args:
            results: Iterable of EvaluationResult objects.

        Returns:
            Dictionary containing count, average, minimum, and maximum scores.
        """
        scores = [result.score.composite for result in results]
        if not scores:
            return {
                "count": 0,
                "average": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
            }
        return {
            "count": len(scores),
            "average": round(sum(scores) / len(scores), 2),
            "minimum": round(min(scores), 2),
            "maximum": round(max(scores), 2),
        }

    def close(self) -> None:
        """Close the crawler and release resources."""
        self.crawler.close()

    def __enter__(self) -> "EvaluationPipeline":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
