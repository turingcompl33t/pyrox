import json
import logging
import sys
from datetime import datetime, timedelta

from pyrox.client.client import Hyrox
from pyrox.logging import create_logger


def _date_range_for_race(race_date: datetime) -> tuple[datetime, datetime]:
    """
    Compute the date range for events relevant to a particular elite race.
    :param race_date: The date of the race
    :return: (begin, end)
    """
    # cutoff data is 3 weeks prior to the race data
    end = race_date - timedelta(weeks=3)
    # begin date is the year prior to the cutoff date
    begin = end - timedelta(days=365)
    return begin, end


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    # Hyrox D.C. - elite race on March 6th, 2026
    race_date_dc = datetime(year=2026, month=3, day=6)
    begin, end = _date_range_for_race(race_date_dc)

    events = client.events()
    # write in jsonlines format
    with open("events.jsonl", "w") as f:
        for e in events:
            f.write(f"{json.dumps(e.model.model_dump(mode='json'))}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
