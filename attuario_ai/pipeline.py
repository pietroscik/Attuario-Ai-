"""High level orchestration for the evaluation workflow."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .crawler import Crawler
from .extraction import PageMetrics, extract_metrics
from .parser import PageParser, ParsedPage
from .scoring import PageScore, ScoreWeights, score_page


@dataclass
class EvaluationResult:
    page: ParsedPage
    metrics: PageMetrics
    score: PageScore


class EvaluationPipeline:
    """End-to-end pipeline that crawls, parses and scores pages."""

    def __init__(
        self,
        base_url: str,
        *,
        max_pages: int = 25,
        max_depth: int = 1,
        delay_seconds: float = 0.2,
        weights: Optional[ScoreWeights] = None,
    ) -> None:
        self.base_url = base_url
        self.crawler = Crawler(
            base_url,
            max_pages=max_pages,
            max_depth=max_depth,
            delay_seconds=delay_seconds,
        )
        self.parser = PageParser()
        self.weights = weights or ScoreWeights()

    def run(self, seeds: Optional[Iterable[str]] = None) -> List[EvaluationResult]:
        results: List[EvaluationResult] = []
        for crawled in self.crawler.crawl(seeds=seeds):
            if crawled.error or not crawled.html:
                continue
            parsed = self.parser.parse(crawled.url, crawled.html, crawled.fetched_at)
            metrics = extract_metrics(parsed.text, parsed.html)
            metadata = {**parsed.metadata, "url": parsed.url}
            score = score_page(metrics, metadata, self.weights)
            results.append(EvaluationResult(page=parsed, metrics=metrics, score=score))
        return results

    def export_csv(self, results: Iterable[EvaluationResult], path: Path) -> None:
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
                        for term, count in sorted(
                            result.metrics.actuarial_terms.items()
                        )
                    ),
                }
                writer.writerow(row)

    def export_json(self, results: Iterable[EvaluationResult], path: Path) -> None:
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
        path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def summary(self, results: Iterable[EvaluationResult]) -> dict:
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
        self.crawler.close()

    def __enter__(self) -> "EvaluationPipeline":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
