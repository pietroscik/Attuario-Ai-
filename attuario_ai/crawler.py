"""Simple crawler constrained to a single domain."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib import robotparser

import requests
from requests import Response


@dataclass
class CrawlResult:
    """Represents a crawled page."""

    url: str
    status_code: int
    html: str
    fetched_at: float
    referer: Optional[str] = None
    error: Optional[str] = None

class RobotsPolicy:
    """Utility wrapper around ``robots.txt``
 directives for the target domain."""

    def __init__(
        self,
        base_url: str,
        *,
        session: requests.Session,
        timeout: float,
        user_agent: str,
    ) -> None:
        self.user_agent = user_agent
        self._parser = robotparser.RobotFileParser()
        self._available = False
        self.crawl_delay: Optional[float] = None
        self.sitemaps: tuple[str, ...] = ()

        robots_url = urljoin(base_url.rstrip("/"),
 "/robots.txt")
        try:
            response = session.get(
robots_url, timeout=timeout)
            if response.status_code < 400 and
 response.text.strip():
                self._parser.parse(
response.text.splitlines())
                self._available = True
                self.crawl_delay = self._parser.crawl_delay(
                    user_agent
                ) or self._parser.crawl_delay("*")
                sitemaps = self._parser.site_maps() or []
                self.sitemaps = tuple(sitemaps)
        except requests.RequestException:
            self._available = False

    def allows(self, url: str) -> bool:
        if not self._available:
            return True
        return self._parser.can_fetch(self.user_agent, url)


class Crawler:
    """Breadth-first crawler restricted to a target domain.

    The crawler respects ``robots.txt`` directives for the target domain.
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
        user_agent:
 str = "AttuarioAI/0.1 (+https://github.com)",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.setdefault(
"User-Agent", user_agent)

        parsed = urlparse(self.base_url)
        if not parsed.scheme
 or not parsed.netloc:
            raise ValueError(
     f"Invalid base_url: {base_url}")
        self._netloc = parsed.netloc

        self._robots = RobotsPolicy(
            self.base_url,
            session=self._session,
            timeout=self.timeout,
            user_agent=self._session.headers["User-Agent"],
        )
        if self._robots.crawl_delay:
            self.delay_seconds = max(
self.delay_seconds, self._robots.crawl_delay)

    def close(self) -> None:
        self._session.close()

    def crawl(self, seeds:
 Optional[Iterable[str]] = None) -> Iterable[CrawlResult]:
        queue:
 Deque[tuple[str, int, Optional[str]]] = deque()
        visited: Set[str] = set()

        if seeds is None:
            queue.append((self.base_url, 0, None))
        else:
            for seed in seeds:
                queue.append((seed, 0, None))

        pages_crawled = 0

        while queue and pages_crawled < self.max_pages:
            url, depth, referer = queue.popleft()
            normalized = self._normalize_url(url)
            if normalized in visited:
                continue
            if not self._robots.allows(normalized):
                continue
            visited.add(normalized)

            result = self._fetch(normalized, referer)
            yield result
            pages_crawled += 1

            if result.error or depth >= self.max_depth:
                continue

            for link in self._extract_links(
result.html, normalized):
                if link not in visited
 and self._robots.allows(link):
                    queue.append((
link, depth + 1, normalized))

            if queue and self.delay_seconds > 0:
                time.sleep(self.delay_seconds)

    def _fetch(
self, url: str, referer: Optional[str]) -> CrawlResult:
        try:
            response:
 Response = self._session.get(url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            status_code = response.status_code
            error = None
        except requests.RequestException as exc:
            html = ""
            status_code = (
                getattr(exc.response, "status_code", 0)
                if hasattr(exc, "response")
                else 0
            )
            error = str(exc)
        return CrawlResult(
            url=url,
            status_code=status_code,
            html=html,
            fetched_at=time.time(),
            referer=referer,
            error=error,
        )

    def _extract_links(
self, html: str, current_url: str) -> Set[str]:
        from bs4 import (
            BeautifulSoup,
        )

        # lazy import to keep dependency optional for non-crawl use

        soup = BeautifulSoup(html, "html.parser")
        links: Set[str] = set()
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if href.startswith("#"):
                continue
            joined = urljoin(current_url, href)
            parsed = urlparse(joined)
            if parsed.netloc == self._netloc and
 parsed.scheme in {"http", "https"}:
                clean = self._normalize_url(joined)
                links.add(clean)
        return links

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = parsed._replace(fragment="").geturl()
        if normalized.endswith("/") and
 normalized != self.base_url:
            normalized = normalized[:-1]
        return normalized

    def __enter__(self) -> "Crawler":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
