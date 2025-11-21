"""
Result scraper.
"""

import logging
from datetime import timedelta

from bs4 import BeautifulSoup, Tag

from pyrox.models import Result, Station

from .base import BaseScraper


class ResultScraper(BaseScraper):
    """A class for scraping results from an individual analysis page."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def scrape(self, soup: BeautifulSoup) -> Result:
        """
        Scrape and parse a result.
        :return: The parsed result
        """
        # find all of the row elements
        rows = soup.find_all("tr", class_="border-b")
        if len(rows) != 31:
            raise ValueError("unexpected number of rows in splits table")

        # the run splits, in order
        run_splits: list[timedelta] = []
        # the station splits, in order
        station_splits: list[timedelta] = []

        # skip the first row (roxzone in)
        run: bool = True
        for row in rows[1:]:
            split, is_roxzone = _parse_row(row)
            if is_roxzone:
                continue

            if run:
                run_splits.append(split)
            else:
                station_splits.append(split)

            # toggle the flag
            run = not run

        if len(run_splits) != 8 or len(station_splits) != 8:
            raise ValueError("failed to parse all data")

        return Result(
            run_splits=run_splits,
            stations={name: split for name, split in zip(Station, station_splits)},
        )


def _parse_row(tag: Tag) -> tuple[timedelta, bool]:
    """
    Parse a row.
    :return: (split parsed from the row, roxzone)
    """
    parts = tag.find_all("td")
    if len(parts) < 1:
        raise ValueError("failed to parse")

    name: str = parts[0].text
    if "roxzone" in name.lower():
        return timedelta(seconds=0), True

    diff: list[str] = parts[-1].text.split(":")
    diff = ["0"] + diff if len(diff) < 3 else diff

    return (
        timedelta(hours=int(diff[0]), minutes=int(diff[1]), seconds=int(diff[2])),
        False,
    )
