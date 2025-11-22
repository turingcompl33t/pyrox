"""
Hyrox results client.
"""

from __future__ import annotations

import logging
import time

import requests
from bs4 import BeautifulSoup

import pyrox.models as models
from pyrox.scrapers.division import DivisionScraper
from pyrox.scrapers.event import EventScraper
from pyrox.scrapers.result import ResultScraper
from pyrox.scrapers.splits import SplitsScraper


class Hyrox:
    """A client for Hyrox results from hyresult.com."""

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.logger = logger

    def events(self) -> list[Event]:
        """
        Get all events.
        :return: A list of events
        """
        self.logger.info("fetching all events")

        res = requests.get("https://www.hyresult.com/events?tab=all")
        res.raise_for_status()

        scraper = EventScraper(self.logger)
        events = [
            Event(e, self.logger)
            for e in scraper.scrape(BeautifulSoup(res.content, "html.parser"))
        ]
        self.logger.info(f"found '{len(events)}' events")

        return events

    def event(self, name: str) -> Event:
        """
        Get an event with name `name`.
        :param name: The name of the event
        :raises: ValueError if the event cannot be found
        :return: The event
        """
        self.logger.info(f"querying event with name '{name}'")
        matches = [
            e
            for e in self.events()
            if e.model.canonical_name == models.Event.canonicalize(name)
        ]
        if len(matches) == 0:
            raise ValueError(f"event with name '{name}' not found")
        return matches[0]


class Event:
    """A Hyrox event."""

    def __init__(self, model: models.Event, logger: logging.Logger) -> None:
        self.model = model
        self.logger = logger

    def results(
        self, division_name: models.DivisionName, splits: bool = False
    ) -> list[Result]:
        """
        Get the results from an event for the specified division.
        :param division: The name of the division
        :param splits: Enrich results with detailed splits data
        :return: The collection of results
        """
        self.logger.info(
            f"fetching results for division '{division_name}' at event '{self.model.canonical_name}'"
        )

        # get the requested division
        division = self._division(division_name)
        self.logger.info(f"found division '{division.model.name}'")

        # get the results from the division
        results = division.results()
        self.logger.info(f"fetched {len(results)} results for division")

        if splits:
            self.logger.info("fetching splits for all results...")
            for result in results:
                result.model.splits = _get_splits_for_result(result)

        return results

    def result(
        self,
        division_name: models.DivisionName,
        athlete_name: str,
        splits: bool = False,
    ) -> Result:
        """
        Get the results from an event for the specified division and athlete.
        :param division_name: The name of the division
        :param athlete_name: The name of the athlete
        :param splits: Enrich results with detailed splits data
        :raises: ValueError: If athlete is not found
        :return: The result
        """
        self.logger.info(
            f"fetching result for athlete '{athlete_name}' in division '{division_name}' at event '{self.model.canonical_name}'"
        )

        # get the requested division
        division = self._division(division_name)

        result = division.result(athlete_name)
        self.logger.info(f"found result for athlete '{athlete_name}'")

        if splits:
            self.logger.info(f"fetching splits for athlete '{athlete_name}'...")
            result.model.splits = _get_splits_for_result(result)

        return result

    def _division(self, name: models.DivisionName) -> _Division:
        """
        Get the division for the event with the specified name.
        :param name: The name of the division
        :raises: ValueError if division with name is not found
        :return: The division
        """
        self.logger.info(
            f"fetching division '{name}' at event '{self.model.canonical_name}'"
        )
        matches = [d for d in self._divisions() if d.model.name == name]
        if len(matches) < 1:
            raise ValueError(f"division with name '{name}' not found for event")
        return matches[0]

    def _divisions(self) -> list[_Division]:
        """
        List the divisions for an event.
        :return: The list of divisions for the event
        """
        self.logger.info(
            f"fetching all divisions at event '{self.model.canonical_name}'"
        )

        # get the content from the event page
        res = requests.get(str(self.model.url))
        res.raise_for_status()

        # scrape the divisions
        scraper = DivisionScraper(logging.getLogger(__name__))
        return [
            _Division(d, self.logger)
            for d in scraper.scrape(BeautifulSoup(res.content, "html.parser"))
        ]


def _get_splits_for_result(r: Result, retry: int = 8) -> models.Splits:
    """
    Get the splits for a specified result.
    :param r: The result
    :param retry: The number of retries
    :return: The splits
    """
    for _ in range(retry):
        try:
            return _try_get_splits(r)
        except ValueError:
            time.sleep(1)
            continue

    raise RuntimeError("maximum retries exceeded when querying result")


def _try_get_splits(r: Result) -> models.Splits:
    """
    Try and query splits for a specified result.
    :param r: The result
    :return: The splits
    """
    # grab the page
    res = requests.get(f"{r.model.url}?tab=splits")

    # scrape the content
    scraper = SplitsScraper(logging.getLogger(__name__))
    return scraper.scrape(BeautifulSoup(res.content, "html.parser"))


class Result:
    """A Hyrox result."""

    def __init__(self, model: models.Result, logger: logging.Logger) -> None:
        self.model = model
        self.logger = logger


# -----------------------------------------------------------------------------
# Private Classes
# -----------------------------------------------------------------------------


class _Division:
    """A hyrox division."""

    def __init__(self, model: models.Division, logger: logging.Logger) -> None:
        self.model = model
        self.logger = logger

    def results(self) -> list[Result]:
        """
        List the rankings for a division.
        :return: The list of rankings
        """
        p = 1
        s = ResultScraper(logging.getLogger(__name__))

        rankings: list[Result] = []
        while True:
            res = requests.get(f"{self.model.url}?p={p}")
            res.raise_for_status()

            scraped = s.scrape(BeautifulSoup(res.content, "html.parser"))
            if len(scraped) == 0:
                break

            rankings.extend([Result(r, self.logger) for r in scraped])
            p += 1

        return rankings

    def result(self, athlete: str) -> Result:
        """
        Find the ranking for a specific athlete.
        :param athlete: The name of the athlete
        :return: The ranking for the athlete, or `None`
        """
        found = [r for r in self.results() if r.model.name.lower() == athlete.lower()]
        if len(found) < 1:
            raise ValueError(
                f"athlete with name '{athlete}' not found in division '{self.model.name}'"
            )
        return found[0]
