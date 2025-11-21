import logging
import sys

import humanize

import pyrox.models as models
from pyrox.client import Hyrox


def main() -> int:
    logging.basicConfig(level=logging.ERROR)

    client = Hyrox()

    # get elite men for chicago 2025
    elite_men = client.division("chicago_2025", models.DivisionName.ELITE_MEN)
    assert elite_men is not None

    # find rich in rankings
    rich = elite_men.ranking("Rich Ryan")
    assert rich is not None

    # get race data for rich
    result = rich.result(retry=16)
    print(humanize.precisedelta(result.model.total_time))

    return 0


if __name__ == "__main__":
    sys.exit(main())
