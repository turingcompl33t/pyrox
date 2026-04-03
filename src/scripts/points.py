"""
Points calculator for new (2026-2027) scoring system.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from pyrox.jobs.scorer import Scorer
from pyrox.logging import create_logger


def main() -> int:
    scorer = Scorer(Path.cwd() / "cache", create_logger(level=logging.DEBUG))

    after = datetime(year=2026, month=3, day=25)
    before = datetime(year=2026, month=4, day=1)

    scorer.score(after, before)

    # # write in jsonlines format
    # with open("events.jsonl", "w") as f:
    #     for e in events:
    #         f.write(f"{json.dumps(e.model.model_dump(mode='json'))}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
