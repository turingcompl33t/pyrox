"""
Hyrox results client.
"""

from __future__ import annotations

import logging
import os
import time
import urllib.parse
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from pydantic import HttpUrl
from requests import HTTPError

import pyrox.http.http as http
import pyrox.models as models
from pyrox.config import BASE_URL
from pyrox.scrapers.event import EventScraper
from pyrox.scrapers.event_details import EventDetailsScraper
from pyrox.scrapers.result import ResultScraper
from pyrox.scrapers.splits import SplitsScraper
from pyrox.util.date import year_month_range


class Hyrox:
    """A client for Hyrox results from hyresult.com."""

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.logger = logger

    def events(self, *, after: datetime, before: datetime) -> list[Event]:
        """
        Get all events, with an optional date range.
        :param: after: The beginning of the date range
        :param before: The end of the date range
        :return: A list of events
        """
        self.logger.info(f"fetching events from {after} to {before}")

        # get the individual requests we need to cover the date range
        requests = year_month_range(after, before)
        self.logger.debug(f"identified {len(requests)} requests to cover date range")

        # get raw events from all (year, month) combinations relevant to range
        raw_events = [
            e
            for year, month in requests
            for e in self._events_for_year_and_month(year, month)
        ]
        self.logger.info(f"scraped {len(raw_events)} raw events for date range")

        # enrich each event with event details; this is now necessary in order
        # to sort events by date because dates no longer appear on the events page
        event_details_scraper = EventDetailsScraper(self.logger)
        for i, event in enumerate(raw_events):
            res = http.get(str(event.url))
            self.logger.debug(
                f"[{i + 1} / {len(raw_events)}] scraping event details for {event.url}"
            )
            event.details = event_details_scraper.scrape(
                BeautifulSoup(res.content, "html.parser")
            )

        # wrap the raw events in objects
        events = [Event(model=e, logger=self.logger) for e in raw_events]

        # filter the events by date
        if after is not None:
            events = [e for e in events if e.model.details.date > after]
        if before is not None:
            events = [e for e in events if e.model.details.date < before]

        self.logger.info(f"filtered to {len(events)} with date constraints")
        return events

    def _events_for_year_and_month(self, year: int, month: int) -> list[models.Event]:
        """
        Get events for a specified year and month.

        On Hyresult, events are now organized according to (year, month),
        so we fetch them in groups in this structure, and then perform
        day-level filtering at a higher level (the caller).

        :param year: The year
        :param month: The month (1-12)
        :return: The events for the year and month
        """
        assert 1 <= month <= 12, "month must be on [1-12]"
        self.logger.info(f"fetching events for year={year}, month={month}")

        url = f"https://www.hyresult.com/events/{year}/{month:02d}"
        self.logger.debug(f"fetching events with URL '{url}'")

        # issue the request
        res = http.get(url)

        # scrape the events
        scraper = EventScraper(self.logger)
        events = scraper.scrape(BeautifulSoup(res.content, "html.parser"))

        self.logger.debug(
            f"scraped {len(events)} events for year={year}, month={month}"
        )
        return events

    # def event(self, name: str) -> Event:
    #     """
    #     Get an event with name `name`.
    #     :param name: The name of the event
    #     :raises: ValueError if the event cannot be found
    #     :return: The event
    #     """
    #     self.logger.info(f"querying event with name '{name}'")
    #     matches = [
    #         e
    #         for e in self.events()
    #         if e.model.canonical_name == models.Event.canonicalize(name)
    #     ]
    #     if len(matches) == 0:
    #         raise ValueError(f"event with name '{name}' not found")
    #     return matches[0]

    # def results(
    #     self,
    #     event_name: str,
    #     division_name: models.DivisionName,
    #     athlete: bool = False,
    #     splits: bool = False,
    #     retry: int = 8,
    #     poll_interval: timedelta = timedelta(seconds=1),
    # ) -> list[Result]:
    #     """
    #     Get results for the specified division at the specified event.
    #     :param event_name: The name of the event
    #     :param division_name: The name of the division
    #     :param athlete: Enrich results with athlete profile data
    #     :param splits: Enrich results with detailed splits data
    #     :param retry: The number of retries for operations
    #     :param poll_interval: The poll interval for operations
    #     :return: The collection of results
    #     """
    #     event = self.event(event_name)
    #     return event.results(division_name, athlete, splits, retry, poll_interval)


class Event:
    """A Hyrox event."""

    def __init__(self, model: models.Event, logger: logging.Logger) -> None:
        self.model = model
        self.logger = logger

    def results(
        self,
        division_name: models.DivisionName,
        athlete: bool = False,
        splits: bool = False,
        retry: int = 8,
        poll_interval: timedelta = timedelta(seconds=1),
    ) -> list[Result]:
        """
        Get the results from an event for the specified division.
        :param division: The name of the division
        :param athlete: Enrich results with athlete profile data
        :param splits: Enrich results with detailed splits data
        :param retry: The number of retries for operations
        :param poll_interval: The poll interval for operations
        :return: The collection of results
        """
        self.logger.info(
            f"fetching results for division '{division_name}' at event '{self.model.canonical_name}'"
        )

        # get the requested division
        division = self.division(division_name)
        self.logger.info(f"found division '{division.model.name}'")

        # get the results from the division
        results = division.results(
            athlete=athlete, splits=splits, retry=retry, poll_interval=poll_interval
        )
        self.logger.info(f"fetched {len(results)} results for division")

        return results

    def result(
        self,
        division_name: models.DivisionName,
        athlete_name: str,
        athlete: bool = False,
        splits: bool = False,
        retry: int = 8,
        poll_interval: timedelta = timedelta(seconds=1),
    ) -> Result:
        """
        Get the results from an event for the specified division and athlete.
        :param division_name: The name of the division
        :param athlete_name: The name of the athlete
        :param athlete: Enrich results with athlete profile data
        :param splits: Enrich results with detailed splits data
        :param retry: The number of retries for operations
        :param poll_interval: The poll interval for operations
        :raises: ValueError: If athlete is not found
        :return: The result
        """
        self.logger.info(
            f"fetching result for athlete '{athlete_name}' in division '{division_name}' at event '{self.model.canonical_name}'"
        )

        # get the requested division
        division = self.division(division_name)

        result = division.result(athlete_name)
        self.logger.info(f"found result for athlete '{athlete_name}'")

        enricher = ResultEnricher(retry, poll_interval, self.logger)
        return enricher.enrich(result, athlete, splits) if splits or athlete else result

    def division(self, name: models.DivisionName) -> Division:
        """
        Get the division for the event with the specified name.
        :param name: The name of the division
        :raises: ValueError if division with name is not found
        :return: The division
        """
        matches = [d for d in self.divisions() if d.model.name == name]
        if len(matches) < 1:
            raise ValueError(f"division with name '{name}' not found for event")
        return matches[0]

    def divisions(self) -> list[Division]:
        """
        List the divisions for an event.
        :return: The list of divisions for the event
        """
        # wrap the division models in objects
        return [
            Division(model=d, logger=self.logger) for d in self.model.details.divisions
        ]


class ResultEnricher:
    """A class for enriching results."""

    def __init__(
        self, retry: int, poll_interval: timedelta, logger: logging.Logger
    ) -> None:
        # number of retries per operation
        self.retry = retry
        # poll interval for retried operations
        self.poll_interval = poll_interval
        # logger instance
        self.logger = logger

    def enrich(self, r: Result, athlete: bool, splits: bool) -> Result:
        """
        Enrich a result with splits and profile data.
        :param r: The result
        :param athlete: Indicates athlete should be included
        :param splits: Indicates splits should be included
        :raises: RuntimeError if maximum retries exceeded
        :return: The enriched result
        """
        if splits:
            r.model.splits = self._get_splits_for_result(r)
        if athlete:
            r.model.athlete = self._get_athlete_for_result(r)

        return r

    def _get_splits_for_result(self, r: Result) -> models.Splits:
        """
        Get the splits for a specified result.
        :param r: The result
        :param retry: The number of retries
        :param logger: The logger instance
        :return: The splits
        """
        self.logger.debug(f"fetching splits for '{r.model.athlete.name}'")
        for i in range(self.retry):
            self.logger.debug(f"attempt {i}...")
            try:
                return self._try_get_splits(r)
            except (ValueError, HTTPError):
                time.sleep(self.poll_interval.seconds)
                continue

        raise RuntimeError("maximum retries exceeded when querying splits")

    def _get_athlete_for_result(self, r: Result) -> models.AthleteRef:
        """
        Get the enriched athlete model fro a result.
        :param r: The result
        :return: The enriched athlete
        """
        self.logger.debug(
            f"fetching athlete data for athlete '{r.model.athlete.name}'..."
        )
        for i in range(self.retry):
            self.logger.debug(f"attempt {i}...")
            try:
                return self._try_get_athlete(r)
            except HTTPError:
                time.sleep(self.poll_interval.seconds)
                continue

        raise RuntimeError("maximum retries exceeded when querying athlete data")

    def _try_get_splits(self, r: Result) -> models.Splits:
        """
        Try and query splits for a specified result.
        :param r: The result
        :return: The splits
        """
        # grab the page
        res = http.get(f"{r.model.url}?tab=splits")

        # scrape the content
        scraper = SplitsScraper(logging.getLogger(__name__))
        return scraper.scrape(BeautifulSoup(res.content, "html.parser"))

    def _try_get_athlete(self, r: Result) -> models.AthleteRef:
        """
        Try and get athlete data for the specified result.
        :param r: The result
        :return: The athlete reference
        """
        # grab the page
        res = http.get(f"{r.model.url}?tab=overview")

        soup = BeautifulSoup(res.content, "html.parser")
        matches = [a["href"] for a in soup.find_all("a") if "/athlete/" in a["href"]]
        if len(matches) == 0:
            raise RuntimeError("could not locate athlete profile URL")

        # build the athlete profile URL
        url = HttpUrl(f"{BASE_URL}{matches[0]}")
        # parse the profile URL to canonical name
        parsed = os.path.basename(urllib.parse.urlparse(str(url)).path)
        return models.AthleteRef(
            name=r.model.athlete.name, canonical_name=parsed, profile_url=url
        )


class Result:
    """A Hyrox result."""

    def __init__(self, model: models.Result, logger: logging.Logger) -> None:
        self.model = model
        self.logger = logger


class Division:
    """A hyrox division."""

    def __init__(self, model: models.Division, logger: logging.Logger) -> None:
        self.model = model
        self.logger = logger

    def results(
        self,
        limit: int = -1,
        athlete: bool = False,
        splits: bool = False,
        retry: int = 8,
        poll_interval: timedelta = timedelta(seconds=1),
    ) -> list[Result]:
        """
        List the rankings for a division.
        :param limit: Limit the number of results queried
        :param athlete: Enrich results with athlete profile data
        :param splits: Enrich results with detailed splits data
        :param retry: The number of retries for operations
        :param poll_interval: The poll interval for operations
        :return: The list of results
        """
        p = 1
        s = ResultScraper(self.logger)

        results: list[Result] = []
        while True:
            res = http.get(f"{self.model.url}?p={p}")

            scraped = s.scrape(BeautifulSoup(res.content, "html.parser"))
            if len(scraped) == 0:
                break

            results.extend([Result(r, self.logger) for r in scraped])
            p += 1

            # break early if limit reached
            if limit > -1 and len(results) >= limit:
                break

        # enrich results
        if splits or athlete:
            enricher = ResultEnricher(retry, poll_interval, self.logger)
            for i, result in enumerate(results):
                self.logger.debug(
                    f"[{i + 1} / {len(results)}] enriching result for athlete '{result.model.athlete.name}'"
                )
                try:
                    result = enricher.enrich(result, athlete, splits)
                except RuntimeError as e:
                    self.logger.warning(
                        f"failed to enrich result for athlete '{result.model.athlete.name}': {e}"
                    )
                    continue

        return results

    def result(
        self,
        athlete_name: str,
        athlete: bool = False,
        splits: bool = False,
        retry: int = 8,
        poll_interval: timedelta = timedelta(seconds=1),
    ) -> Result:
        """
        Find the ranking for a specific athlete.
        :param athlete_name: The name of the athlete
        :param athlete: Enrich results with athlete profile data
        :param splits: Enrich results with detailed splits data
        :param retry: The number of retries for operations
        :param poll_interval: The poll interval for operations
        :return: The ranking for the athlete, or `None`
        """
        found = [
            r
            for r in self.results(
                athlete=athlete, splits=splits, retry=retry, poll_interval=poll_interval
            )
            if r.model.athlete.name.lower() == athlete_name.lower()
        ]
        if len(found) < 1:
            raise ValueError(
                f"athlete with name '{athlete}' not found in division '{self.model.name}'"
            )
        return found[0]
