"""Unit tests for ML module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from attuario_ai.extraction import PageMetrics
from ml.baseline_model import BaselineMLModel
from ml.predictor import MLPredictor


class TestBaselineMLModel:
    """Tests for BaselineMLModel class."""

    def test_model_initialization(self):
        """Test model can be initialized."""
        model = BaselineMLModel()
        assert model is not None
        assert not model.is_trained

    def test_train_model(self):
        """Test training the model with sample data."""
        model = BaselineMLModel()

        texts = [
            "This is a comprehensive actuarial analysis with solvency data",
            "Poor quality page with no actuarial content",
            "Excellent article discussing risk margin and SCR calculations",
            "Basic page about insurance",
        ]
        scores = [85.0, 40.0, 92.0, 55.0]

        metrics = model.train(texts, scores)

        assert model.is_trained
        assert "mae" in metrics
        assert "mse" in metrics
        assert "train_samples" in metrics
        assert "test_samples" in metrics

    def test_train_empty_data_raises_error(self):
        """Test that training with empty data raises ValueError."""
        model = BaselineMLModel()

        with pytest.raises(ValueError, match="Cannot train on empty dataset"):
            model.train([], [])

    def test_train_mismatched_lengths_raises_error(self):
        """Test that mismatched texts and scores raise ValueError."""
        model = BaselineMLModel()

        texts = ["text1", "text2"]
        scores = [50.0]

        with pytest.raises(ValueError, match="same length"):
            model.train(texts, scores)

    def test_predict_without_training_raises_error(self):
        """Test that prediction without training raises RuntimeError."""
        model = BaselineMLModel()

        with pytest.raises(RuntimeError, match="must be trained"):
            model.predict(["some text"])

    def test_predict_after_training(self):
        """Test prediction after training."""
        model = BaselineMLModel()

        texts = [
            "This is actuarial content with solvency ii",
            "Poor content no value",
            "Excellent analysis with risk margin",
            "Basic insurance page",
        ]
        scores = [85.0, 40.0, 90.0, 55.0]

        model.train(texts, scores)
        predictions = model.predict(["New actuarial content about solvency"])

        assert len(predictions) == 1
        assert 0 <= predictions[0] <= 100

    def test_save_without_training_raises_error(self):
        """Test that saving without training raises RuntimeError."""
        model = BaselineMLModel()

        with TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            vectorizer_path = Path(tmpdir) / "vectorizer.pkl"

            with pytest.raises(RuntimeError, match="Cannot save untrained model"):
                model.save(model_path, vectorizer_path)

    def test_save_and_load_model(self):
        """Test saving and loading a trained model."""
        model = BaselineMLModel()

        texts = [
            "Actuarial content with solvency",
            "Poor content",
            "Excellent analysis",
            "Basic page",
        ]
        scores = [85.0, 40.0, 90.0, 55.0]

        model.train(texts, scores)

        with TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            vectorizer_path = Path(tmpdir) / "vectorizer.pkl"

            model.save(model_path, vectorizer_path)

            # Load into new model
            new_model = BaselineMLModel()
            new_model.load(model_path, vectorizer_path)

            assert new_model.is_trained
            predictions = new_model.predict(["Test text"])
            assert len(predictions) == 1

    def test_load_nonexistent_model_raises_error(self):
        """Test that loading nonexistent model raises FileNotFoundError."""
        model = BaselineMLModel()

        with pytest.raises(FileNotFoundError):
            model.load(Path("/nonexistent/model.pkl"), Path("/nonexistent/vec.pkl"))


class TestMLPredictor:
    """Tests for MLPredictor class."""

    def test_predictor_initialization_without_model(self):
        """Test predictor can be initialized without a model."""
        predictor = MLPredictor()
        assert predictor is not None
        assert predictor.model is not None

    def test_predictor_initialization_with_nonexistent_model_raises_error(self):
        """Test that initializing with nonexistent model raises error."""
        with pytest.raises(FileNotFoundError):
            MLPredictor(model_dir=Path("/nonexistent/models"))

    def test_score_page_without_trained_model_raises_error(self):
        """Test that scoring without trained model raises RuntimeError."""
        predictor = MLPredictor()

        metrics = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=0,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )
        metadata = {"url": "https://example.com"}

        with pytest.raises(RuntimeError, match="must be trained"):
            predictor.score_page("Some text", metrics, metadata)

    def test_score_page_with_trained_model(self):
        """Test scoring a page with a trained model."""
        # Train a model first
        model = BaselineMLModel()
        texts = [
            "Actuarial content with solvency",
            "Poor content",
            "Excellent analysis",
            "Basic page",
        ]
        scores = [85.0, 40.0, 90.0, 55.0]
        model.train(texts, scores)

        # Create predictor with trained model
        predictor = MLPredictor()
        predictor.model = model

        metrics = PageMetrics(
            word_count=100,
            actuarial_terms={"solvency": 2},
            numeric_tokens=10,
            has_formula=True,
            has_table=True,
            has_list=True,
            citation_matches=2,
            example_values=[],
        )
        metadata = {"url": "https://example.com/test"}

        score = predictor.score_page("Test actuarial content", metrics, metadata)

        assert score is not None
        assert score.url == "https://example.com/test"
        assert 0 <= score.composite <= 100
        assert score.classification in ["Eccellente", "Buono", "Discreto", "Criticità"]
        assert "ml_score" in score.components

    def test_classification_thresholds(self):
        """Test classification thresholds in predictor."""
        predictor = MLPredictor()

        assert predictor._classify(90.0) == "Eccellente"
        assert predictor._classify(75.0) == "Buono"
        assert predictor._classify(60.0) == "Discreto"
        assert predictor._classify(40.0) == "Criticità"
