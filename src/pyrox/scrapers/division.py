"""
Scrape division information from an event page.
"""

import logging

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl, ValidationError

from pyrox.config import BASE_URL
from pyrox.objects import Division, DivisionName

from .base import BaseScraper


class DivisionScraper(BaseScraper):
    """A class for scraping events."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def scrape(self, soup: BeautifulSoup) -> list[Division]:
        """
        Scrape and parse divisions.
        :return: The collection of divisions
        """
        # find all of the row elements
        rows = soup.find_all("tr", class_="border-b")
        if len(rows) < 2:
            return []

        # the first row is the table header
        divisions: list[Division] = []
        for row in rows[1:]:
            try:
                divisions.append(_parse_row(row))
            except (ValueError, ValidationError):
                self.logger.warning("failed to parse division from row")
                continue
        return divisions


def _parse_row(tag: Tag) -> Division:
    """
    Parse a division from a row of the page.
    :param tag: The input tag
    :return: The parsed division
    """
    data = tag.find_all("td")
    if len(data) != 3:
        raise ValueError("cannot parse division from row; missing data")
    return Division(
        name=_parse_name(data[0]),
        n_finishers=_parse_n_finishers(data[1]),
        url=_parse_link(data[2]),
    )


def _parse_name(tag: Tag) -> DivisionName:
    """Parse the division name from the tag in which it appears."""
    parts: list[str] = tag.text.split()

    in_name: list[str] = []
    # the first part is always 'HYROX', skip it
    for p in parts[1:]:
        in_name.append(p)

        # the last part of the division name is always the gender
        if p in {"MEN", "WOMEN", "MIXED"}:
            break

    return DivisionName("_".join(in_name).lower())


def _parse_n_finishers(tag: Tag) -> int:
    """Parse the number of finishers from the tag in which it appears."""
    return int(tag.text.strip())


def _parse_link(tag: Tag) -> HttpUrl:
    """Parse the results URL from the tag in which it appears."""
    a = tag.find("a")
    if a is None:
        raise ValueError("missing anchor tag")
    return HttpUrl(f"{BASE_URL}{a['href']}")
