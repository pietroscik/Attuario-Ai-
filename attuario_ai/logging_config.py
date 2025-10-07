"""Logging configuration for the Attuario AI pipeline."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    console_level: int = logging.INFO,
) -> None:
    """Configure logging for the application.

    Sets up logging to write to both console and file with appropriate formatting.

    Args:
        log_file: Path to the log file. If None, uses 'logs/pipeline.log'.
        log_level: Logging level for the file handler.
        console_level: Logging level for the console handler.
    """
    if log_file is None:
        log_file = "logs/pipeline.log"

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler with detailed format
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler with simpler format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    logging.info(f"Logging configured. Writing to {log_file}")
