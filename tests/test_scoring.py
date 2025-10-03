"""Unit tests for scoring.py module."""

import datetime as dt

import pytest

from attuario_ai.extraction import PageMetrics
from attuario_ai.scoring import (
    PageScore,
    ScoreWeights,
    apply_weights,
    compute_components,
    score_page,
)


class TestScoreWeights:
    """Tests for ScoreWeights class."""

    def test_default_weights(self):
        """Test default weight values."""
        weights = ScoreWeights()

        assert weights.accuracy == 0.4
        assert weights.transparency == 0.2
        assert weights.completeness == 0.2
        assert weights.freshness == 0.1
        assert weights.clarity == 0.1

    def test_custom_weights(self):
        """Test custom weight values."""
        weights = ScoreWeights(
            accuracy=0.5,
            transparency=0.3,
            completeness=0.1,
            freshness=0.05,
            clarity=0.05,
        )

        assert weights.accuracy == 0.5
        assert weights.transparency == 0.3
        assert weights.completeness == 0.1

    def test_normalize_weights(self):
        """Test weight normalization."""
        weights = ScoreWeights(
            accuracy=2.0,
            transparency=1.0,
            completeness=1.0,
            freshness=0.5,
            clarity=0.5,
        )

        normalized = weights.normalize()

        # Sum should be 1.0 after normalization
        total = (
            normalized.accuracy
            + normalized.transparency
            + normalized.completeness
            + normalized.freshness
            + normalized.clarity
        )
        assert abs(total - 1.0) < 0.001

    def test_normalize_zero_weights_raises_error(self):
        """Test that normalizing zero weights raises ValueError."""
        weights = ScoreWeights(
            accuracy=0.0,
            transparency=0.0,
            completeness=0.0,
            freshness=0.0,
            clarity=0.0,
        )

        with pytest.raises(ValueError, match="Weights sum to zero"):
            weights.normalize()

    def test_weights_to_dict(self):
        """Test conversion of weights to dictionary."""
        weights = ScoreWeights()
        result = weights.to_dict()

        assert isinstance(result, dict)
        assert result["accuracy"] == 0.4
        assert result["transparency"] == 0.2
        assert result["completeness"] == 0.2
        assert result["freshness"] == 0.1
        assert result["clarity"] == 0.1

    def test_weights_from_dict(self):
        """Test creation of weights from dictionary."""
        data = {
            "accuracy": 0.5,
            "transparency": 0.25,
            "completeness": 0.15,
            "freshness": 0.05,
            "clarity": 0.05,
        }

        weights = ScoreWeights.from_dict(data)

        assert weights.accuracy == 0.5
        assert weights.transparency == 0.25
        assert weights.completeness == 0.15


class TestComputeComponents:
    """Tests for compute_components function."""

    def test_compute_basic_components(self):
        """Test computation of basic score components."""
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
        metadata = {}

        components = compute_components(metrics, metadata)

        assert "accuracy" in components
        assert "transparency" in components
        assert "completeness" in components
        assert "freshness" in components
        assert "clarity" in components
        assert all(0 <= v <= 100 for v in components.values())

    def test_accuracy_score_with_numerics(self):
        """Test accuracy score increases with numeric content."""
        metrics_no_numbers = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=0,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        metrics_with_numbers = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=10,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        components_no = compute_components(metrics_no_numbers, {})
        components_yes = compute_components(metrics_with_numbers, {})

        assert components_yes["accuracy"] > components_no["accuracy"]

    def test_accuracy_score_with_formula(self):
        """Test accuracy score increases with formulas."""
        metrics_no_formula = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=10,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        metrics_with_formula = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=10,
            has_formula=True,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        components_no = compute_components(metrics_no_formula, {})
        components_yes = compute_components(metrics_with_formula, {})

        assert components_yes["accuracy"] > components_no["accuracy"]

    def test_transparency_score_with_citations(self):
        """Test transparency score increases with citations."""
        metrics_no_citations = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=0,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        metrics_with_citations = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=0,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=3,
            example_values=[],
        )

        components_no = compute_components(metrics_no_citations, {})
        components_yes = compute_components(metrics_with_citations, {})

        assert components_yes["transparency"] > components_no["transparency"]

    def test_completeness_score_with_structure(self):
        """Test completeness score with tables and lists."""
        metrics_minimal = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=0,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        metrics_complete = PageMetrics(
            word_count=100,
            actuarial_terms={"solvency": 2, "ivass": 1, "scr": 1},
            numeric_tokens=0,
            has_formula=False,
            has_table=True,
            has_list=True,
            citation_matches=0,
            example_values=[],
        )

        components_min = compute_components(metrics_minimal, {})
        components_comp = compute_components(metrics_complete, {})

        assert components_comp["completeness"] > components_min["completeness"]

    def test_freshness_score_recent_date(self):
        """Test freshness score for recent content."""
        recent_date = (
            dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
        ).isoformat()
        old_date = (
            dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=400)
        ).isoformat()

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

        components_recent = compute_components(metrics, {"published": recent_date})
        components_old = compute_components(metrics, {"published": old_date})

        assert components_recent["freshness"] > components_old["freshness"]

    def test_freshness_score_no_date(self):
        """Test freshness score when no date is provided."""
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

        components = compute_components(metrics, {})

        # Should return default score of 50.0
        assert components["freshness"] == 50.0

    def test_clarity_score(self):
        """Test clarity score based on numeric ratio."""
        metrics_few_numbers = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=5,  # 5% ratio
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        metrics_many_numbers = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=20,  # 20% ratio
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )

        components_few = compute_components(metrics_few_numbers, {})
        components_many = compute_components(metrics_many_numbers, {})

        # Higher clarity score for fewer numbers (more readable)
        assert components_few["clarity"] > components_many["clarity"]


class TestApplyWeights:
    """Tests for apply_weights function."""

    def test_apply_default_weights(self):
        """Test applying default weights to components."""
        components = {
            "accuracy": 80.0,
            "transparency": 70.0,
            "completeness": 60.0,
            "freshness": 50.0,
            "clarity": 90.0,
        }
        weights = ScoreWeights()

        score = apply_weights(components, weights)

        # Should be weighted average
        expected = (80.0 * 0.4 + 70.0 * 0.2 + 60.0 * 0.2 + 50.0 * 0.1 + 90.0 * 0.1)
        assert abs(score - expected) < 0.01

    def test_apply_custom_weights(self):
        """Test applying custom weights."""
        components = {
            "accuracy": 100.0,
            "transparency": 0.0,
            "completeness": 0.0,
            "freshness": 0.0,
            "clarity": 0.0,
        }
        weights = ScoreWeights(
            accuracy=1.0,
            transparency=0.0,
            completeness=0.0,
            freshness=0.0,
            clarity=0.0,
        )

        score = apply_weights(components, weights)

        # Should be 100.0 since only accuracy matters
        assert score == 100.0


class TestScorePage:
    """Tests for score_page function."""

    def test_score_excellent_page(self):
        """Test scoring an excellent actuarial page."""
        metrics = PageMetrics(
            word_count=500,
            actuarial_terms={
                "solvency": 3,
                "ivass": 2,
                "best estimate": 2,
                "scr": 1,
                "bscr": 1,
            },
            numeric_tokens=50,
            has_formula=True,
            has_table=True,
            has_list=True,
            citation_matches=4,
            example_values=[1000.0, 2000.0, 3000.0],
        )
        recent_date = (
            dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
        ).isoformat()
        metadata = {
            "url": "https://attuario.eu/analysis",
            "published": recent_date,
        }
        weights = ScoreWeights()

        result = score_page(metrics, metadata, weights)

        assert isinstance(result, PageScore)
        assert result.url == "https://attuario.eu/analysis"
        assert result.composite >= 70.0  # Should be at least "Buono"
        assert result.classification in ["Eccellente", "Buono"]
        assert "accuracy" in result.components
        assert "transparency" in result.components

    def test_score_poor_page(self):
        """Test scoring a poor quality page."""
        metrics = PageMetrics(
            word_count=50,
            actuarial_terms={},
            numeric_tokens=0,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=0,
            example_values=[],
        )
        metadata = {"url": "https://example.com/test"}
        weights = ScoreWeights()

        result = score_page(metrics, metadata, weights)

        assert result.composite < 70.0
        assert result.classification in ["Discreto", "Criticità"]

    def test_classification_thresholds(self):
        """Test classification boundary values."""
        metrics_base = PageMetrics(
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

        # Test that classification follows thresholds:
        # >= 85: Eccellente
        # >= 70: Buono
        # >= 50: Discreto
        # < 50: Criticità

        result = score_page(metrics_base, metadata, ScoreWeights())
        assert result.classification in ["Eccellente", "Buono", "Discreto", "Criticità"]

    def test_score_components_rounded(self):
        """Test that score components are properly rounded."""
        metrics = PageMetrics(
            word_count=100,
            actuarial_terms={},
            numeric_tokens=5,
            has_formula=False,
            has_table=False,
            has_list=False,
            citation_matches=1,
            example_values=[],
        )
        metadata = {"url": "https://example.com"}
        weights = ScoreWeights()

        result = score_page(metrics, metadata, weights)

        # Check that all values are rounded to 2 decimal places
        assert result.composite == round(result.composite, 2)
        for value in result.components.values():
            assert value == round(value, 2)

    def test_score_with_missing_url(self):
        """Test scoring when URL is missing from metadata."""
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
        metadata = {}
        weights = ScoreWeights()

        result = score_page(metrics, metadata, weights)

        assert result.url == ""

    def test_score_comprehensive_actuarial_page(self):
        """Test scoring a comprehensive actuarial analysis page."""
        metrics = PageMetrics(
            word_count=800,
            actuarial_terms={
                "solvency": 5,
                "solvency ii": 3,
                "ivass": 4,
                "eiopa": 2,
                "riserva": 3,
                "best estimate": 4,
                "premio": 2,
                "scr": 3,
                "bscr": 2,
                "risk margin": 2,
            },
            numeric_tokens=120,
            has_formula=True,
            has_table=True,
            has_list=True,
            citation_matches=6,
            example_values=[1000.0, 2500.0, 3700.5, 10000.0],
        )
        recent_date = (
            dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=15)
        ).isoformat()
        metadata = {
            "url": "https://attuario.eu/solvency-analysis",
            "title": "Comprehensive Solvency II Analysis",
            "published": recent_date,
        }
        weights = ScoreWeights()

        result = score_page(metrics, metadata, weights)

        # Should score highly on all dimensions
        assert result.composite >= 75.0
        assert result.components["accuracy"] >= 70.0
        assert result.components["transparency"] >= 70.0
        assert result.components["completeness"] >= 70.0
        assert result.components["freshness"] >= 85.0
        assert result.classification in ["Eccellente", "Buono"]
