"""
I/O example.
"""

import logging
import sys
from pathlib import Path

import pyrox.models as models
from pyrox.client import Hyrox
from pyrox.io import ResultsReader
from pyrox.jobs.loader import MultiEventLoader
from pyrox.logging import create_logger


def main() -> int:
    client = Hyrox(create_logger(level=logging.DEBUG))

    save_path = Path.cwd() / "results.csv"

    # load and write results
    loader = MultiEventLoader(client)
    loader.load(
        {"chicago_2025", "glasgow_2025"},
        {models.DivisionName.ELITE_MEN},
        save_path,
        athlete=True,
        splits=True,
    )

    # read back the results
    reader = ResultsReader()
    results = reader.read(save_path)
    print(len(results))

    return 0


if __name__ == "__main__":
    sys.exit(main())
