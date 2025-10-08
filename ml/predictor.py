"""ML-based predictor for scoring pages."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from attuario_ai.extraction import PageMetrics
from attuario_ai.scoring import PageScore

from .baseline_model import BaselineMLModel


class MLPredictor:
    """ML-based predictor for actuarial content scoring.

    This predictor uses a trained machine learning model to score pages
    based on their text content.

    Attributes:
        model: BaselineMLModel instance for prediction.
    """

    def __init__(self, model_dir: Path | None = None) -> None:
        """Initialize the ML predictor.

        Args:
            model_dir: Optional directory containing saved model files.
                      If provided, loads the model from disk.
        """
        self.model = BaselineMLModel()

        if model_dir is not None:
            model_path = model_dir / "model.pkl"
            vectorizer_path = model_dir / "vectorizer.pkl"
            self.model.load(model_path, vectorizer_path)

    def score_page(self, text: str, metrics: PageMetrics, metadata: Dict[str, str]) -> PageScore:
        """Score a page using the ML model.

        Args:
            text: Page text content.
            metrics: PageMetrics object (used for fallback classification).
            metadata: Dictionary containing page metadata (including URL).

        Returns:
            PageScore object with ML-predicted score.

        Raises:
            RuntimeError: If model hasn't been trained.
        """
        if not self.model.is_trained:
            raise RuntimeError("Model must be trained or loaded before prediction")

        # Predict score using ML model
        predicted_scores = self.model.predict([text])
        composite = round(predicted_scores[0], 2)

        # Classify based on score
        classification = self._classify(composite)

        # Components are not available from ML model, so we set them to composite
        components = {
            "ml_score": composite,
            "accuracy": composite,
            "transparency": composite,
            "completeness": composite,
            "freshness": composite,
            "clarity": composite,
        }

        return PageScore(
            url=metadata.get("url", ""),
            composite=composite,
            components=components,
            classification=classification,
        )

    def _classify(self, score: float) -> str:
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
