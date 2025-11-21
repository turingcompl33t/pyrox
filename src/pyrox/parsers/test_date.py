"""
Unit tests for parser.
"""

from datetime import datetime

from .date import DateParser


def test_date_parser() -> None:
    """Date parser behaves as expected."""

    parser = DateParser()

    assert parser.parse("8 years ago (20 Oct 2018)") == datetime(
        day=20, month=10, year=2018
    )
    assert parser.parse("2 weeks ago (7–9 Nov 2025)") == datetime(
        day=7, month=11, year=2025
    )
    assert parser.parse("12 months ago (29 Nov–1 Dec 2024)") == datetime(
        day=29, month=11, year=2024
    )
    assert parser.parse("20–23 Nov 2025, France, Europe") == datetime(
        day=20, month=11, year=2025
    )

    assert parser.parse("28 Feb 2026, Taiwan, Asia") == datetime(
        day=28, month=2, year=2026
    )
