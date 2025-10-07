"""Feature extraction helpers for actuarial content analysis."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List

ACTUARIAL_TERMS = {
    "solvency",
    "solvency ii",
    "ivass",
    "eiopa",
    "riserva",
    "best estimate",
    "premio",
    "longevità",
    "mortalità",
    "stress test",
    "discount rate",
    "best estimate",
    "risk margin",
    "scr",
    "bscr",
    "premio puro",
    "var",
    "value at risk",
    "tasso tecnico",
    "attuario",
    "riserva matematica",
}

FORMULA_PATTERNS = [
    re.compile(r"\\begin\{equation\}"),
    re.compile(r"\\\[(.*?)\\\]", re.DOTALL),
    re.compile(r"[=\u2260\u2264\u2265]"),
]

CITATION_PATTERNS = [
    re.compile(
        r"\b(?:ivass|eiopa|isvap|solvency\s*ii|european insurance)\b", re.IGNORECASE
    ),
    re.compile(r"\bregolament[oi]|circolare|normativa\b", re.IGNORECASE),
]


@dataclass
class PageMetrics:
    """Aggregated metrics extracted from a parsed page.

    This class contains various metrics used to assess the quality and
    characteristics of actuarial content on a page.

    Attributes:
        word_count: Total number of words in the page text.
        actuarial_terms: Dictionary mapping actuarial terms to their occurrence counts.
        numeric_tokens: Count of numeric values found in the text.
        has_formula: Whether the page contains mathematical formulas.
        has_table: Whether the page contains HTML tables.
        has_list: Whether the page contains HTML lists (ordered or unordered).
        citation_matches: Count of regulatory citations found.
        example_values: Sample of numeric values extracted from the text (up to 20).
    """

    word_count: int
    actuarial_terms: Dict[str, int]
    numeric_tokens: int
    has_formula: bool
    has_table: bool
    has_list: bool
    citation_matches: int
    example_values: List[float]

    def to_dict(self) -> Dict[str, object]:
        """Convert metrics to a dictionary for serialization.

        Returns:
            Dictionary containing all metrics.
        """
        return {
            "word_count": self.word_count,
            "actuarial_terms": self.actuarial_terms,
            "numeric_tokens": self.numeric_tokens,
            "has_formula": self.has_formula,
            "has_table": self.has_table,
            "has_list": self.has_list,
            "citation_matches": self.citation_matches,
            "example_values": self.example_values,
        }


def extract_metrics(parsed_text: str, html: str) -> PageMetrics:
    """Extract various metrics from parsed text and HTML content.

    Analyzes the page content to extract metrics relevant to actuarial content
    quality assessment, including word counts, actuarial terminology usage,
    numeric data presence, and structural elements.

    Args:
        parsed_text: Plain text extracted from the HTML page.
        html: Raw HTML content of the page.

    Returns:
        PageMetrics object containing all extracted metrics.
    """
    lower_text = parsed_text.lower()
    words = re.findall(r"\b\w+\b", lower_text)
    word_count = len(words)

    actuarial_counter: Counter[str] = Counter()
    for term in ACTUARIAL_TERMS:
        if term in lower_text:
            actuarial_counter[term] = lower_text.count(term)

    numeric_tokens = len(re.findall(r"\b\d+(?:[.,]\d+)?\b", parsed_text))
    example_values = [
        float(token.replace(",", "."))
        for token in re.findall(r"\b\d+(?:[.,]\d+)?\b", parsed_text)[:20]
    ]

    has_formula = any(pattern.search(parsed_text) for pattern in FORMULA_PATTERNS)
    has_table = "<table" in html.lower()
    has_list = "<ul" in html.lower() or "<ol" in html.lower()

    citation_matches = sum(
        pattern.findall(parsed_text).__len__() for pattern in CITATION_PATTERNS
    )

    return PageMetrics(
        word_count=word_count,
        actuarial_terms=dict(actuarial_counter),
        numeric_tokens=numeric_tokens,
        has_formula=has_formula,
        has_table=has_table,
        has_list=has_list,
        citation_matches=citation_matches,
        example_values=example_values,
    )
