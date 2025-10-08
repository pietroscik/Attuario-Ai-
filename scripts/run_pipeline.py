#!/usr/bin/env python3
"""Command line entry point for the Attuario AI evaluation pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from attuario_ai import EvaluationPipeline, ScoreWeights, setup_logging


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
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("logs/pipeline.log"),
        help="Path to log file (default: logs/pipeline.log)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["heuristic", "ml", "hybrid"],
        default="heuristic",
        help="Scoring mode: heuristic (rule-based), ml (machine learning), or hybrid (both)",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        help="Directory containing trained ML model (required for ml/hybrid modes)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable HTTP response caching (default: caching enabled)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help=(
            "Maximum number of parallel workers for crawling "
            "(default: 4, use 1 to disable parallelization)"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Setup logging
    setup_logging(log_file=str(args.log_file))

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate mode and model-dir
    if args.mode in ("ml", "hybrid") and not args.model_dir:
        print("ERROR: --model-dir is required when using ml or hybrid mode")
        return

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
        mode=args.mode,
        model_dir=args.model_dir,
        use_cache=not args.no_cache,
        max_workers=args.max_workers,
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
