#!/usr/bin/env python3
"""Command line entry point for the Attuario AI evaluation pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from attuario_ai import EvaluationPipeline, ScoreWeights


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate actuarial content quality for a domain."
    )
    parser.add_argument(
        "base_url", help="Starting URL for the crawl (e.g. https://www.example.com)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=25, help="Maximum number of pages to crawl"
    )
    parser.add_argument("--max-depth", type=int, default=1, help="Maximum crawl depth")
    parser.add_argument(
        "--delay", type=float, default=0.2, help="Delay between requests in seconds"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for generated reports",
    )
    parser.add_argument(
        "--weights",
        type=Path,
        help="Optional JSON file containing custom score weights",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    weights = None
    if args.weights:
        weights_data = json.loads(args.weights.read_text(encoding="utf-8"))
        weights = ScoreWeights.from_dict(weights_data)

    with EvaluationPipeline(
        args.base_url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay_seconds=args.delay,
        weights=weights,
    ) as pipeline:
        results = pipeline.run()
        pipeline.export_csv(results, output_dir / "report.csv")
        pipeline.export_json(results, output_dir / "report.json")
        summary = pipeline.summary(results)

    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
