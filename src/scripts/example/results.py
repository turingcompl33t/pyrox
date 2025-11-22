"""
Get results for a specific race.
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

    # get elite men's race
    results = chicago.results(models.DivisionName.ELITE_MEN)
    print(len(results))

    return 0


if __name__ == "__main__":
    sys.exit(main())
