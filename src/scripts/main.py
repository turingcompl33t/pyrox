import logging
import sys
from pathlib import Path

import pyrox.models as models
from pyrox.client import Hyrox
from pyrox.jobs.loader import MultiEventLoader
from pyrox.logging import create_logger


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    loader = MultiEventLoader(client)
    loader.load(
        {"chicago_2025", "glasgow_2025"},
        {models.DivisionName.ELITE_MEN},
        Path.cwd() / "results.csv",
        splits=True,
        profile=True,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
