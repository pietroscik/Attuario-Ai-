"""Tests for logging configuration."""

import logging
import tempfile
from pathlib import Path

from attuario_ai.logging_config import setup_logging


class TestLoggingConfig:
    """Tests for logging configuration."""

    def test_setup_logging_creates_log_file(self):
        """Test that setup_logging creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(log_file=str(log_file))

            # Log a test message
            logger = logging.getLogger("test_logger")
            logger.info("Test message")

            # Verify log file exists and contains the message
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content
            assert "INFO" in content

    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates the logs directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "nested" / "dir" / "test.log"
            setup_logging(log_file=str(log_file))

            # Verify directory was created
            assert log_file.parent.exists()
            assert log_file.exists()

    def test_logging_levels(self):
        """Test that different logging levels are captured correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "levels.log"
            setup_logging(log_file=str(log_file), log_level=logging.DEBUG)

            logger = logging.getLogger("test_levels")
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            content = log_file.read_text()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content

    def test_default_log_file_location(self):
        """Test that default log file is logs/pipeline.log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to tmpdir to avoid creating logs in repo
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                setup_logging()

                expected_log = Path("logs/pipeline.log")
                assert expected_log.exists()

                logger = logging.getLogger("test_default")
                logger.info("Default location test")

                content = expected_log.read_text()
                assert "Default location test" in content
            finally:
                os.chdir(original_cwd)
