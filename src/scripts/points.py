"""
Points calculator for new (2026-2027) scoring system.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pyrox.models as models
from pyrox.jobs.scorer import Scorer
from pyrox.logging import create_logger


def main() -> int:
    # a map that defines the event types (e.g. regionals, majors)
    event_map = {}
    # the scorer instance
    scorer = Scorer(Path.cwd() / "cache", event_map, create_logger(level=logging.DEBUG))

    after = datetime(year=2026, month=3, day=25)
    before = datetime(year=2026, month=4, day=1)

    # compute the scoring
    points = scorer.score(models.Gender.MALE, models.Race.SINGLES, after, before)
    print(json.dumps(points, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
