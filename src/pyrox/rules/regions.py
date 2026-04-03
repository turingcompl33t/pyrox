"""
Map countries to regions.
"""

from pyrox.models.region import Region
from pyrox.rules.regions_data import _DATA


class RegionMapper:
    def __init__(self) -> None:
        pass

    def region_for(self, country: str) -> Region:
        """
        Map the provided country to its Hyrox region.
        :param country: The country name
        :raises: ValueError if the country is not recognized
        :return: The region for the country
        """
        normalized = country.lower()
        if normalized not in _DATA:
            raise ValueError(f"country '{country}' not recognized")
        return _DATA[normalized]
