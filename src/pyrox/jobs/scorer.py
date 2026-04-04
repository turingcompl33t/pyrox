"""
Hyrox points scorer.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol

from pydantic import BaseModel

import pyrox.models as models
from pyrox.client import Division, Event, Hyrox


class Scorer:
    def __init__(
        self,
        cache_dir: Path,
        event_map: dict[str, models.EventTier],
        logger: logging.Logger,
    ) -> None:
        # the cache directory path
        self.cache_dir = cache_dir
        # the map from event name -> event class
        self.event_map = event_map
        # the logger instance
        self.logger = logger

    def score(
        self,
        gender: models.Gender,
        race: models.Race,
        after: datetime,
        before: datetime,
    ) -> dict[str, float]:
        """
        Compute scoring.
        :param gender: The target gender
        :param race: The target race
        :param after: The begin date
        :param before: The end date
        """
        if not self.cache_dir.is_dir():
            raise ValueError(f"cache directory {self.cache_dir} not found")
        self.logger.info(f"computing scoring for gender {gender} and race {race}")

        # a client to perform all scoring
        client = Hyrox(self.logger)

        # get all events relevant to the date range
        events = self._fetch_events(client, after, before)
        self.logger.info(f"found {len(events)} events in date range")

        # the master points data structure maps athlete name -> points data,
        # across all events that are relevant to the specified date range
        points: dict[str, list[models.PointsAward]] = {}
        for event in events:
            # compute the update for the event
            update = self._score_event(gender, race, event)

            # update the master data structure with the update
            for athlete, results in update.items():
                if athlete in points:
                    points[athlete].extend(results)
                else:
                    points[athlete] = results
        self.logger.info(
            f"identified {len(points)} athletes awarded points for performances in specified date range"
        )

        # for each athlete, filter all point awards to top-5 performances,
        # and aggregate (sum) to produce the final point calculation
        awarded: dict[str, float] = {}
        for athlete, point_awards in points.items():
            awarded[athlete] = sum(
                sorted([pa.points_awarded for pa in point_awards], reverse=True)[:5]
            )

        self.logger.info(f"computed point awards for {len(awarded)} athletes")
        return awarded

    def _score_event(
        self, gender: models.Gender, race: models.Race, event: Event
    ) -> dict[str, list[models.PointsAward]]:
        """
        Score an event for the specified gender and race.
        :param gender: The target gender
        :param race: The target race
        :param event: The event to score
        :return: The scoring
        """
        self.logger.info(f"scoring event {event.model.canonical_name}")

        # get the divisions relevant to the query
        relevant_division_names = _divisions_for_query(gender, race)
        self.logger.debug(
            f"identified {len(relevant_division_names)} relevant divisions for query: {relevant_division_names}"
        )

        # get the data for the relevant divisions
        relevant_divisions = [
            d for d in event.divisions() if d.model.name in relevant_division_names
        ]
        self.logger.debug(
            f"resolved {len(relevant_divisions)} relevant divisions from event data"
        )

        points: dict[str, list[models.PointsAward]] = {}
        for division in relevant_divisions:
            update = self._score_division(event.model.canonical_name, division)
            for athlete, points_awarded in update.items():
                self.logger.debug(f"computed points award for athlete {athlete}")
                new = models.PointsAward(
                    event_name=event.model.canonical_name,
                    division_name=division.model.name.value,
                    points_awarded=points_awarded,
                )
                if athlete in points:
                    points[athlete].append(new)
                else:
                    points[athlete] = [new]

        return points

    def _score_division(self, event_name: str, division: Division) -> dict[str, float]:
        """
        Score an individual division.
        :param event_name: The name of the event
        :param division: The division to score
        :return: The points results for the division
        """
        self.logger.info(f"scoring division {division.model.name}")

        # get the results for the division, with athlete enrichment;
        # we only ever need top 15 results from the division for points allocation,
        # regardless of the race tier that is being used (maximum through 15th place)
        results = division.results(limit=16, athlete=True, retry=1)
        self.logger.debug(
            f"fetched {len(results)} results for division {division.model.name}"
        )

        # determine the race tier
        race_tier = self._event_to_race_tier(event_name)

        runner = AlgorithmRunner(self.logger)
        return runner.run(race_tier, [r.model for r in results])

    def _event_to_race_tier(self, event_name: str) -> models.RaceTier:
        """
        Compute the race tier for the specified event.
        :param event_name: The canonical name of the event
        :return: The race tier for points calculation
        """
        if event_name in self.event_map:
            match self.event_map[event_name]:
                case models.EventTier.REGIONAL:
                    return models.RaceTier.REGIONAL_E15
                case models.EventTier.MAJOR:
                    return models.RaceTier.MAJOR_E15
                case models.EventTier.WC:
                    return models.RaceTier.WC_E15
                case _:
                    raise RuntimeError(f"unknown '{self.event_map[event_name]}'")
        else:
            # default if not provided is standard pro race
            return models.RaceTier.STANDARD_PRO

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


# the callback function used to compute points allocation
# Args:
# 1. first place time
# 2. target time
# Returns: points allocation
type AllocationFn = Callable[[float, float], float]


class TableEntry(BaseModel):
    """An entry in the algorithm table."""

    # the callback used to compute points allocation
    fn: AllocationFn
    # the percentile logic; a float that represents the
    # percentile that the position must finish within of
    # the first place time in order to be awarded points
    percentile: float


def _default(x: float, y: float) -> float:
    return x / y * 100


class Algorithm(Protocol):
    @property
    def table(self) -> list[TableEntry]:
        """Get the table."""
        ...


class AlgorithmStandardPro:
    """The algorithm for STANDARD PRO race tier."""

    def __init__(self) -> None:
        self._table: list[TableEntry] = [
            TableEntry(fn=lambda x, y: 105.0, percentile=1.0),
            TableEntry(fn=lambda x, y: 100.0, percentile=0.1),
            TableEntry(fn=_default, percentile=0.125),
            TableEntry(fn=_default, percentile=0.15),
            TableEntry(fn=_default, percentile=0.175),
            TableEntry(fn=_default, percentile=0.2),
            TableEntry(fn=_default, percentile=0.2),
            TableEntry(fn=_default, percentile=0.2),
        ]

    @property
    def table(self) -> list[TableEntry]:
        return self._table


class AlgorithmRunner:
    """The points algorithm."""

    def __init__(self, logger: logging.Logger) -> None:
        # logger for the instance
        self.logger = logger

    def run(
        self, tier: models.RaceTier, results: list[models.Result]
    ) -> dict[str, float]:
        """
        Compute scoring for the provided results.
        :param tier: The race tier
        :param results: The raw results
        :return: The results augmented with points allocation
        """
        # ensure results are sorted by position
        results = sorted(results, key=lambda r: r.position, reverse=True)

        # get the appropriate algorithm
        algo = self._get_algorithm(tier)

        # filter results; we only need as many as are present in the table;
        # these are the only positions that may receive points
        results = results[: len(algo.table)]

        # the time for the first place finisher is needed for most calculations
        first_place_time = results[0].time.total_seconds()

        points: dict[str, float] = {}
        for result, entry in zip(results, algo.table):
            # determine if the position meets percentile requirement
            if result.time.total_seconds() > first_place_time * (
                1.0 + entry.percentile
            ):
                continue

            # meets percentile requirement; compute points and track
            assert result.athlete.canonical_name is not None, "broken invariant"
            points[result.athlete.canonical_name] = entry.fn(
                first_place_time, result.time.total_seconds()
            )

        return points

    def _get_algorithm(self, tier: models.RaceTier) -> Algorithm:
        match tier:
            case models.RaceTier.STANDARD_PRO:
                return AlgorithmStandardPro()
            case _:
                raise NotImplementedError("not implemented")


def _cache_key(object: str, after: datetime, before: datetime) -> str:
    """Compute the cache key."""
    return f"{after.year}-{after.month:02d}-{after.day:02d}-to-{before.year}-{before.month:02d}-{before.day:02d}-{object}"


def _divisions_for_query(
    gender: models.Gender, race: models.Race
) -> set[models.DivisionName]:
    """
    Get the relevant divisions for the specified query.
    :param gender: The query gender
    :param race: The query race
    :return: The relevant division names
    """
    if gender == models.Gender.MALE and race == models.Race.SINGLES:
        return {models.DivisionName.ELITE_MEN, models.DivisionName.PRO_MEN}
    if gender == models.Gender.FEMALE and race == models.Race.SINGLES:
        return {models.DivisionName.ELITE_WOMEN, models.DivisionName.PRO_WOMEN}
    if gender == models.Gender.MALE and race == models.Race.DOUBLES:
        return {
            models.DivisionName.PRO_DOUBLES_ELITE_MEN,
            models.DivisionName.PRO_DOUBLES_MEN,
        }
    if gender == models.Gender.FEMALE and race == models.Race.DOUBLES:
        return {
            models.DivisionName.PRO_DOUBLES_ELITE_WOMEN,
            models.DivisionName.PRO_DOUBLES_WOMEN,
        }
    raise RuntimeError("unreachable")
