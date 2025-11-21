"""
Race result model.
"""

from datetime import timedelta
from enum import StrEnum
from typing import Annotated

from annotated_types import Len
from pydantic import BaseModel


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


class Result(BaseModel):
    """The data model for Hyrox results."""

    # the run splits for the race (8 in total)
    run_splits: Annotated[list[timedelta], Len(min_length=8, max_length=8)]

    # the station splits for the race
    stations: dict[Station, timedelta]

    @property
    def run_total(self) -> timedelta:
        """Get total run time."""
        return sum((duration for duration in self.run_splits), timedelta(seconds=0))

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
