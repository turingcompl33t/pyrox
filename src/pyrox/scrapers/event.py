"""
Scrape events from the events page.
"""

import logging
from datetime import datetime

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from pyrox.config import BASE_URL
from pyrox.models import Event

from .base import BaseScraper


class EventScraper(BaseScraper):
    """A class for scraping events."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def scrape(self, soup: BeautifulSoup) -> list[Event]:
        """
        Scrape and parse events.
        :return: The collection of events
        """
        # find all of the card elements for each event on the page
        cards = [a for a in soup.find_all("a") if a["href"].startswith("/event/")]  # type: ignore
        self.logger.info(f"found {len(cards)} event cards")

        events: list[Event] = []
        for card in cards:
            name = _parse_name(card.find("h2"))
            link = _parse_link(card)  # type: ignore

            if name is not None and link is not None:
                events.append(
                    Event(name=name, date=datetime(year=2025, month=1, day=1), url=link)
                )

        return events


def _parse_name(tag: Tag | None) -> str | None:
    """
    Parse a name from a tag.
    :param tag: The input tag
    :return: The parsed name, or `None`
    """
    return tag.text if tag is not None else None


def _parse_link(tag: Tag | None) -> HttpUrl | None:
    """
    Parse a link from a tag.
    :param tag: The input tag
    :return: The parsed link, or `None`
    """
    return HttpUrl(f"{BASE_URL}/{tag['href']}") if tag is not None else None
