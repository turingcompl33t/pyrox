"""
Results I/O.
"""

import csv
from datetime import timedelta
from pathlib import Path

from pydantic import HttpUrl

import pyrox.models as models


class ResultsReader:
    """A simple reader for results."""

    def __init__(self) -> None:
        pass

    def read(self, path: Path) -> list[tuple[str, models.DivisionName, models.Result]]:
        """
        Read results from the file at `path`.
        :param path: The path to the saved results file
        :return: The list of results
        """
        if not path.is_file():
            raise ValueError(f"file at path {path} not found")

        with path.open("r") as f:
            reader = csv.DictReader(f)
            return [_read_row(row) for row in reader]


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
            "athlete_canonical_name",
            "athlete_profile_url",
            "age_group",
            "position",
            "position_ag",
            "finish_time",
            "analysis_url",
            "has_splits",
        ]
        + headers_splits_run
        + header_splits_station
        + ["roxzone"]
    )


def _read_row(row: dict[str, str]) -> tuple[str, models.DivisionName, models.Result]:
    """
    Deserialize data from a row.
    :param row: The row data
    :return: (event name, division name, deserialized result)
    """
    return (
        row["event_name"],
        models.DivisionName(row["division_name"]),
        _row_to_result(row),
    )


def _row_to_result(row: dict[str, str]) -> models.Result:
    """
    Read row data to a result.
    :param row: Row data
    :return: Deserialized result
    """
    athlete = models.AthleteRef(
        name=row["athlete_name"],
        canonical_name=(
            row["athlete_canonical_name"]
            if row["athlete_canonical_name"] != "unknown"
            else None
        ),
        profile_url=(
            HttpUrl(row["athlete_profile_url"])
            if row["athlete_profile_url"] != "unknown"
            else None
        ),
    )

    splits = (
        models.Splits(
            runs=[timedelta(seconds=int(row[f"run_{i + 1}"])) for i in range(8)],
            stations={
                name: timedelta(seconds=int(row[name])) for name in models.Station
            },
            roxzone=timedelta(seconds=int(row["roxzone"])),
        )
        if bool(row["has_splits"])
        else None
    )

    return models.Result(
        athlete=athlete,
        position=int(row["position"]),
        position_ag=(
            int(row["position_ag"]) if row["position_ag"] != "unknown" else None
        ),
        age_group=(
            models.AgeGroup(row["age_group"]) if row["age_group"] != "unknown" else None
        ),
        time=timedelta(seconds=int(row["finish_time"])),
        url=HttpUrl(row["analysis_url"]),
        splits=splits,
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

    # athlete_name, athlete_canonical_name, athlete_profile_url,
    # ag, position, position_ag, finish_time,
    # has_splits, ...run_splits..., ...station_splits..., roxzone
    return (
        [
            r.athlete.name,
            (
                r.athlete.canonical_name
                if r.athlete.canonical_name is not None
                else "unknown"
            ),
            (
                str(r.athlete.profile_url)
                if r.athlete.profile_url is not None
                else "unknown"
            ),
            str(r.age_group) if r.age_group is not None else "unknown",
            str(r.position),
            str(r.position_ag) if r.position_ag is not None else "unknown",
            str(r.time.seconds),
            str(r.url),
            "true" if r.splits is not None else "false",
        ]
        + run_splits
        + station_splits
        + [str(r.splits.roxzone.seconds) if r.splits is not None else str(0)]
    )
