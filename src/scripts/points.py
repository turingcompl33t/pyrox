"""
Points calculator for new (2026-2027) scoring system.
"""

import logging
import sys
from datetime import datetime

from pyrox.client.client import Hyrox
from pyrox.logging import create_logger


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    after = datetime(year=2026, month=3, day=25)
    before = datetime(year=2026, month=4, day=1)

    events = client.events(before=before, after=after)
    print(f"found {len(events)} events")
    for e in events:
        print(e.model.canonical_name)

    # # write in jsonlines format
    # with open("events.jsonl", "w") as f:
    #     for e in events:
    #         f.write(f"{json.dumps(e.model.model_dump(mode='json'))}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
