"""
Object model.
"""

from enum import StrEnum

from pydantic import BaseModel, HttpUrl


class DivisionName(StrEnum):
    """An enumeration over Hyrox divisions."""

    # solo men, open weights
    MEN = "men"
    # solo women, open weights
    WOMEN = "women"
    # doubles men, open weights
    DOUBLES_MEN = "doubles_men"
    # double women, open weights
    DOUBLES_WOMEN = "doubles_women"
    # doubles mixed, open weights
    DOUBLES_MIXED = "doubles_mixed"
    # solo men, pro weights
    PRO_MEN = "pro_men"
    # solo women, pro weights
    PRO_WOMEN = "pro_women"
    # double men, pro weights
    PRO_DOUBLES_MEN = "pro_doubles_men"
    # doubles women, pro weights
    PRO_DOUBLES_WOMEN = "pro_doubles_women"
    # mixed, pro weights
    PRO_DOUBLES_MIXED = "pro_doubles_mixed"
    # team relay men
    TEAM_RELAY_MEN = "team_relay_men"
    # team relay women
    TEAM_RELAY_WOMEN = "team_relay_women"
    # team relay mixed
    TEAM_RELAY_MIXED = "team_relay_mixed"
    # adaptive men
    ADAPTIVE_MEN = "adaptive_men"
    # adaptive women
    ADAPTIVE_WOMEN = "adaptive_women"

    # solo men elite
    ELITE_MEN = "elite_men"
    # solo elite women
    ELITE_WOMEN = "elite_women"
    # doubles elite men
    PRO_DOUBLES_ELITE_MEN = "pro_doubles_elite_men"
    # doubles elite women
    PRO_DOUBLES_ELITE_WOMEN = "pro_doubles_elite_women"


class Division(BaseModel):
    """A Hyrox division, in the context of an event."""

    # the name of the division
    name: DivisionName
    # the number of finishers in the division
    n_finishers: int
    # the link to division rankings
    url: HttpUrl
