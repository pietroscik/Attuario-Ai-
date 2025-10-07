# Logging and Robustness Features

## Overview

The Attuario AI pipeline now includes comprehensive logging and robustness improvements to increase reliability and traceability.

## Features

### 1. Logging System

The pipeline uses Python's standard `logging` module with three levels:

- **INFO**: General information about the crawling and parsing process
- **WARNING**: Non-critical issues that should be noted (e.g., timeouts, missing metadata)
- **ERROR**: Critical errors that prevent normal operation

### 2. Dual Output

Logs are written to two destinations simultaneously:

- **Console**: Simple format for real-time monitoring
  ```
  INFO: Starting crawl
  WARNING: Timeout fetching https://example.com
  ERROR: Failed to parse page
  ```

- **File (logs/pipeline.log)**: Detailed format with timestamps and module names
  ```
  2025-10-07 21:12:05 - attuario_ai.crawler - INFO - Starting crawl
  2025-10-07 21:12:06 - attuario_ai.crawler - WARNING - Timeout fetching https://example.com
  2025-10-07 21:12:07 - attuario_ai.parser - ERROR - Failed to parse page
  ```

### 3. Retry Mechanism

Network errors are automatically retried with exponential backoff:

- **Max retries**: 3 attempts
- **Backoff strategy**: Exponential (1s, 2s, 4s)
- **Retriable errors**:
  - `requests.Timeout`: Request exceeded timeout limit
  - `requests.ConnectionError`: Network connectivity issues
- **Non-retriable errors**:
  - `requests.HTTPError`: HTTP 4xx/5xx status codes (logged but not retried)

### 4. Error Handling

All network operations are wrapped in try/except blocks with specific exception handling:

```python
try:
    response = self._session.get(url, timeout=self.timeout)
    response.raise_for_status()
except requests.Timeout as exc:
    logger.warning(f"Timeout fetching {url}")
except requests.ConnectionError as exc:
    logger.warning(f"Connection error fetching {url}")
except requests.HTTPError as exc:
    logger.error(f"HTTP error {exc.response.status_code}")
```

## Usage

### Basic Usage

The logging system is automatically enabled when you import and use the pipeline:

```python
from attuario_ai import setup_logging, Crawler, PageParser

# Setup logging
setup_logging()

# Use the crawler (logging is automatic)
crawler = Crawler("https://example.com")
results = list(crawler.crawl())
```

### Custom Log File

You can specify a custom log file location:

```python
setup_logging(log_file="my_logs/custom.log")
```

### CLI Usage

The `run_pipeline.py` script automatically sets up logging:

```bash
python scripts/run_pipeline.py https://www.attuario.eu --max-pages 50
```

Specify a custom log file:

```bash
python scripts/run_pipeline.py https://www.attuario.eu --log-file custom.log
```

### Custom Log Levels

Control the verbosity of logging:

```python
import logging
from attuario_ai import setup_logging

# More verbose file logging
setup_logging(log_level=logging.DEBUG)

# Less verbose console output
setup_logging(console_level=logging.WARNING)
```

## What Gets Logged

### Crawler Module

- Initialization parameters (max_pages, max_depth, delay)
- robots.txt fetch attempts and results
- Crawl start/completion
- Each page fetch attempt
- Network errors and retries
- URL filtering by robots.txt

### Parser Module

- Page parsing start
- Warnings for missing title or content
- Successful parsing with title preview
- Parsing errors with full exception details

## Example Output

### Console Output

```
INFO: Logging configured. Writing to logs/pipeline.log
INFO: Initializing crawler for https://www.attuario.eu
INFO: Config: max_pages=50, max_depth=2, delay=0.5s
INFO: Successfully fetched robots.txt from https://www.attuario.eu/robots.txt
INFO: Adjusted delay to 1.0s based on robots.txt
INFO: Starting crawl
INFO: Successfully crawled [1/50]: https://www.attuario.eu/
INFO: Parsing page: https://www.attuario.eu/
INFO: Successfully parsed page: https://www.attuario.eu/ (title: Attuario.eu - Home...)
WARNING: Timeout fetching https://www.attuario.eu/old-page (attempt 1/3)
INFO: Retry attempt 2/3 for https://www.attuario.eu/old-page after 1.0s
INFO: Successfully fetched https://www.attuario.eu/old-page on retry attempt 2
INFO: Crawl completed. Total pages crawled: 50
```

### Log File Content

```
2025-10-07 21:12:00 - root - INFO - Logging configured. Writing to logs/pipeline.log
2025-10-07 21:12:00 - attuario_ai.crawler - INFO - Initializing crawler for https://www.attuario.eu
2025-10-07 21:12:00 - attuario_ai.crawler - INFO - Config: max_pages=50, max_depth=2, delay=0.5s
2025-10-07 21:12:00 - attuario_ai.crawler - INFO - Successfully fetched robots.txt from https://www.attuario.eu/robots.txt
2025-10-07 21:12:00 - attuario_ai.crawler - INFO - Adjusted delay to 1.0s based on robots.txt
2025-10-07 21:12:01 - attuario_ai.crawler - INFO - Starting crawl
2025-10-07 21:12:02 - attuario_ai.crawler - INFO - Successfully crawled [1/50]: https://www.attuario.eu/
2025-10-07 21:12:02 - attuario_ai.parser - INFO - Parsing page: https://www.attuario.eu/
2025-10-07 21:12:02 - attuario_ai.parser - INFO - Successfully parsed page: https://www.attuario.eu/ (title: Attuario.eu - Home...)
2025-10-07 21:12:03 - attuario_ai.crawler - WARNING - Timeout fetching https://www.attuario.eu/old-page (attempt 1/3)
2025-10-07 21:12:04 - attuario_ai.crawler - INFO - Retry attempt 2/3 for https://www.attuario.eu/old-page after 1.0s
2025-10-07 21:12:06 - attuario_ai.crawler - INFO - Successfully fetched https://www.attuario.eu/old-page on retry attempt 2
2025-10-07 21:12:30 - attuario_ai.crawler - INFO - Crawl completed. Total pages crawled: 50
```

## Troubleshooting

### Log File Not Created

Ensure the parent directory exists or that the application has write permissions:

```python
from pathlib import Path
Path("logs").mkdir(exist_ok=True)
```

### Too Verbose

Reduce console logging level:

```python
import logging
setup_logging(console_level=logging.WARNING)
```

### Log File Growing Too Large

Implement log rotation (for advanced users):

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/pipeline.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## Testing

The logging functionality includes comprehensive tests:

```bash
# Run logging tests
python -m pytest tests/test_logging.py -v

# Run crawler logging integration tests
python -m pytest tests/test_crawler_logging.py -v
```

## Benefits

1. **Traceability**: Complete audit trail of crawling activities
2. **Debugging**: Easy identification of problematic URLs or network issues
3. **Monitoring**: Real-time visibility into pipeline progress
4. **Reliability**: Automatic retry of transient network failures
5. **Production Ready**: Proper error handling for production deployments
