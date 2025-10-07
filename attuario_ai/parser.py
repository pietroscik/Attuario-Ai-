"""HTML parsing and content normalization utilities."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    """Structured representation of an HTML page.

    Attributes:
        url: The URL of the page.
        title: The page title extracted from the <title> tag.
        text: Extracted plain text content from the main content area.
        html: Original HTML content.
        fetched_at: Datetime when the page was fetched.
        metadata: Dictionary containing page metadata (language, description, dates, author).
    """

    url: str
    title: str
    text: str
    html: str
    fetched_at: dt.datetime
    metadata: Dict[str, Optional[str]]


class PageParser:
    """Parses raw HTML into structured text and metadata.

    This parser extracts the main content from HTML pages, extracts metadata
    such as title, description, publication dates, and author information.

    Attributes:
        language: The expected language of the content (default: "it" for Italian).
    """

    def __init__(self, *, language: str = "it") -> None:
        """Initialize the parser.

        Args:
            language: The expected language code (default: "it").
        """
        self.language = language

    def parse(self, url: str, html: str, fetched_at: float) -> ParsedPage:
        """Parse HTML into a structured ParsedPage object.

        Args:
            url: The URL of the page being parsed.
            html: Raw HTML content.
            fetched_at: Unix timestamp of when the page was fetched.

        Returns:
            ParsedPage object containing extracted text and metadata.
        """
        logger.info(f"Parsing page: {url}")

        try:
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            if not title:
                logger.warning(f"No title found for page: {url}")

            main = self._select_main_content(soup)
            text = main.get_text("\n", strip=True)

            if not text:
                logger.warning(f"No text content found for page: {url}")

            metadata = {
                "language": self.language,
                "title": title,
                "description": self._meta_content(soup, "description"),
                "published": self._find_datetime(soup, "article:published_time"),
                "modified": self._find_datetime(soup, "article:modified_time"),
                "author": self._meta_content(soup, "author"),
            }

            logger.info(f"Successfully parsed page: {url} (title: {title[:50]}...)")

            return ParsedPage(
                url=url,
                title=title,
                text=text,
                html=html,
                fetched_at=dt.datetime.fromtimestamp(fetched_at, tz=dt.timezone.utc),
                metadata=metadata,
            )
        except Exception as exc:
            logger.error(f"Error parsing page {url}: {exc}")
            raise

    def _select_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Select the main content area from the page.

        Searches for common content containers (article, main, div, body)
        and returns the one with the most text content.

        Args:
            soup: BeautifulSoup object representing the parsed HTML.

        Returns:
            BeautifulSoup object representing the main content area.
        """
        candidates = []
        for selector in ("article", "main", "div", "body"):
            node = soup.find(selector)
            if node:
                candidates.append((len(node.get_text()), node))
        if not candidates:
            return soup
        _, best = max(candidates, key=lambda pair: pair[0])
        return best

    def _meta_content(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Extract content from a meta tag by name.

        Args:
            soup: BeautifulSoup object representing the parsed HTML.
            name: The name attribute of the meta tag to find.

        Returns:
            The content attribute value, or None if not found.
        """
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    def _find_datetime(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Find datetime information from meta tags or time elements.

        Args:
            soup: BeautifulSoup object representing the parsed HTML.
            property_name: The property attribute of the meta tag to search for.

        Returns:
            ISO format datetime string, or None if not found.
        """
        tag = soup.find("meta", attrs={"property": property_name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            return time_tag["datetime"].strip()
        return None
