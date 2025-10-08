#!/usr/bin/env python3
"""Example demonstrating different scoring modes: heuristic, ml, and hybrid."""

import datetime as dt

from attuario_ai.extraction import extract_metrics
from attuario_ai.parser import PageParser
from attuario_ai.scoring import ScoreWeights, score_page
from ml.baseline_model import BaselineMLModel
from ml.predictor import MLPredictor


def main():
    """Demonstrate all three scoring modes."""

    # Sample HTML content
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Solvency II Risk Analysis</title>
    </head>
    <body>
        <article>
            <h1>Comprehensive Solvency II Risk Analysis</h1>
            <p>This article provides a detailed analysis of Solvency II regulations
            and their impact on insurance companies. The IVASS guidelines require
            careful calculation of the SCR (Solvency Capital Requirement).</p>

            <p>According to EIOPA standards, the risk margin should be calculated
            using the cost of capital approach with a rate of 6%. The best estimate
            liabilities must include all future cash flows with appropriate
            discounting.</p>

            <h2>Key Components</h2>
            <ul>
                <li>SCR: 1,250,000 EUR</li>
                <li>Best Estimate: 5,800,000 EUR</li>
                <li>Risk Margin: 320,000 EUR</li>
            </ul>

            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Coverage Ratio</td><td>185%</td></tr>
                <tr><td>MCR</td><td>562,500 EUR</td></tr>
            </table>

            <p>The stress test scenarios include market risk (32.5%), credit risk
            (18.2%), and operational risk (8.9%). The correlation matrix follows
            the standard formula prescribed by the regulation.</p>
        </article>
    </body>
    </html>
    """

    # Parse HTML
    parser = PageParser()
    fetched_at = dt.datetime.now(dt.timezone.utc).timestamp()
    parsed = parser.parse("https://example.com/solvency-analysis", sample_html, fetched_at)

    # Extract metrics
    metrics = extract_metrics(parsed.text, parsed.html)
    metadata = {"url": parsed.url, **parsed.metadata}

    print("=" * 70)
    print("EXAMPLE: Comparing Different Scoring Modes")
    print("=" * 70)
    print()

    # 1. Heuristic Mode (rule-based)
    print("1. HEURISTIC MODE (Rule-based)")
    print("-" * 70)
    weights = ScoreWeights()
    heuristic_score = score_page(metrics, metadata, weights)
    print(f"   Composite Score: {heuristic_score.composite:.2f}")
    print(f"   Classification: {heuristic_score.classification}")
    print("   Components:")
    for component, value in heuristic_score.components.items():
        print(f"     - {component}: {value:.2f}")
    print()

    # 2. ML Mode (machine learning)
    print("2. ML MODE (Machine Learning)")
    print("-" * 70)

    # Train a simple model for demonstration
    training_texts = [
        (
            "Comprehensive actuarial analysis with Solvency II, IVASS, SCR, "
            "risk margin, and EIOPA guidelines with detailed numerical calculations."
        ),
        "Simple page with no technical content.",
        (
            "Excellent analysis of best estimate liabilities with extensive "
            "regulatory citations and formulas."
        ),
        "Basic insurance information.",
        (
            "Advanced article on stress testing with market risk, credit risk, "
            "and operational risk calculations."
        ),
    ]
    training_scores = [85.0, 35.0, 92.0, 50.0, 88.0]

    model = BaselineMLModel()
    train_metrics = model.train(training_texts, training_scores)
    print(
        f"   Model trained with MAE: {train_metrics['mae']:.2f}, "
        f"MSE: {train_metrics['mse']:.2f}"
    )

    # Create predictor with trained model
    predictor = MLPredictor()
    predictor.model = model

    ml_score = predictor.score_page(parsed.text, metrics, metadata)
    print(f"   Composite Score: {ml_score.composite:.2f}")
    print(f"   Classification: {ml_score.classification}")
    print()

    # 3. Hybrid Mode (combination)
    print("3. HYBRID MODE (Combined Heuristic + ML)")
    print("-" * 70)
    hybrid_composite = (heuristic_score.composite + ml_score.composite) / 2

    # Determine classification
    if hybrid_composite >= 85:
        hybrid_classification = "Eccellente"
    elif hybrid_composite >= 70:
        hybrid_classification = "Buono"
    elif hybrid_composite >= 50:
        hybrid_classification = "Discreto"
    else:
        hybrid_classification = "Criticità"

    print(f"   Composite Score: {hybrid_composite:.2f}")
    print(f"   Classification: {hybrid_classification}")
    print("   Breakdown:")
    print(f"     - Heuristic: {heuristic_score.composite:.2f}")
    print(f"     - ML: {ml_score.composite:.2f}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Heuristic Mode: {heuristic_score.composite:.2f} ({heuristic_score.classification})")
    print(f"ML Mode:        {ml_score.composite:.2f} ({ml_score.classification})")
    print(f"Hybrid Mode:    {hybrid_composite:.2f} ({hybrid_classification})")
    print()
    print("The hybrid mode provides a balanced approach that combines")
    print("domain-specific rules with learned patterns from training data.")
    print()


if __name__ == "__main__":
    main()
