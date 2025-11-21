"""
The base scraper implementation.
"""

import logging


class BaseScraper:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
