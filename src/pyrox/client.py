"""
Hyrox results client.
"""

import logging

import requests
from bs4 import BeautifulSoup

from pyrox.objects import Division, Event
from pyrox.scrapers.division import DivisionScraper
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

    def divisions(self, event_name: str) -> list[Division]:
        """
        Get the divisions for a particular event.
        :param event_name: The name of the event
        :return: A list of the divisions for the event
        """
        # get all events
        events = self.events()
        # find the event in which the user is interested
        event = next(
            filter(
                lambda e: e.canonical_name == Event.canonicalize(event_name), events
            ),
            None,
        )
        if event is None:
            raise ValueError(f"event with name {event_name} not found")

        # get the content from the event page
        res = requests.get(str(event.url))
        res.raise_for_status()

        # scrape the divisions
        scraper = DivisionScraper(self.logger)
        return scraper.scrape(BeautifulSoup(res.content, "html.parser"))
