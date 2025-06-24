"""
Module for parsing avro data
"""

from pathlib import Path

import pandas as pd
from fastavro import reader


def load_avro(avro_path: Path) -> list[dict]:
    """
    Load the avro file into a pandas DataFrame.

    :param avro_path: Avro file to load.
    :return: DataFrame of data.
    """

    records = []
    with open(avro_path, "rb") as avro_f:
        avro_reader = reader(avro_f)
        for record in avro_reader:
            records.append(record)

    return records


def convert_avro_list_to_df(records: list[dict]) -> pd.DataFrame:
    """
    Convert a list of dictionaries to a pandas DataFrame.

    :param data: List of dictionaries to convert.
    :return: DataFrame of data.
    """
    unpacked = []

    for record in records:
        new = {}

        for field in [
            "objectid",
            "cutout_science",
            "cutout_template",
            "cutout_difference",
        ]:
            new[field] = record[field]

        # Backwards compatibility for old avro files
        if "fieldid" not in record["candidate"]:
            record["candidate"]["fieldid"] = record["candidate"]["field"]

        # Prepend the latest observation to the history
        latest = pd.DataFrame(
            [{x: record["candidate"][x]
              for x in record["candidate"].keys()
              if x != "prv_candidates"}]
        )
        hist = pd.concat(
            [pd.DataFrame(record["prv_candidates"]), latest], axis=0, ignore_index=True
        )
        new["prv_candidates"] = hist

        for field in record["candidate"]:
            new[field] = record["candidate"][field]

        unpacked.append(new)

    res = pd.DataFrame(unpacked)

    return res


def load_avro_as_df(avro_path: Path) -> pd.DataFrame:
    """
    """
    records = load_avro(avro_path)
    return convert_avro_list_to_df(records)
