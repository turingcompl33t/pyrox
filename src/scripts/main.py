import logging
import sys
from pathlib import Path

import humanize

import pyrox.models as models
from pyrox.client import Hyrox
from pyrox.jobs.loader import MultiDivisionLoader
from pyrox.logging import create_logger
from pyrox.scrapers.splits import SplitsScraper


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    # loader = MultiDivisionLoader(client)
    # duration = loader.load(
    #     "chicago_2025",
    #     {models.DivisionName.ELITE_MEN, models.DivisionName.PRO_MEN},
    #     Path.cwd() / "results.csv",
    #     athlete=True,
    #     splits=True,
    # )
    # print(f"complete in {humanize.precisedelta(duration)}")

    # chicago = client.event("chicago_2025")
    # harry = chicago.result(models.DivisionName.PRO_MEN, "Harry Thompson", athlete=True)
    # print(harry)

    return 0


if __name__ == "__main__":
    sys.exit(main())
