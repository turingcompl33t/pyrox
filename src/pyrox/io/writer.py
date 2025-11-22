"""
Results writer.
"""

import csv
from pathlib import Path

import pyrox.models as models


class ResultsWriter:
    """A simple writer for results."""

    def __init__(
        self, event: str | None = None, division: models.DivisionName | None = None
    ) -> None:
        # the name of the event for which results are written
        self.event = event
        # the name of the division for which results are written
        self.division = division

    def write(
        self,
        results: list[models.Result],
        path: Path,
        append: bool = False,
        force: bool = False,
    ) -> None:
        """
        Write the provided results to a CSV file at `path`.
        :param results: The results to write
        :param path: The path to which results are written
        :param append: Append to the file instead of
        :param force: Overwrite existing file
        """
        if path.exists():
            if not append and not force:
                raise RuntimeError(
                    f"file at path {path} already exists and not appending"
                )

            # remove the existing file if forcing an overwrite
            if not append and force:
                path.unlink()

        mode = "a" if append else "w"
        with path.open(mode, newline="") as f:
            writer = csv.writer(f)
            # write the header if not appending
            if not append:
                writer.writerow(_write_header())
            writer.writerows(
                [_write_row(self.event, self.division, result) for result in results]
            )


def _write_header() -> list[str]:
    """Write the header row."""
    headers_splits_run = [f"run_{i + 1}" for i in range(8)]
    header_splits_station = [str(name) for name in models.Station]
    return (
        [
            "event_name",
            "division_name",
            "athlete_name",
            "age_group",
            "position",
            "position_ag",
            "finish_time",
            "analysis_url",
            "has_splits",
        ]
        + headers_splits_run
        + header_splits_station
        + ["has_profile", "profile_url"]
    )


def _write_row(
    event: str | None, division: models.DivisionName | None, result: models.Result
) -> list[str]:
    """
    Serialize all data for a row.
    :param event: The event name
    :param division: The division name
    :param result: The result
    :return: The serialized row
    """
    # event_name, division_name, ...results
    return [
        event if event is not None else "unknown",
        str(division) if division is not None else "unknown",
    ] + _result_to_row(result)


def _result_to_row(r: models.Result) -> list[str]:
    """
    Convert a result to a row for writing.
    :param r: The result
    :return: The serialized row
    """

    # serialize run splits
    run_splits = (
        [str(split.seconds) for split in r.splits.runs]
        if r.splits is not None
        else [str(0)] * 8
    )
    # serialize station splits
    station_splits = (
        [str(r.splits.stations[name].seconds) for name in models.Station]
        if r.splits is not None
        else [str(0)] * 8
    )

    # name, ag, position, position_ag, finish_time, analysis_url, has_splits, ...run_splits..., ...station_splits..., has_profile, profile
    return (
        [
            r.name,
            str(r.age_group) if r.age_group is not None else "unknown",
            str(r.position),
            str(r.position_ag) if r.position_ag is not None else "unknown",
            str(r.time.seconds),
            str(r.url),
            "true" if r.splits is not None else "false",
        ]
        + run_splits
        + station_splits
        + [
            "true" if r.profile is not None else "false",
            str(r.profile) if r.profile is not None else "n/a",
        ]
    )
