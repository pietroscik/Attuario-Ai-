"""
Simple crawler constrained to a single domain.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Deque, Iterable, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib import robotparser

import requests
import requests_cache
from requests import Response
from bs4 import BeautifulSoup  # import moved to top for efficiency

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Represents a crawled page.

    Attributes:
        url: The URL of the crawled page.
        status_code: HTTP status code of the response.
        html: Raw HTML content of the page.
        fetched_at: Timestamp when the page was fetched.
        referer: The referring URL (optional).
        error: Error message if the fetch failed (optional).
    """

    url: str
    status_code: int
    html: str
    fetched_at: float
    referer: Optional[str] = None
    error: Optional[str] = None


class RobotsPolicy:
    """Utility wrapper around ``robots.txt`` directives for the target domain.

    This class fetches and parses the robots.txt file for a domain to determine
    which URLs can be crawled and what crawl delays should be respected.
    """

    def __init__(
        self,
        base_url: str,
        *,
        session: requests.Session,
        timeout: float,
        user_agent: str,
    ) -> None:
        """Initialize the RobotsPolicy.

        Args:
            base_url: The base URL of the domain.
            session: Requests session to use for fetching robots.txt.
            timeout: Timeout for HTTP requests in seconds.
            user_agent: User-Agent string to identify the crawler.
        """
        self.user_agent = user_agent
        self._parser = robotparser.RobotFileParser()
        self._available = False
        self.crawl_delay: Optional[float] = None
        self.sitemaps: tuple[str, ...] = ()

        robots_url = urljoin(base_url.rstrip("/"), "/robots.txt")
        try:
            response = session.get(robots_url, timeout=timeout)
            if response.status_code < 400 and response.text.strip():
                self._parser.parse(response.text.splitlines())
                self._available = True
                self.crawl_delay = self._parser.crawl_delay(
                    user_agent
                ) or self._parser.crawl_delay("*")
                sitemaps = self._parser.site_maps() or []
                self.sitemaps = tuple(sitemaps)
                logger.info(f"Successfully fetched robots.txt from {robots_url}")
                if self.crawl_delay:
                    logger.info(f"Crawl delay from robots.txt: {self.crawl_delay}s")
        except requests.RequestException as exc:
            self._available = False
            logger.warning(f"Failed to fetch robots.txt from {robots_url}: {exc}")

    def is_allowed(self, url: str) -> bool:
        """Check if the given URL is allowed to be crawled.

        Args:
            url: The URL to check.

        Returns:
            True if the URL can be crawled, False otherwise.
        """
        if not self._available:
            return True
        return self._parser.can_fetch(self.user_agent, url)


class Crawler:
    """Breadth-first crawler restricted to a target domain that respects robots.txt.

    This crawler performs a breadth-first search (BFS) traversal of web pages
    starting from a base URL, staying within the same domain. It respects
    robots.txt directives and implements polite crawling with configurable delays.

    Attributes:
        base_url: The starting URL for the crawl.
        max_pages: Maximum number of pages to crawl.
        max_depth: Maximum link depth from the starting URL.
        delay_seconds: Delay between requests in seconds.
        timeout: Timeout for HTTP requests in seconds.
    """

    def __init__(
        self,
        base_url: str,
        *,
        max_pages: int = 100,
        max_depth: int = 2,
        delay_seconds: float = 0.5,
        session: Optional[requests.Session] = None,
        timeout: float = 10.0,
        user_agent: str = "AttuarioAI/0.1 (+https://github.com)",
        use_cache: bool = True,
        cache_expire_after: int = 3600,
        max_workers: int = 4,
    ) -> None:
        """
        Initialize the crawler.

        Args:
            base_url (str): The starting URL for the crawl.
            max_pages (int, optional): Maximum number of pages to crawl. Defaults to 100.
            max_depth (int, optional): Maximum depth for crawling. Defaults to 2.
            delay_seconds (float, optional): Delay between requests in seconds. Defaults to 0.5.
            session (requests.Session, optional): Custom requests session. Defaults to None.
            timeout (float, optional): Timeout for HTTP requests in seconds. Defaults to 10.0.
            user_agent (str, optional): The User-Agent string sent with HTTP requests.
                This identifies the crawler to web servers and is used for robots.txt compliance.
                Defaults to "AttuarioAI/0.1 (+https://github.com)".
            use_cache (bool, optional): Enable caching of HTTP responses. Defaults to True.
            cache_expire_after (int, optional): Cache expiration time in seconds. Defaults to 3600.
            max_workers (int, optional): Maximum number of parallel workers for fetching.
                Defaults to 4. Set to 1 to disable parallelization.
        """
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.max_workers = max_workers

        # Setup session with optional caching
        if session is None:
            if use_cache:
                self._session = requests_cache.CachedSession(
                    cache_name=".attuario_cache",
                    backend="sqlite",
                    expire_after=cache_expire_after,
                )
                logger.info(
                    f"HTTP caching enabled (expire_after={cache_expire_after}s)"
                )
            else:
                self._session = requests.Session()
        else:
            self._session = session

        self._session.headers.setdefault("User-Agent", user_agent)

        parsed = urlparse(self.base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid base_url: {base_url}")
        self._netloc = parsed.netloc

        logger.info(f"Initializing crawler for {self.base_url}")
        logger.info(
            f"Config: max_pages={max_pages}, max_depth={max_depth}, "
            f"delay={delay_seconds}s, max_workers={max_workers}"
        )

        self._robots = RobotsPolicy(
            self.base_url,
            session=self._session,
            timeout=self.timeout,
            user_agent=self._session.headers["User-Agent"],
        )
        if self._robots.crawl_delay:
            self.delay_seconds = max(self.delay_seconds, self._robots.crawl_delay)
            logger.info(f"Adjusted delay to {self.delay_seconds}s based on robots.txt")

    def close(self) -> None:
        """Close the HTTP session and release resources."""
        self._session.close()

    def crawl(self, seeds: Optional[Iterable[str]] = None) -> Iterable[CrawlResult]:
        """Perform breadth-first crawl starting from seed URLs.

        Args:
            seeds: Optional list of seed URLs to start from. If None, uses base_url.

        Yields:
            CrawlResult objects for each successfully fetched page.
        """
        logger.info("Starting crawl")
        queue: Deque[tuple[str, int, Optional[str]]] = deque()
        visited: Set[str] = set()
        if seeds is None:
            queue.append((self.base_url, 0, None))
        else:
            for seed in seeds:
                queue.append((seed, 0, None))

        pages_crawled = 0

        # Use parallel fetching if max_workers > 1
        if self.max_workers > 1:
            yield from self._crawl_parallel(queue, visited, pages_crawled)
        else:
            yield from self._crawl_sequential(queue, visited, pages_crawled)

    def _crawl_sequential(
        self,
        queue: Deque[tuple[str, int, Optional[str]]],
        visited: Set[str],
        pages_crawled: int,
    ) -> Iterable[CrawlResult]:
        """Sequential crawling (original implementation)."""
        while queue and pages_crawled < self.max_pages:
            url, depth, referer = queue.popleft()
            normalized = self._normalize_url(url)
            if not self._robots.is_allowed(normalized):
                logger.info(f"URL disallowed by robots.txt: {normalized}")
                continue
            visited.add(normalized)
            result = self._fetch(normalized, referer)
            yield result
            pages_crawled += 1

            if result.error:
                logger.warning(f"Error fetching {normalized}: {result.error}")
            else:
                logger.info(
                    f"Successfully crawled [{pages_crawled}/{self.max_pages}]: {normalized}"
                )

            if result.error or depth >= self.max_depth:
                continue

            for link in self._extract_links(result.html, normalized):
                if link not in visited and self._robots.is_allowed(link):
                    queue.append((link, depth + 1, normalized))

        logger.info(f"Crawl completed. Total pages crawled: {pages_crawled}")

    def _crawl_parallel(
        self,
        queue: Deque[tuple[str, int, Optional[str]]],
        visited: Set[str],
        pages_crawled: int,
    ) -> Iterable[CrawlResult]:
        """Parallel crawling using ThreadPoolExecutor."""
        logger.info(f"Using parallel crawling with {self.max_workers} workers")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while queue and pages_crawled < self.max_pages:
                # Collect batch of URLs to fetch
                batch = []
                while (
                    queue
                    and len(batch) < self.max_workers
                    and pages_crawled + len(batch) < self.max_pages
                ):
                    url, depth, referer = queue.popleft()
                    normalized = self._normalize_url(url)
                    if not self._robots.is_allowed(normalized):
                        logger.info(f"URL disallowed by robots.txt: {normalized}")
                        continue
                    if normalized not in visited:
                        visited.add(normalized)
                        batch.append((normalized, depth, referer))

                if not batch:
                    break

                # Submit all URLs in batch for parallel fetching
                future_to_url = {
                    executor.submit(self._fetch, url, referer): (url, depth, referer)
                    for url, depth, referer in batch
                }

                # Process results as they complete
                for future in as_completed(future_to_url):
                    url, depth, referer = future_to_url[future]
                    try:
                        result = future.result()
                        yield result
                        pages_crawled += 1

                        if result.error:
                            logger.warning(f"Error fetching {url}: {result.error}")
                        else:
                            logger.info(
                                f"Successfully crawled [{pages_crawled}/{self.max_pages}]: {url}"
                            )

                        # Extract links only if no error and depth allows
                        if not result.error and depth < self.max_depth:
                            for link in self._extract_links(result.html, url):
                                if link not in visited and self._robots.is_allowed(
                                    link
                                ):
                                    queue.append((link, depth + 1, url))
                    except Exception as exc:
                        logger.error(f"Unexpected error processing {url}: {exc}")

        logger.info(f"Crawl completed. Total pages crawled: {pages_crawled}")

    def _fetch(self, url: str, referer: Optional[str]) -> CrawlResult:
        """Fetch a single URL and return the result.

        Args:
            url: The URL to fetch.
            referer: The referring URL (optional).

        Returns:
            CrawlResult containing the fetched page or error information.
        """
        max_retries = 3
        retry_delay = 1.0  # Initial retry delay in seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    logger.info(
                        f"Retry attempt {attempt + 1}/{max_retries} for {url} after {wait_time}s"
                    )
                    time.sleep(wait_time)

                response: Response = self._session.get(url, timeout=self.timeout)
                response.raise_for_status()
                html = response.text
                status_code = response.status_code
                error = None

                if attempt > 0:
                    logger.info(
                        f"Successfully fetched {url} on retry attempt {attempt + 1}"
                    )

                time.sleep(self.delay_seconds)
                break
            except requests.Timeout as exc:
                html = ""
                status_code = None
                error = f"Timeout: {exc}"
                logger.warning(
                    f"Timeout fetching {url} (attempt {attempt + 1}/{max_retries})"
                )
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to fetch {url} after {max_retries} attempts: {error}"
                    )
            except requests.ConnectionError as exc:
                html = ""
                status_code = None
                error = f"Connection error: {exc}"
                logger.warning(
                    f"Connection error fetching {url} (attempt {attempt + 1}/{max_retries})"
                )
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to fetch {url} after {max_retries} attempts: {error}"
                    )
            except requests.HTTPError as exc:
                html = ""
                status_code = exc.response.status_code if exc.response else None
                error = f"HTTP {status_code}: {exc}"
                logger.error(f"HTTP error fetching {url}: {error}")
                break  # Don't retry on HTTP errors (4xx, 5xx)
            except requests.RequestException as exc:
                html = ""
                status_code = (
                    exc.response.status_code
                    if getattr(exc, "response", None) is not None
                    else None
                )
                error = str(exc)
                logger.error(f"Request error fetching {url}: {error}")
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to fetch {url} after {max_retries} attempts: {error}"
                    )

        return CrawlResult(
            url=url,
            status_code=status_code,
            html=html,
            fetched_at=time.time(),
            referer=referer,
            error=error,
        )

    def _extract_links(self, html: str, current_url: str) -> Set[str]:
        """Extract all valid links from an HTML page.

        Args:
            html: The HTML content to parse.
            current_url: The URL of the current page (for resolving relative links).

        Returns:
            Set of normalized absolute URLs found on the page.
        """
        soup = BeautifulSoup(html, "html.parser")
        links: Set[str] = set()
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if href.startswith("#"):
                continue
            joined = urljoin(current_url, href)
            parsed = urlparse(joined)
            if parsed.netloc == self._netloc and parsed.scheme in {"http", "https"}:
                clean = self._normalize_url(joined)
                links.add(clean)
        return links

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL by removing fragments and trailing slashes.

        Args:
            url: The URL to normalize.

        Returns:
            Normalized URL string.
        """
        parsed = urlparse(url)
        normalized = parsed._replace(fragment="").geturl()
        # Remove trailing slash except for root path
        if (
            normalized.endswith("/")
            and normalized != f"{parsed.scheme}://{parsed.netloc}/"
        ):
            normalized = normalized[:-1]
        return normalized

    def __enter__(self) -> "Crawler":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
