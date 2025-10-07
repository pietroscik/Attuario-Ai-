"""Unit tests for parser.py module."""

import time
from datetime import datetime, timezone

from attuario_ai.parser import PageParser, ParsedPage


class TestPageParser:
    """Tests for PageParser class."""

    def test_parser_initialization(self):
        """Test parser initializes with correct language."""
        parser = PageParser(language="it")
        assert parser.language == "it"

        parser_en = PageParser(language="en")
        assert parser_en.language == "en"

    def test_parse_simple_html(self):
        """Test parsing simple HTML with title and body."""
        parser = PageParser()
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <p>This is a test paragraph.</p>
                </article>
            </body>
        </html>
        """
        url = "https://example.com/test"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        assert isinstance(result, ParsedPage)
        assert result.url == url
        assert result.title == "Test Page"
        assert "Article Title" in result.text
        assert "test paragraph" in result.text
        assert result.html == html
        assert isinstance(result.fetched_at, datetime)
        assert result.fetched_at.tzinfo == timezone.utc

    def test_parse_with_metadata(self):
        """Test parsing HTML with metadata tags."""
        parser = PageParser()
        html = """
        <html>
            <head>
                <title>Actuarial Article</title>
                <meta name="description" content="Test description">
                <meta name="author" content="Test Author">
                <meta property="article:published_time" content="2023-01-15T10:00:00Z">
                <meta property="article:modified_time" content="2023-06-20T14:30:00Z">
            </head>
            <body>
                <main>Content here</main>
            </body>
        </html>
        """
        url = "https://example.com/article"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        assert result.metadata["description"] == "Test description"
        assert result.metadata["author"] == "Test Author"
        assert result.metadata["published"] == "2023-01-15T10:00:00Z"
        assert result.metadata["modified"] == "2023-06-20T14:30:00Z"
        assert result.metadata["language"] == "it"

    def test_parse_without_metadata(self):
        """Test parsing HTML without metadata tags."""
        parser = PageParser()
        html = """
        <html>
            <head><title>Simple Page</title></head>
            <body><p>Simple content</p></body>
        </html>
        """
        url = "https://example.com/simple"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        assert result.metadata["description"] is None
        assert result.metadata["author"] is None
        assert result.metadata["published"] is None
        assert result.metadata["modified"] is None

    def test_parse_empty_title(self):
        """Test parsing HTML without title tag."""
        parser = PageParser()
        html = """
        <html>
            <head></head>
            <body><p>No title page</p></body>
        </html>
        """
        url = "https://example.com/notitle"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        assert result.title == ""

    def test_select_main_content_article(self):
        """Test that parser selects article content appropriately."""
        parser = PageParser()
        html = """
        <html>
            <body>
                <header>Header</header>
                <article>
                    Main article content with substantial text to make it
                    the largest element. This should be selected as the main
                    content area since it contains the most text.
                </article>
                <footer>Footer</footer>
            </body>
        </html>
        """
        url = "https://example.com/test"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        # Should contain the main article content
        assert "Main article content" in result.text
        assert "substantial text" in result.text

    def test_parse_actuarial_content(self):
        """Test parsing actuarial-specific content."""
        parser = PageParser()
        html = """
        <html>
            <head><title>Solvency II Analysis</title></head>
            <body>
                <article>
                    <h1>Riserva Matematica</h1>
                    <p>Il Best Estimate è calcolato secondo IVASS.</p>
                    <p>Il premio puro ammonta a 1000 EUR.</p>
                </article>
            </body>
        </html>
        """
        url = "https://attuario.eu/solvency"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        assert result.title == "Solvency II Analysis"
        assert "Riserva Matematica" in result.text
        assert "Best Estimate" in result.text
        assert "IVASS" in result.text
        assert "premio puro" in result.text

    def test_find_datetime_with_time_tag(self):
        """Test datetime extraction from time tag."""
        parser = PageParser()
        html = """
        <html>
            <body>
                <time datetime="2023-12-01T12:00:00Z">December 1, 2023</time>
            </body>
        </html>
        """
        url = "https://example.com/test"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        # Should find time tag datetime if no meta property
        assert result.metadata["published"] == "2023-12-01T12:00:00Z"

    def test_parse_preserves_original_html(self):
        """Test that original HTML is preserved in result."""
        parser = PageParser()
        html = "<html><body><p>Test</p></body></html>"
        url = "https://example.com/test"
        fetched_at = time.time()

        result = parser.parse(url, html, fetched_at)

        assert result.html == html
