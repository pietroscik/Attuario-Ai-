"""Baseline ML model using TF-IDF and Logistic Regression."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split


class BaselineMLModel:
    """TF-IDF + Logistic Regression model for scoring actuarial content.

    This baseline model uses TF-IDF vectorization to convert text into features
    and Logistic Regression to predict quality scores.

    Attributes:
        vectorizer: TfidfVectorizer for text feature extraction.
        model: LogisticRegression model for prediction.
    """

    def __init__(self) -> None:
        """Initialize the baseline ML model."""
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
        )
        self.model = LogisticRegression(max_iter=1000, random_state=42)
        self._is_trained = False

    def train(
        self, texts: List[str], scores: List[float], test_size: float = 0.2
    ) -> Dict[str, float]:
        """Train the model on labeled data.

        Args:
            texts: List of text content from pages.
            scores: List of target scores (0-100) corresponding to each text.
            test_size: Fraction of data to use for validation (default: 0.2).

        Returns:
            Dictionary containing training metrics (MAE, MSE, R2).

        Raises:
            ValueError: If texts and scores have different lengths or are empty.
        """
        if len(texts) != len(scores):
            raise ValueError("texts and scores must have the same length")
        if len(texts) == 0:
            raise ValueError("Cannot train on empty dataset")

        # Convert continuous scores to bins for classification
        # Bins: 0-50 (Criticità), 50-70 (Discreto), 70-85 (Buono), 85-100 (Eccellente)
        score_bins = [0, 50, 70, 85, 100]
        y_binned = np.digitize(scores, bins=score_bins[1:], right=False)

        # Split data
        if len(texts) < 4:
            # Too few samples for split, use all for training
            X_train_text = texts
            y_train = y_binned
            X_test_text = texts
            y_test = y_binned
        else:
            X_train_text, X_test_text, y_train, y_test = train_test_split(
                texts, y_binned, test_size=test_size, random_state=42
            )

        # Vectorize text
        X_train = self.vectorizer.fit_transform(X_train_text)
        X_test = self.vectorizer.transform(X_test_text)

        # Train model
        self.model.fit(X_train, y_train)
        self._is_trained = True

        # Evaluate on test set
        y_pred = self.model.predict(X_test)

        # Convert class predictions back to scores (use bin midpoints)
        bin_midpoints = [25.0, 60.0, 77.5, 92.5]
        y_test_scores = [bin_midpoints[int(label)] for label in y_test]
        y_pred_scores = [bin_midpoints[int(label)] for label in y_pred]

        mae = mean_absolute_error(y_test_scores, y_pred_scores)
        mse = mean_squared_error(y_test_scores, y_pred_scores)

        return {
            "mae": round(mae, 2),
            "mse": round(mse, 2),
            "train_samples": len(X_train_text),
            "test_samples": len(X_test_text),
        }

    def predict(self, texts: List[str]) -> List[float]:
        """Predict scores for new texts.

        Args:
            texts: List of text content to score.

        Returns:
            List of predicted scores (0-100).

        Raises:
            RuntimeError: If model hasn't been trained yet.
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before prediction")

        X = self.vectorizer.transform(texts)
        y_pred = self.model.predict(X)

        # Convert class predictions to scores (use bin midpoints)
        bin_midpoints = [25.0, 60.0, 77.5, 92.5]
        scores = [bin_midpoints[int(label)] for label in y_pred]

        return scores

    def save(self, model_path: Path, vectorizer_path: Path) -> None:
        """Save the trained model and vectorizer to disk.

        Args:
            model_path: Path where the model should be saved.
            vectorizer_path: Path where the vectorizer should be saved.

        Raises:
            RuntimeError: If model hasn't been trained yet.
        """
        if not self._is_trained:
            raise RuntimeError("Cannot save untrained model")

        model_path.parent.mkdir(parents=True, exist_ok=True)
        vectorizer_path.parent.mkdir(parents=True, exist_ok=True)

        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)

        with open(vectorizer_path, "wb") as f:
            pickle.dump(self.vectorizer, f)

    def load(self, model_path: Path, vectorizer_path: Path) -> None:
        """Load a trained model and vectorizer from disk.

        Args:
            model_path: Path to the saved model.
            vectorizer_path: Path to the saved vectorizer.

        Raises:
            FileNotFoundError: If model or vectorizer files don't exist.
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not vectorizer_path.exists():
            raise FileNotFoundError(f"Vectorizer file not found: {vectorizer_path}")

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        with open(vectorizer_path, "rb") as f:
            self.vectorizer = pickle.load(f)

        self._is_trained = True

    @property
    def is_trained(self) -> bool:
        """Check if the model has been trained.

        Returns:
            True if model is trained, False otherwise.
        """
        return self._is_trained
