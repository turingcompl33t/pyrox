"""
Models for points calculations.
"""

from enum import StrEnum

from pydantic import BaseModel


class Gender(StrEnum):
    """The athlete gender category."""

    # all male results
    MALE = "male"
    # all female results
    FEMALE = "female"


class Race(StrEnum):
    """Singles versus doubles."""

    # singles races
    SINGLES = "singles"
    # doubles races
    DOUBLES = "doubles"


class EventTier(StrEnum):
    """The event class according to the points system."""

    # a regional race
    REGIONAL = "regional"
    # a major race
    MAJOR = "major"
    # world championships
    WC = "wc"


class RaceTier(StrEnum):
    """The race class according to the points system."""

    # a standard pro race
    STANDARD_PRO = "standard_pro"
    # a regional race
    REGIONAL_E15 = "regional_e15"
    # a major race
    MAJOR_E15 = "major_e15"
    # worlds elite race
    WC_E15 = "worlds_e15"


class PointsAward(BaseModel):
    """A single result with data relevant to points calculation."""

    # the name of the event
    event_name: str
    # the name of the division
    division_name: str
    # points awarded
    points_awarded: float
