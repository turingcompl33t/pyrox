"""
Hyrox results client.
"""

import logging

import requests
from bs4 import BeautifulSoup

from pyrox.objects import Event
from pyrox.scrapers.event import EventScraper


class Hyrox:
    """A client for Hyrox results from hyresult.com."""

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.logger = logger

    def events(self) -> list[Event]:
        """
        Get all events.
        :return: A list of events
        """
        res = requests.get("https://www.hyresult.com/events?tab=all")
        res.raise_for_status()

        scraper = EventScraper(self.logger)
        return scraper.scrape(BeautifulSoup(res.content, "html.parser"))
