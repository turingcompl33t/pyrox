"""
Object model.
"""

from datetime import timedelta
from enum import StrEnum

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


class Ranking(BaseModel):
    """A ranking for a particular division."""

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
