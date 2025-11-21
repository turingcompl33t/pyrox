import logging
import sys

import pyrox.models as models
from pyrox.client import Hyrox


def main() -> int:
    logging.basicConfig(level=logging.DEBUG)

    client = Hyrox()

    # get divisions for chicago 2025
    divisions = client.divisions("chicago_2025")

    # find the elite men
    elite_men = [d for d in divisions if d.model.name == models.DivisionName.ELITE_MEN][
        0
    ]

    # get the rankings
    rankings = elite_men.rankings()
    for r in rankings:
        print(r.model_dump_json(indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
