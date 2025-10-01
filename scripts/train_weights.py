#!/usr/bin/env python3
"""CLI per apprendere i pesi di scoring a partire da revisioni manuali."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from attuario_ai import EvaluationPipeline
from attuario_ai.learning import WeightLearner, normalize_url, samples_from_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Learn score weights from labelled pages."
    )
    parser.add_argument(
        "base_url", help="Base domain for crawling (e.g. https://www.attuario.eu)"
    )
    parser.add_argument(
        "labels", type=Path, help="JSON file with [{'url': str, 'target_score': float}]"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Override max pages for evaluation (defaults to number of labels)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between requests while collecting training data",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("weights.json"),
        help="Destination file for the learned weights",
    )
    return parser.parse_args()


def load_targets(path: Path) -> Tuple[Dict[str, float], List[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Labels file must contain a list of entries")
    targets: Dict[str, float] = {}
    seeds: List[str] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        url = entry.get("url")
        score = entry.get("target_score")
        if not url or score is None:
            continue
        normalized = normalize_url(str(url))
        targets[normalized] = float(score)
        seeds.append(str(url))
    if not targets:
        raise ValueError("No valid labelled entries were found")
    return targets, seeds


def main() -> None:
    args = parse_args()
    targets, seeds = load_targets(args.labels)
    max_pages = args.max_pages or len(targets)

    with EvaluationPipeline(
        args.base_url,
        max_pages=max_pages,
        max_depth=0,
        delay_seconds=args.delay,
    ) as pipeline:
        results = pipeline.run(seeds=seeds)

    samples = samples_from_results(results, targets)
    if not samples:
        raise ValueError("Unable to match any crawled pages with provided labels")

    learner = WeightLearner()
    weights = learner.fit(samples)
    evaluation = learner.evaluate(samples, weights)

    args.output.write_text(
        json.dumps(weights.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    report = {
        "weights": weights.to_dict(),
        "evaluation": evaluation,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
