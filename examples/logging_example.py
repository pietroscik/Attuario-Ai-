#!/usr/bin/env python3
"""Example demonstrating the logging and robustness features."""

from attuario_ai import Crawler, PageParser, setup_logging

# Setup logging to both console and file
setup_logging(log_file="logs/example.log")

# Create a crawler with retry mechanism
print("\n=== Example: Crawler with Logging and Retry ===\n")

crawler = Crawler(
    "https://httpbin.org",  # Public test API
    max_pages=3,
    max_depth=1,
    delay_seconds=0.5,
)

print("Starting crawl (check logs/example.log for detailed output)...\n")

# Crawl pages - logging happens automatically
results = list(crawler.crawl())

print(f"\nCrawled {len(results)} pages")

# Parse the results - logging happens automatically
parser = PageParser()
for result in results:
    if result.html and not result.error:
        parsed = parser.parse(result.url, result.html, result.fetched_at)
        print(f"✓ Parsed: {parsed.url} (title: {parsed.title[:50]}...)")
    elif result.error:
        print(f"✗ Error: {result.url} - {result.error}")

print("\n✓ Example completed. Check logs/example.log for detailed logging output.\n")
