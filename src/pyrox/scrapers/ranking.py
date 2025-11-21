"""
Scrape ranking information from the ranking page.
"""

import logging
from datetime import timedelta

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl, ValidationError

from pyrox.config import BASE_URL
from pyrox.models import AgeGroup, Ranking

from .base import BaseScraper


class RankingScraper(BaseScraper):
    """A class for scraping rankings from an individual race."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def scrape(self, soup: BeautifulSoup) -> list[Ranking]:
        """
        Scrape and parse rankings.
        :return: The collection rankings.
        """
        # find all of the row elements
        rows = soup.find_all("tr", class_="border-t")
        if len(rows) < 2:
            return []

        rankings: list[Ranking] = []
        for row in rows:
            try:
                rankings.append(_parse_row(row))
            except (ValueError, ValidationError):
                self.logger.warning("failed to parse ranking from row")
                continue
        return rankings


def _parse_row(tag: Tag) -> Ranking:
    """
    Parse a ranking from a row of the page.
    :param tag: The input tag
    :return: The parsed ranking
    """
    data = tag.find_all("td")

    if len(data) != 7:
        raise ValueError("cannot parse division from row; missing data")

    return Ranking(
        position=int(data[1].text),
        position_ag=_parse_position_nullable(data[2]),
        name=_parse_name(data[3]),
        age_group=_parse_age_group(data[4]),
        time=_parse_time(data[5]),
        url=_parse_link(data[6]),
    )


def _parse_position_nullable(tag: Tag) -> int | None:
    """Parse the ranking position which may be unparsable."""
    try:
        return int(tag.text)
    except ValueError:
        return None


def _parse_name(tag: Tag) -> str:
    """Parse athlete name from the tag in which it appears."""
    return tag.text


def _parse_age_group(tag: Tag) -> AgeGroup | None:
    """Parse athlete age group from the tag in which it appears."""
    text: str = tag.text
    try:
        return AgeGroup(text.replace("-", "_"))
    except ValueError:
        return None


def _parse_time(tag: Tag) -> timedelta:
    """Parse finish time from the tag in which it appears."""
    parts: list[str] = tag.text.split(":")
    parts = ["0"] + parts if len(parts) < 3 else parts
    return timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))


def _parse_link(tag: Tag) -> HttpUrl:
    """Parse the link to race analysis from the tag in which it appears."""
    a = tag.find("a")
    if a is None:
        raise ValueError("failed to find anchor tag")
    return HttpUrl(f"{BASE_URL}{a['href']}")
