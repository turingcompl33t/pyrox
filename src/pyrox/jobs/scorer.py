"""
Hyrox points scorer.
"""

import logging
from datetime import datetime
from pathlib import Path

import pyrox.models as models
from pyrox.client import Event, Hyrox


class Scorer:
    def __init__(self, cache_dir: Path, logger: logging.Logger) -> None:
        # the cache directory path
        self.cache_dir = cache_dir
        # the logger instance
        self.logger = logger

    def score(self, after: datetime, before: datetime) -> None:
        """
        Compute scoring.
        :param after: The begin date
        :param before: The end date
        """
        if not self.cache_dir.is_dir():
            raise ValueError(f"cache directory {self.cache_dir} not found")
        self.logger.info("scoring")

        # a client to perform all scoring
        client = Hyrox(self.logger)

        # get all events relevant to the date range
        events = self._fetch_events(client, after, before)
        self.logger.info(f"found {len(events)} events in date range")

    def _fetch_events(
        self, client: Hyrox, after: datetime, before: datetime
    ) -> list[Event]:
        """
        Fetch events for the specified date range, with caching.
        :param after: The begin date
        :param before: The end date
        :return: The events
        """
        assert self.cache_dir.is_dir(), "broken precondition"

        path = (self.cache_dir / _cache_key("events", after, before)).with_suffix(
            ".jsonl"
        )
        if path.is_file():
            # events for query already present; load from serialized data
            self.logger.debug("cached data exists; loading...")
            with path.open("r") as f:
                return [
                    Event(
                        model=models.Event.model_validate_json(line.strip()),
                        logger=self.logger,
                    )
                    for line in f
                ]

        # the data is not present in cache; fetch it
        self.logger.debug("events data is not cached; fetching...")
        events = client.events(after=after, before=before)

        # serialize to cache for future use
        with path.open("w") as f:
            for event in events:
                f.write(f"{event.model.model_dump_json()}\n")

        return events


def _cache_key(object: str, after: datetime, before: datetime) -> str:
    """Compute the cache key."""
    return f"{after.year}-{after.month:02d}-{after.day:02d}-to-{before.year}-{before.month:02d}-{before.day:02d}-{object}"
