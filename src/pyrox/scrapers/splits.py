"""
Result scraper.
"""

import logging
from datetime import timedelta
from enum import Enum

from bs4 import BeautifulSoup, Tag

from pyrox.models import Splits, Station

from .base import BaseScraper


class RowType(Enum):
    ROXZONE_IN = 0
    ROXZONE_OUT = 1
    STATION_IN = 2
    STATION_OUT = 3


class SplitsScraper(BaseScraper):
    """A class for scraping splits from an individual analysis page."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def scrape(self, soup: BeautifulSoup) -> Splits:
        """
        Scrape and parse splits.
        :return: The parsed splits
        """
        # find all of the row elements
        rows = soup.find_all("tr", class_="border-b")
        if len(rows) != 31:
            raise ValueError("unexpected number of rows in splits table")

        # parse the first non-header row
        without_roxzone = False
        try:
            _ = _parse_row(rows[1])
        except ValueError:
            without_roxzone = True

        # defer to distinct parsing logic depending on if this race has roxzone tracking
        return (
            self._scrape_without_roxzone(rows[1:])
            if without_roxzone
            else self._scrape_with_roxzone(rows[1:])
        )

    def _scrape_with_roxzone(self, rows: list[Tag]) -> Splits:
        """Scrape with roxzone data."""

        # the run splits, in order
        run_splits: list[timedelta] = []
        # the station splits, in order
        station_splits: list[timedelta] = []
        # the total time spent in the roxzone, in seconds
        roxzone: timedelta = timedelta(seconds=0)

        # skip the header row
        for row in rows:
            split, type = _parse_row(row)

            if type == RowType.ROXZONE_IN:
                # roxzone in completes a run split
                run_splits.append(split)
            elif type == RowType.ROXZONE_OUT:
                # roxzone out just adds to roxzone time
                roxzone += split
            elif type == RowType.STATION_IN:
                # station in just adds to roxzone time UNLESS it is the final run
                # there is no roxzone for wallballs, for some reason...
                if len(run_splits) == 7 and len(station_splits) == 7:
                    run_splits.append(split)
                else:
                    roxzone += split
            else:
                # station out gives station split
                station_splits.append(split)

        if len(run_splits) != 8 or len(station_splits) != 8:
            raise ValueError("failed to parse all data")

        return Splits(
            runs=run_splits,
            stations={name: split for name, split in zip(Station, station_splits)},
            roxzone=roxzone,
        )

    def _scrape_without_roxzone(self, rows: list[Tag]) -> Splits:
        """Scrape without roxzone data."""

        # the run splits, in order
        run_splits: list[timedelta] = []
        # the station splits, in order
        station_splits: list[timedelta] = []

        # skip the header row
        run: bool = True
        for row in rows:
            split, type = _parse_row(row, skip_roxzone=True)
            if type in {RowType.ROXZONE_IN, RowType.ROXZONE_OUT}:
                continue

            if run:
                run_splits.append(split)
            else:
                station_splits.append(split)

            # toggle for next event
            run = not run

        if len(run_splits) != 8 or len(station_splits) != 8:
            raise ValueError("failed to parse all data")

        return Splits(
            runs=run_splits,
            stations={name: split for name, split in zip(Station, station_splits)},
            roxzone=timedelta(seconds=0),
        )


def _parse_row(tag: Tag, skip_roxzone: bool = False) -> tuple[timedelta, RowType]:
    """
    Parse a row.
    :return: (split parsed from the row, station type)
    """
    parts = tag.find_all("td")
    if len(parts) < 1:
        raise ValueError("failed to parse")

    # parse the row type from the name
    type = _parse_type(parts[0].text)
    if type in {RowType.ROXZONE_IN, RowType.ROXZONE_OUT} and skip_roxzone:
        return timedelta(seconds=0), type

    # parse the time delta
    diff: list[str] = parts[-1].text.split(":")
    diff = ["0"] + diff if len(diff) < 3 else diff

    return (
        timedelta(hours=int(diff[0]), minutes=int(diff[1]), seconds=int(diff[2])),
        type,
    )


def _parse_type(name: str) -> RowType:
    """Parse a row type from the row identifier."""

    if "Roxzone" in name and "In" in name:
        return RowType.ROXZONE_IN
    elif "Roxzone" in name and "Out" in name:
        return RowType.ROXZONE_OUT
    elif "Total Time" in name:
        # treat total time as a roxzone out because it completes a station
        return RowType.ROXZONE_OUT
    elif "In" in name:
        return RowType.STATION_IN
    else:
        return RowType.STATION_OUT
