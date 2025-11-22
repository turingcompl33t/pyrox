"""
Get a race result for a specific athlete.
"""

import logging
import sys

import pyrox.models as models
from pyrox.client import Hyrox
from pyrox.logging import create_logger


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    # get the chicago event
    chicago = client.event("chicago_2025")

    # get Rich Ryan's results
    rich = chicago.result(models.DivisionName.ELITE_MEN, "Rich Ryan", splits=True)
    assert rich.model.splits is not None
    print(rich.model.splits.pretty())

    return 0


if __name__ == "__main__":
    sys.exit(main())
