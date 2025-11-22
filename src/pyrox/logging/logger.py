"""
Logging utilities.
"""

import logging
from typing import Any


def create_logger(name: str = "pyrox", level: Any = logging.ERROR) -> logging.Logger:
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
