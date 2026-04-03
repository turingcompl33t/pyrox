"""
Scrape events from an events page.
"""

import logging

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
        # event cards contain an HREF to event page that starts with the
        # season identifier for the event - this is somewhat brittle...
        anchors = soup.find_all(
            "a", href=lambda h: h is not None and h.startswith("/event/s")
        )
        self.logger.debug(f"found {len(anchors)} event cards")

        events: list[Event] = []
        for anchor in anchors:
            name = _parse_name(anchor.find("h2"))
            link = _parse_link(anchor)

            if name is not None and link is not None:
                events.append(Event(name=name, url=link))

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
    # the relative link includes a leading '/'
    return HttpUrl(f"{BASE_URL}{tag['href']}") if tag is not None else None
