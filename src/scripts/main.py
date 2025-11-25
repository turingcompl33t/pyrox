import logging
import sys
from pathlib import Path

import humanize

import pyrox.models as models
from pyrox.client import Hyrox
from pyrox.jobs.loader import MultiDivisionLoader
from pyrox.logging import create_logger


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    loader = MultiDivisionLoader(client)
    duration = loader.load(
        "chicago_2025",
        {models.DivisionName.ELITE_WOMEN, models.DivisionName.PRO_WOMEN},
        Path.cwd() / "results.csv",
        athlete=True,
        splits=True,
        retry=16,
    )
    print(f"complete in {humanize.precisedelta(duration)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
