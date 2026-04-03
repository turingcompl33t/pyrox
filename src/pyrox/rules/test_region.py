"""
Unit tests for region mapping.
"""

from pyrox.models.region import Region
from pyrox.rules.regions import RegionMapper


def test_region_map() -> None:
    """We can map countries to their regions."""
    mapper = RegionMapper()
    assert mapper.region_for("United States") == Region.AMERICAS
    assert mapper.region_for("united states") == Region.AMERICAS
    assert mapper.region_for("Switzerland") == Region.EMEA
    assert mapper.region_for("Australia") == Region.APAC
