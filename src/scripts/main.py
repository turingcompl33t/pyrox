import logging
import sys

from pyrox.client import Hyrox


def main() -> int:
    logging.basicConfig(level=logging.DEBUG)

    client = Hyrox()

    # get divisions for chicago 2025
    ds = client.divisions("chicago_2025")
    print(len(ds))

    return 0


if __name__ == "__main__":
    sys.exit(main())
