"""
Object model.
"""

import json
from datetime import timedelta
from enum import StrEnum
from typing import Annotated

import humanize
from annotated_types import Len
from pydantic import BaseModel, HttpUrl


class AgeGroup(StrEnum):
    """Hyrox age groups"""

    # solo and doubles
    AG_UNDER_24 = "under_24"
    AG_25_29 = "25_29"
    AG_30_34 = "30_34"
    AG_35_39 = "35_39"
    AG_40_44 = "40_44"
    AG_45_49 = "45_49"
    AG_50_54 = "50_54"
    AG_55_59 = "55_59"
    AG_60_64 = "60_64"
    AG_65_69 = "65_69"
    AG_70_74 = "70_74"
    AG_75_79 = "75_79"
    AG_80_84 = "80_84"
    AG_85_89 = "85_89"

    # relay
    AG_UNDER_40 = "relay_under_40"
    AG_40_PLUS = "relay_40_plus"


class Station(StrEnum):
    """An enumeration over Hyrox stations."""

    Ski = "ski"
    SledPush = "sled_push"
    SledPull = "sled_pull"
    BurpeeBroadJumps = "burpee_bround_jumps"
    Row = "row"
    FarmersCarry = "farmers_carry"
    Lunges = "lunges"
    Wallballs = "wallballs"


class Splits(BaseModel):
    """The data model for Hyrox splits."""

    # the run splits for the race (8 in total)
    runs: Annotated[list[timedelta], Len(min_length=8, max_length=8)]

    # the station splits for the race
    stations: dict[Station, timedelta]

    @property
    def run_total(self) -> timedelta:
        """Get total run time."""
        return sum((duration for duration in self.runs), timedelta(seconds=0))

    @property
    def station_total(self) -> timedelta:
        """Get total station time"""
        return sum(
            (duration for duration in self.stations.values()), timedelta(seconds=0)
        )

    @property
    def total_time(self) -> timedelta:
        """Get total time."""
        return self.run_total + self.station_total

    def pretty(self) -> str:
        """Return a pretty JSON-string representation."""

        data = {
            "total": humanize.precisedelta(self.total_time),
            "run_total": humanize.precisedelta(self.run_total),
            "station_total": humanize.precisedelta(self.station_total),
            "run_splits": [humanize.precisedelta(split) for split in self.runs],
            "station_splits": {
                str(name): humanize.precisedelta(split)
                for name, split in self.stations.items()
            },
        }
        return json.dumps(data, indent=2)


class Result(BaseModel):
    """A result for a specific athlete, division, and event"""

    # the finish position
    position: int
    # the age group finish position; some rankings do not report AG positions
    position_ag: int | None = None
    # the athlete name
    name: str
    # the athlete age group; some rankings do not report AG
    age_group: AgeGroup | None = None
    # finish time
    time: timedelta
    # the link to the race analysis for the athlete
    url: HttpUrl

    # the splits for the race, if available / requested
    splits: Splits | None = None
    # the athlete profile URL, if available / requested
    profile: HttpUrl | None = None
