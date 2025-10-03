"""Unit tests for extraction.py module."""

import pytest

from attuario_ai.extraction import (
    ACTUARIAL_TERMS,
    CITATION_PATTERNS,
    FORMULA_PATTERNS,
    PageMetrics,
    extract_metrics,
)


class TestExtractMetrics:
    """Tests for extract_metrics function."""

    def test_extract_basic_metrics(self):
        """Test extraction of basic word count."""
        text = "This is a simple test with ten words in it."
        html = "<html><body><p>This is a simple test with ten words in it.</p></body></html>"

        metrics = extract_metrics(text, html)

        assert isinstance(metrics, PageMetrics)
        assert metrics.word_count == 10
        assert metrics.numeric_tokens == 0
        assert metrics.has_formula is False
        assert metrics.has_table is False
        assert metrics.has_list is False

    def test_extract_actuarial_terms(self):
        """Test extraction of actuarial terminology."""
        text = """
        The solvency ratio is important. The best estimate must be calculated.
        IVASS requires risk margin calculations. The SCR and BSCR are key metrics.
        We analyze mortalità and longevità trends.
        """
        html = "<html><body><p>" + text + "</p></body></html>"

        metrics = extract_metrics(text, html)

        assert "solvency" in metrics.actuarial_terms
        assert "best estimate" in metrics.actuarial_terms
        assert "ivass" in metrics.actuarial_terms
        assert "risk margin" in metrics.actuarial_terms
        assert "scr" in metrics.actuarial_terms
        assert "bscr" in metrics.actuarial_terms
        assert "mortalità" in metrics.actuarial_terms
        assert "longevità" in metrics.actuarial_terms
        assert len(metrics.actuarial_terms) >= 6

    def test_extract_numeric_tokens(self):
        """Test extraction of numeric tokens."""
        text = "The premium is 1000 EUR and the reserve is 25000.50 EUR. Risk is 3.14%."
        html = "<html><body><p>" + text + "</p></body></html>"

        metrics = extract_metrics(text, html)

        assert metrics.numeric_tokens == 3
        assert 1000.0 in metrics.example_values
        assert 25000.50 in metrics.example_values
        assert 3.14 in metrics.example_values

    def test_extract_numeric_with_comma(self):
        """Test extraction of numbers with comma as decimal separator."""
        text = "Il premio è 1500,75 EUR e la riserva è 30000,25 EUR."
        html = "<html><body><p>" + text + "</p></body></html>"

        metrics = extract_metrics(text, html)

        assert metrics.numeric_tokens == 2
        assert 1500.75 in metrics.example_values
        assert 30000.25 in metrics.example_values

    def test_detect_formula_patterns(self):
        """Test detection of mathematical formulas."""
        text_with_equation = r"The formula is \begin{equation} E = mc^2 \end{equation}"
        html = "<html><body><p>" + text_with_equation + "</p></body></html>"

        metrics = extract_metrics(text_with_equation, html)

        assert metrics.has_formula is True

    def test_detect_formula_with_latex(self):
        """Test detection of LaTeX-style formulas."""
        text_with_latex = r"The equation is \[ \int_0^1 f(x) dx = 1 \]"
        html = "<html><body><p>" + text_with_latex + "</p></body></html>"

        metrics = extract_metrics(text_with_latex, html)

        assert metrics.has_formula is True

    def test_detect_formula_with_math_symbols(self):
        """Test detection of mathematical symbols."""
        text_with_symbols = "The inequality a ≤ b ≥ c ≠ d holds."
        html = "<html><body><p>" + text_with_symbols + "</p></body></html>"

        metrics = extract_metrics(text_with_symbols, html)

        assert metrics.has_formula is True

    def test_detect_table_in_html(self):
        """Test detection of HTML tables."""
        text = "Analysis of data"
        html = """
        <html><body>
            <p>Analysis of data</p>
            <table>
                <tr><th>Year</th><th>Premium</th></tr>
                <tr><td>2023</td><td>1000</td></tr>
            </table>
        </body></html>
        """

        metrics = extract_metrics(text, html)

        assert metrics.has_table is True

    def test_detect_list_in_html(self):
        """Test detection of HTML lists."""
        text = "Requirements:"
        html = """
        <html><body>
            <p>Requirements:</p>
            <ul>
                <li>Solvency II compliance</li>
                <li>Risk assessment</li>
            </ul>
        </body></html>
        """

        metrics = extract_metrics(text, html)

        assert metrics.has_list is True

    def test_detect_ordered_list(self):
        """Test detection of ordered lists."""
        text = "Steps:"
        html = """
        <html><body>
            <ol>
                <li>First step</li>
                <li>Second step</li>
            </ol>
        </body></html>
        """

        metrics = extract_metrics(text, html)

        assert metrics.has_list is True

    def test_detect_citations(self):
        """Test detection of regulatory citations."""
        text = """
        According to IVASS regulations and EIOPA guidelines,
        the Solvency II framework requires specific calculations.
        The normativa and regolamento must be followed.
        """
        html = "<html><body><p>" + text + "</p></body></html>"

        metrics = extract_metrics(text, html)

        assert metrics.citation_matches > 0

    def test_empty_content(self):
        """Test extraction from empty content."""
        text = ""
        html = "<html><body></body></html>"

        metrics = extract_metrics(text, html)

        assert metrics.word_count == 0
        assert metrics.numeric_tokens == 0
        assert len(metrics.actuarial_terms) == 0
        assert metrics.citation_matches == 0

    def test_comprehensive_actuarial_document(self):
        """Test extraction from comprehensive actuarial document."""
        text = """
        Analisi Solvency II per IVASS
        
        Il Best Estimate della riserva matematica è calcolato utilizzando il tasso tecnico.
        Il premio puro è 5000 EUR con un risk margin di 500 EUR.
        
        Calcolo SCR:
        - BSCR base: 10000
        - Stress test applicato: 1.5
        - Value at Risk (VaR) al 99.5%
        
        Riferimenti normativi: EIOPA guidelines, circolare IVASS n. 23/2020.
        """
        html = """
        <html><body>
            <article>
                <h1>Analisi Solvency II per IVASS</h1>
                <p>Il Best Estimate della riserva matematica è calcolato utilizzando il tasso tecnico.</p>
                <p>Il premio puro è 5000 EUR con un risk margin di 500 EUR.</p>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>BSCR</td><td>10000</td></tr>
                </table>
                <ul>
                    <li>Stress test applicato: 1.5</li>
                    <li>Value at Risk (VaR) al 99.5%</li>
                </ul>
                <p>Riferimenti normativi: EIOPA guidelines, circolare IVASS n. 23/2020.</p>
            </article>
        </body></html>
        """

        metrics = extract_metrics(text, html)

        # Check actuarial terms
        assert len(metrics.actuarial_terms) >= 8
        assert "solvency" in metrics.actuarial_terms
        assert "ivass" in metrics.actuarial_terms
        assert "best estimate" in metrics.actuarial_terms
        assert "riserva matematica" in metrics.actuarial_terms
        assert "premio puro" in metrics.actuarial_terms
        assert "risk margin" in metrics.actuarial_terms
        assert "scr" in metrics.actuarial_terms
        assert "bscr" in metrics.actuarial_terms

        # Check numeric content
        assert metrics.numeric_tokens >= 4
        assert metrics.word_count > 30

        # Check structural elements
        assert metrics.has_table is True
        assert metrics.has_list is True

        # Check citations
        assert metrics.citation_matches >= 2

    def test_example_values_limit(self):
        """Test that example values are limited to 20."""
        numbers = " ".join([str(i) for i in range(50)])
        text = f"Numbers: {numbers}"
        html = f"<html><body><p>{text}</p></body></html>"

        metrics = extract_metrics(text, html)

        assert len(metrics.example_values) <= 20

    def test_metrics_to_dict(self):
        """Test conversion of metrics to dictionary."""
        text = "The premium is 1000 EUR."
        html = "<html><body><p>" + text + "</p></body></html>"

        metrics = extract_metrics(text, html)
        result_dict = metrics.to_dict()

        assert isinstance(result_dict, dict)
        assert "word_count" in result_dict
        assert "actuarial_terms" in result_dict
        assert "numeric_tokens" in result_dict
        assert "has_formula" in result_dict
        assert "has_table" in result_dict
        assert "has_list" in result_dict
        assert "citation_matches" in result_dict
        assert "example_values" in result_dict
