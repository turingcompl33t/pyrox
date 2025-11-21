"""
Parser implementation.
"""

import re
from datetime import datetime

from dateutil.parser import parse
from dateutil.parser._parser import ParserError


class DateParser:
    """A class for parsing dates."""

    def __init__(self) -> None:
        pass

    def parse(self, text: str) -> datetime:
        """
        Parse a datetime from the provided text.
        :return: the parsed datetime
        :raises: ValueError on failure to parse
        """
        try:
            return _try_parse_date_old(text)
        except Exception:
            pass

        try:
            return _try_parse_date_new(text)
        except Exception:
            pass

        raise ValueError("unable to parse date")


def _try_parse_date_old(text: str) -> datetime:
    """
    Try to parse a date from the "old" style text.
        e.g. 8 years ago (1 Jan 2020)
    """
    match = re.search(r"\((.*?)\)", text)
    if match is None:
        raise RuntimeError("not an old-style date")

    return _try_parse_date_string(match.group(1))


def _try_parse_date_new(text: str) -> datetime:
    """
    Try to parse a date from the "new" style text.
        e.g. 1 Jan 2020, Chicago, USA
    """
    date, *_ = text.split(",")
    return _try_parse_date_string(date)


def _try_parse_date_string(text: str) -> datetime:
    """
    Try to parse a generic date string;
    this may include no range / range / cross-month range.
    """
    try:
        return parse(text)
    except ParserError:
        pass

    # the date might include a range
    try:
        return _try_parse_range_simple(text)
    except (IndexError, ValueError, ParserError):
        pass

    return _try_parse_range_cross_month(text)


def _try_parse_range_simple(text: str) -> datetime:
    """
    Try to parse a simple date range
        e.g. 27-28 Jan 2024.
    """
    # extract day(s), month, year
    parts = text.split()
    # isolate the first part of the days component
    begin, _ = parts[0].split("–")
    # join and re-attempt
    return parse(" ".join([begin, parts[1], parts[2]]))


def _try_parse_range_cross_month(text: str) -> datetime:
    """
    Try to parse a date range that crosses month boundary
        e.g. 31 Aug-1 Sept 2024
    """
    # extract day(s), month, year
    parts = text.split()
    # isolate the first part of the days component
    month, _ = parts[1].split("–")
    # join and re-attempt
    return parse(" ".join([parts[0], month, parts[3]]))
