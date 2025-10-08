"""Integration tests for crawler with logging and retry mechanism."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from attuario_ai import Crawler, setup_logging


class TestCrawlerLogging:
    """Tests for crawler logging functionality."""

    def test_crawler_logs_initialization(self):
        """Test that crawler logs initialization information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "crawler_test.log"
            setup_logging(log_file=str(log_file))

            # Create a crawler (we need to use it to trigger logging)
            _ = Crawler(
                "https://example.com", max_pages=10, max_depth=2, use_cache=False
            )

            # Check log content
            content = log_file.read_text()
            assert "Initializing crawler for https://example.com" in content
            assert "max_pages=10" in content
            assert "max_depth=2" in content

    def test_crawler_logs_robots_txt_fetch(self):
        """Test that crawler logs robots.txt fetch attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "crawler_test.log"
            setup_logging(log_file=str(log_file))

            with patch("requests.Session.get") as mock_get:
                # Mock successful robots.txt fetch
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = "User-agent: *\nDisallow:\n"
                mock_get.return_value = mock_response

                _ = Crawler("https://example.com", use_cache=False)

                content = log_file.read_text()
                assert (
                    "Successfully fetched robots.txt from https://example.com/robots.txt"
                    in content
                )

    def test_crawler_retry_on_timeout(self):
        """Test that crawler retries on timeout errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "retry_test.log"
            setup_logging(log_file=str(log_file))

            with patch("requests.Session.get") as mock_get:
                # First attempt for robots.txt - success
                robots_response = Mock()
                robots_response.status_code = 404
                robots_response.text = ""

                # Page fetch attempts - first timeout, second success
                page_response = Mock()
                page_response.status_code = 200
                page_response.text = "<html><body>Test</body></html>"

                mock_get.side_effect = [
                    robots_response,  # robots.txt
                    requests.Timeout("Timeout"),  # First page attempt
                    page_response,  # Second page attempt (retry success)
                ]

                crawler = Crawler("https://example.com", max_pages=1, use_cache=False)
                results = list(crawler.crawl())

                # Check that we got a result
                assert len(results) == 1

                # Check log content
                content = log_file.read_text()
                assert "Timeout fetching" in content
                assert "attempt 1/3" in content or "Retry attempt" in content

    def test_crawler_logs_successful_crawl(self):
        """Test that crawler logs successful crawl operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "success_test.log"
            setup_logging(log_file=str(log_file))

            with patch("requests.Session.get") as mock_get:
                # Mock robots.txt
                robots_response = Mock()
                robots_response.status_code = 404
                robots_response.text = ""

                # Mock page response
                page_response = Mock()
                page_response.status_code = 200
                page_response.text = "<html><body><h1>Test Page</h1></body></html>"

                mock_get.side_effect = [robots_response, page_response]

                crawler = Crawler("https://example.com", max_pages=1, use_cache=False)
                results = list(crawler.crawl())

                assert len(results) == 1

                # Check log content
                content = log_file.read_text()
                assert "Starting crawl" in content
                assert "Successfully crawled [1/1]" in content
                assert "Crawl completed. Total pages crawled: 1" in content
