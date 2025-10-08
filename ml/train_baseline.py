#!/usr/bin/env python3
"""Script to train the baseline ML model on labeled data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from attuario_ai import EvaluationPipeline
from ml.baseline_model import BaselineMLModel


def normalize_url(url: str) -> str:
    """Normalize URL for consistent matching.

    Args:
        url: URL string to normalize.

    Returns:
        Normalized URL string.
    """
    url = url.strip().rstrip("/")
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)
    return url


def load_labels(labels_path: Path) -> Tuple[Dict[str, float], List[str]]:
    """Load training labels from JSON file.

    Args:
        labels_path: Path to labels.json file.

    Returns:
        Tuple of (url_to_score dict, list of seed URLs).

    Raises:
        ValueError: If labels file is invalid or empty.
    """
    with open(labels_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Labels file must contain a JSON array")

    url_to_score: Dict[str, float] = {}
    seeds: List[str] = []

    for entry in data:
        if not isinstance(entry, dict):
            continue
        url = entry.get("url")
        score = entry.get("target_score")
        if url and score is not None:
            normalized = normalize_url(str(url))
            url_to_score[normalized] = float(score)
            seeds.append(str(url))

    if not url_to_score:
        raise ValueError("No valid labels found in file")

    return url_to_score, seeds


def main() -> None:
    """Main training function."""
    parser = argparse.ArgumentParser(
        description="Train baseline ML model on labeled pages"
    )
    parser.add_argument(
        "base_url",
        help="Base URL for crawling (e.g., https://www.attuario.eu)",
    )
    parser.add_argument(
        "labels",
        type=Path,
        help="Path to labels.json file with training data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml/models"),
        help="Directory to save trained model (default: ml/models)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Max pages to crawl (defaults to number of labels)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between requests in seconds",
    )

    args = parser.parse_args()

    # Load labels
    print(f"Loading labels from {args.labels}...")
    url_to_score, seeds = load_labels(args.labels)
    print(f"Found {len(url_to_score)} labeled pages")

    # Crawl and parse pages
    max_pages = args.max_pages or len(url_to_score)
    print(f"Crawling up to {max_pages} pages from {args.base_url}...")

    with EvaluationPipeline(
        args.base_url,
        max_pages=max_pages,
        max_depth=0,
        delay_seconds=args.delay,
    ) as pipeline:
        results = pipeline.run(seeds=seeds)

    print(f"Successfully crawled {len(results)} pages")

    # Match crawled pages with labels
    texts: List[str] = []
    scores: List[float] = []

    for result in results:
        normalized_url = normalize_url(result.page.url)
        if normalized_url in url_to_score:
            texts.append(result.page.text)
            scores.append(url_to_score[normalized_url])

    if not texts:
        print("ERROR: No pages matched with labels!")
        return

    print(f"Matched {len(texts)} pages with labels")

    # Train model
    print("Training baseline ML model...")
    model = BaselineMLModel()
    metrics = model.train(texts, scores)

    print("\nTraining results:")
    print(f"  MAE: {metrics['mae']}")
    print(f"  MSE: {metrics['mse']}")
    print(f"  Train samples: {metrics['train_samples']}")
    print(f"  Test samples: {metrics['test_samples']}")

    # Save model
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "model.pkl"
    vectorizer_path = args.output_dir / "vectorizer.pkl"

    model.save(model_path, vectorizer_path)
    print(f"\nModel saved to {args.output_dir}/")
    print(f"  - {model_path.name}")
    print(f"  - {vectorizer_path.name}")


if __name__ == "__main__":
    main()
