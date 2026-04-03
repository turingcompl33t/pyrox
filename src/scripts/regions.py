import json
import logging
import sys
from datetime import datetime

from pyrox.client.client import Hyrox
from pyrox.logging import create_logger
from pyrox.util.date import date_range_for_race


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    # Hyrox D.C. - elite race on March 6th, 2026
    race_date_dc = datetime(year=2026, month=3, day=6)
    begin, end = date_range_for_race(race_date_dc)

    events = client.events(before=end, after=begin)
    # write in jsonlines format
    with open("events.jsonl", "w") as f:
        for e in events:
            f.write(f"{json.dumps(e.model.model_dump(mode='json'))}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
