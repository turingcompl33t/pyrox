"""
Get events in a specified datetime range.
"""

import logging
import sys
from datetime import datetime

from pyrox.client import Hyrox
from pyrox.logging import create_logger


def main() -> int:
    client = Hyrox(create_logger(level=logging.INFO))

    # get events in 24/25 season (roughly)
    events = client.events(
        after=datetime(day=1, month=7, year=2024),
        before=datetime(day=1, month=7, year=2025),
    )
    print(len(events))

    return 0


if __name__ == "__main__":
    sys.exit(main())
