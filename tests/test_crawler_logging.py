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

    def test_crawler_with_caching_enabled(self):
        """Test that crawler logs caching configuration when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "cache_test.log"
            setup_logging(log_file=str(log_file))

            # Create crawler with caching enabled (default)
            crawler = Crawler("https://example.com", use_cache=True)
            crawler.close()

            # Check log content for cache configuration
            content = log_file.read_text()
            assert "HTTP caching enabled" in content
            assert "expire_after=" in content

    def test_crawler_with_parallel_workers(self):
        """Test that crawler logs parallel configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "parallel_test.log"
            setup_logging(log_file=str(log_file))

            # Create crawler with multiple workers
            _ = Crawler("https://example.com", max_workers=8, use_cache=False)

            # Check log content for worker configuration
            content = log_file.read_text()
            assert "max_workers=8" in content

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

    def test_parallel_crawling_path_used(self):
        """Test that parallel crawling path is used when max_workers > 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "parallel_crawl_test.log"
            setup_logging(log_file=str(log_file))

            with patch("requests.Session.get") as mock_get:
                # Mock robots.txt
                robots_response = Mock()
                robots_response.status_code = 404
                robots_response.text = ""

                # Mock page responses
                page_response = Mock()
                page_response.status_code = 200
                page_response.text = "<html><body><h1>Test</h1></body></html>"

                mock_get.side_effect = [robots_response, page_response]

                crawler = Crawler(
                    "https://example.com", max_pages=1, max_workers=2, use_cache=False
                )
                results = list(crawler.crawl())

                assert len(results) == 1

                # Check that parallel crawling log message appears
                content = log_file.read_text()
                assert "Using parallel crawling with 2 workers" in content

    def test_sequential_crawling_path_used(self):
        """Test that sequential crawling path is used when max_workers = 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "sequential_crawl_test.log"
            setup_logging(log_file=str(log_file))

            with patch("requests.Session.get") as mock_get:
                # Mock robots.txt
                robots_response = Mock()
                robots_response.status_code = 404
                robots_response.text = ""

                # Mock page response
                page_response = Mock()
                page_response.status_code = 200
                page_response.text = "<html><body><h1>Test</h1></body></html>"

                mock_get.side_effect = [robots_response, page_response]

                crawler = Crawler(
                    "https://example.com", max_pages=1, max_workers=1, use_cache=False
                )
                results = list(crawler.crawl())

                assert len(results) == 1

                # Check that parallel crawling log message does NOT appear
                content = log_file.read_text()
                assert "Using parallel crawling" not in content
