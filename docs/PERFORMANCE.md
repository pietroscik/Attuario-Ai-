# Performance and Scalability Improvements

This document describes the performance optimizations added to the Attuario-AI crawler in Issue #7.

## Features

### 1. HTTP Response Caching

The crawler now caches HTTP responses using `requests-cache` to avoid redundant downloads.

**Benefits:**
- Faster repeated crawls of the same domain
- Reduced network bandwidth usage
- Lower load on target servers

**Configuration:**
- **Default:** Caching enabled with 1-hour expiration
- **Cache backend:** SQLite (`.attuario_cache.sqlite`)
- **Disable:** Use `--no-cache` CLI flag or `use_cache=False` parameter

**Example:**
```python
from attuario_ai import Crawler

# With caching (default)
crawler = Crawler("https://example.com")

# Without caching
crawler = Crawler("https://example.com", use_cache=False)
```

**CLI:**
```bash
# With caching (default)
python scripts/run_pipeline.py https://example.com

# Without caching
python scripts/run_pipeline.py https://example.com --no-cache
```

### 2. Parallel Crawling

The crawler can now fetch multiple pages concurrently using `ThreadPoolExecutor`.

**Benefits:**
- Faster crawling of large datasets
- Better utilization of network I/O
- Configurable parallelism level

**Configuration:**
- **Default:** 4 parallel workers
- **Sequential mode:** Set `max_workers=1`
- **Custom parallelism:** Set `max_workers=N` (recommended: 2-8)

**Example:**
```python
from attuario_ai import Crawler

# With 4 parallel workers (default)
crawler = Crawler("https://example.com")

# With 8 parallel workers
crawler = Crawler("https://example.com", max_workers=8)

# Sequential (no parallelization)
crawler = Crawler("https://example.com", max_workers=1)
```

**CLI:**
```bash
# With 4 workers (default)
python scripts/run_pipeline.py https://example.com

# With 8 workers
python scripts/run_pipeline.py https://example.com --max-workers 8

# Sequential
python scripts/run_pipeline.py https://example.com --max-workers 1
```

### 3. Crawl Depth Control

The crawler respects the `--max-depth` parameter for BFS crawling.

**Configuration:**
- **Default:** 1 level
- **Custom depth:** Set via `--max-depth N` CLI flag or `max_depth=N` parameter

**Example:**
```python
from attuario_ai import Crawler

# Crawl only the starting page
crawler = Crawler("https://example.com", max_depth=0)

# Crawl starting page and direct links (default)
crawler = Crawler("https://example.com", max_depth=1)

# Crawl 3 levels deep
crawler = Crawler("https://example.com", max_depth=3)
```

**CLI:**
```bash
# Default depth (1)
python scripts/run_pipeline.py https://example.com

# Custom depth
python scripts/run_pipeline.py https://example.com --max-depth 3
```

## Performance Characteristics

### When to use caching:
- ✅ Development and testing
- ✅ Repeated crawls of the same domain
- ✅ When target content changes infrequently
- ❌ When you need fresh data every time
- ❌ When crawling different domains each time

### When to use parallelization:
- ✅ Crawling many pages (`--max-pages` > 10)
- ✅ High-latency networks
- ✅ Target servers with good concurrency support
- ❌ Low `--max-pages` values (< 5)
- ❌ When target server has strict rate limits
- ❌ When `--delay` is very high (> 2 seconds)

### Optimal configurations:

**Small crawl (< 10 pages):**
```bash
python scripts/run_pipeline.py https://example.com \
  --max-pages 5 \
  --max-workers 2 \
  --delay 0.5
```

**Medium crawl (10-50 pages):**
```bash
python scripts/run_pipeline.py https://example.com \
  --max-pages 25 \
  --max-workers 4 \
  --delay 0.2
```

**Large crawl (50+ pages):**
```bash
python scripts/run_pipeline.py https://example.com \
  --max-pages 100 \
  --max-workers 8 \
  --delay 0.1
```

## Backward Compatibility

All existing code continues to work without modification:
- Caching is enabled by default (can be disabled)
- Parallelization is enabled by default (can be disabled with `--max-workers 1`)
- Existing parameters (`--max-pages`, `--max-depth`, `--delay`) work as before

## Testing

The implementation includes comprehensive tests:
- Caching configuration tests
- Parallel vs. sequential crawling tests
- Integration with existing crawler tests
- All 74 tests passing

Run tests:
```bash
pytest -v
```

## Troubleshooting

### Cache not working:
- Check if `.attuario_cache.sqlite` file exists
- Verify `use_cache=True` (default)
- Clear cache: `rm .attuario_cache*`

### Parallel crawling not working:
- Check `max_workers` parameter (must be > 1)
- Check logs for "Using parallel crawling with N workers" message
- Verify you have enough pages to crawl (`max_pages` > 1)

### Performance not improving:
- Increase `max_workers` for parallelization
- Decrease `--delay` if target server allows
- Use caching for repeated crawls
- Ensure adequate network bandwidth
