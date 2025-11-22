import logging
import sys
from datetime import datetime
from typing import Any

import pyrox.models as models
from pyrox.client import Hyrox


def _create_logger(name: str = "pyrox", level: Any = logging.ERROR) -> logging.Logger:
    """
    Create a logger for the miner instance.
    :param name: The name of the logger
    :param verbosity: The requested verbosity level
    :return: The logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    logger.addHandler(ch)
    return logger


def main() -> int:
    client = Hyrox(_create_logger(level=logging.DEBUG))

    # get events in 24/25 season (roughly)
    events = client.events(
        after=datetime(day=1, month=7, year=2024),
        before=datetime(day=1, month=7, year=2025),
    )
    print(len(events))

    # get the chicago event
    chicago = client.event("chicago_2025")

    # get elite men's race
    results = chicago.results(models.DivisionName.ELITE_MEN)
    print(len(results))

    # get Rich's results
    rich = chicago.result(models.DivisionName.ELITE_MEN, "Rich Ryan", splits=True)
    assert rich.model.splits is not None
    print(rich.model.splits.pretty())

    return 0


if __name__ == "__main__":
    sys.exit(main())
