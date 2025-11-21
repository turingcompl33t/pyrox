"""
Hyrox results client.
"""

from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

import pyrox.models as models
from pyrox.scrapers.division import DivisionScraper
from pyrox.scrapers.event import EventScraper
from pyrox.scrapers.ranking import RankingScraper


class Event(BaseModel):
    """A Hyrox event."""

    # the event data model
    model: models.Event

    def divisions(self) -> list[Division]:
        """
        List the divisions for an event.
        :return: The list of divisions for the event
        """
        # get the content from the event page
        res = requests.get(str(self.model.url))
        res.raise_for_status()

        # scrape the divisions
        scraper = DivisionScraper(logging.getLogger(__name__))
        return [
            Division(model=d)
            for d in scraper.scrape(BeautifulSoup(res.content, "html.parser"))
        ]


class Division(BaseModel):
    """A hyrox division."""

    # the division data model
    model: models.Division

    def rankings(self) -> list[Ranking]:
        """
        List the rankings for a division.
        :return: The list of rankings
        """
        p = 1
        s = RankingScraper(logging.getLogger(__name__))

        rankings: list[Ranking] = []
        while True:
            res = requests.get(f"{self.model.url}?p={p}")
            res.raise_for_status()

            scraped = s.scrape(BeautifulSoup(res.content, "html.parser"))
            if len(scraped) == 0:
                break

            rankings.extend([Ranking(model=r) for r in scraped])
            p += 1

        return rankings


class Ranking(BaseModel):
    """A Hyrox ranking."""

    # ranking data model
    model: models.Ranking


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
        return [
            Event(model=e)
            for e in scraper.scrape(BeautifulSoup(res.content, "html.parser"))
        ]

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
                lambda e: e.model.canonical_name
                == models.Event.canonicalize(event_name),
                events,
            ),
            None,
        )
        if event is None:
            raise ValueError(f"event with name {event_name} not found")

        return event.divisions()
