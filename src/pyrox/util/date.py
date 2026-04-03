"""
Date utilities.
"""

from datetime import datetime, timedelta


def date_range_for_race(
    race_date: datetime, cutoff_duration: timedelta = timedelta(weeks=3)
) -> tuple[datetime, datetime]:
    """
    Compute the date range for events relevant to a particular elite race.
    :param race_date: The date of the race
    :param cutoff_duration: The cutoff duration from the race date (default: 3 weeks)
    :return: (begin, end)
    """
    # cutoff data is 3 weeks prior to the race date
    end = race_date - cutoff_duration
    # begin date is the year prior to the cutoff date
    begin = end - timedelta(days=365)
    return begin, end


def year_month_range(start: datetime, end: datetime) -> list[tuple[int, int]]:
    """
    Generate (year, month) tuples for all combinations in a date range.
    :param start: The start date
    :param end: The end date
    :return: The sequence
    """
    if start > end:
        raise ValueError("start must be <= end")

    year, month = start.year, start.month

    result = []
    while (year, month) <= (end.year, end.month):
        result.append((year, month))

        # increment month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return result
