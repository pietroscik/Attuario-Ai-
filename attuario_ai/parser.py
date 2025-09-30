"""HTML parsing and content normalization utilities."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, Optional

from bs4 import BeautifulSoup


@dataclass
class ParsedPage:
    """Structured representation of an HTML page."""

    url: str
    title: str
    text: str
    html: str
    fetched_at: dt.datetime
    metadata: Dict[str, Optional[str]]


class PageParser:
    """Parses raw HTML into structured text and metadata."""

    def __init__(self, *, language: str = "it") -> None:
        self.language = language

    def parse(self, url: str, html: str, fetched_at: float) -> ParsedPage:
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        main = self._select_main_content(soup)
        text = main.get_text("\n", strip=True)

        metadata = {
            "language": self.language,
            "title": title,
            "description": self._meta_content(soup, "description"),
            "published": self._find_datetime(soup, "article:published_time"),
            "modified": self._find_datetime(soup, "article:modified_time"),
            "author": self._meta_content(soup, "author"),
        }

        return ParsedPage(
            url=url,
            title=title,
            text=text,
            html=html,
            fetched_at=dt.datetime.fromtimestamp(fetched_at, tz=dt.timezone.utc),
            metadata=metadata,
        )

    def _select_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
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
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    def _find_datetime(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"property": property_name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            return time_tag["datetime"].strip()
        return None
