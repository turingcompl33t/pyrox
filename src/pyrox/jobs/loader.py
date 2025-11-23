"""
Results loading jobs.
"""

from pathlib import Path

import pyrox.models as models
from pyrox.client import Hyrox
from pyrox.io import ResultsWriter


class ResultsLoader:
    """A class for downloading results to a file."""

    def __init__(self, client: Hyrox) -> None:
        # the client
        self.client = client
        # inherit the client's logger
        self.logger = self.client.logger

    def load(
        self,
        event_name: str,
        division_name: models.DivisionName,
        path: Path,
        athlete: bool = False,
        splits: bool = False,
    ) -> None:
        """
        Load results from the specified event and division.
        :param event_name: The name of the event
        :param division_name: The name of the division
        :param path: The path to which results are written
        :param athlete: Load with athlete data
        :param splits: Load with splits
        """
        results = self.client.results(
            event_name,
            division_name,
            athlete=athlete,
            splits=splits,
        )

        writer = ResultsWriter(event_name, division_name)
        writer.write([r.model for r in results], path)


class MultiDivisionLoader:
    """Download results from multiple divisions at the same event."""

    def __init__(self, client: Hyrox) -> None:
        # the client
        self.client = client
        # inherit the client's logger
        self.logger = self.client.logger

    def load(
        self,
        event_name: str,
        division_names: set[models.DivisionName],
        path: Path,
        athlete: bool = False,
        splits: bool = False,
    ) -> None:
        """
        Load results from the specified divisions at the specified event.
        :param event_name: The name of the event
        :param division_names: The names of the divisions
        :param path: The path to which results are written
        :param athlete: Load with athlete data
        :param splits: Load with splits
        """
        # write results for all requested divisions
        for i, division_name in enumerate(division_names):
            try:
                division_results = self.client.results(
                    event_name, division_name, athlete=athlete, splits=splits
                )
            except RuntimeError:
                self.logger.warning(
                    f"failed to load results for division '{division_name}'"
                )
                continue

            writer = ResultsWriter(event_name, division_name)
            writer.write([r.model for r in division_results], path, append=i > 0)


class MultiEventLoader:
    """Download results from multiple events."""

    def __init__(self, client: Hyrox) -> None:
        # the client
        self.client = client
        # inherit the client's logger
        self.logger = self.client.logger

    def load(
        self,
        event_names: set[str],
        division_names: set[models.DivisionName],
        path: Path,
        athlete: bool = False,
        splits: bool = False,
    ) -> None:
        """
        Load results from the specified divisions at the specified event.
        :param event_names: The names of the event
        :param division_name: The names of the divisions
        :param path: The path to which results are written
        :param athlete: Load with athlete data
        :param splits: Load with splits
        """
        for i, event_name in enumerate(event_names):
            for j, division_name in enumerate(division_names):
                try:
                    results = self.client.results(
                        event_name, division_name, athlete=athlete, splits=splits
                    )
                except RuntimeError:
                    self.logger.warning(
                        f"failed to load results for division '{division_name}' at event '{event_name}'"
                    )
                    continue

                writer = ResultsWriter(event_name, division_name)
                writer.write([r.model for r in results], path, append=(i + j) > 0)
