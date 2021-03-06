"""
    nemreader.outputs
    ~~~~~
    Output results in different formats
"""

import os
import logging
import csv
from typing import Generator, Tuple, List, Dict, Any
from pathlib import Path
import pandas as pd
from .nem_objects import Reading
from .nem_reader import read_nem_file

log = logging.getLogger(__name__)


def nmis_in_file(file_name) -> Generator[Tuple[str, List[str]], None, None]:
    """ Return list of NMIs in file """
    m = read_nem_file(file_name)
    for nmi in m.transactions.keys():
        suffixes = list(m.transactions[nmi].keys())
        yield nmi, suffixes


def flatten_rows(
    nmi_transactions: Dict[str, list], nmi_readings: Dict[str, List[Reading]]
) -> Tuple[List[str], List[list]]:
    """ Create flattened list of NMI reading data """

    channels = list(nmi_transactions.keys())

    headings = ["period_start", "period_end"]
    for channel in channels:
        headings.append(channel)
    headings.append("quality_method")
    headings.append("event")

    rows = []
    num_records = len(nmi_readings[channels[0]])
    first_ch = channels[0]
    for i in range(0, num_records):
        t_start = nmi_readings[first_ch][i].t_start
        t_end = nmi_readings[first_ch][i].t_end
        quality_method = nmi_readings[first_ch][i].quality_method
        event_code = nmi_readings[first_ch][i].event_code
        event_desc = nmi_readings[first_ch][i].event_desc
        row: List[Any] = [t_start, t_end]
        for ch in channels:
            try:
                val = nmi_readings[ch][i].read_value
            except IndexError:
                val = None
            row.append(val)
        row.append(quality_method)
        row.append(f"{event_code} {event_desc}")
        rows.append(row)
    return headings, rows


def output_as_data_frames(file_name):
    """ Return list of data frames for each NMI """

    m = read_nem_file(file_name)
    nmis = list(m.readings.keys())
    data_frames = []
    for nmi in nmis:
        headings, rows = flatten_rows(m.transactions[nmi], m.readings[nmi])
        nmi_df = pd.DataFrame(data=rows, columns=headings)
        data_frames.append((nmi, nmi_df))

    return data_frames


def output_as_csv(file_name, output_dir="."):
    """
    Transpose all channels and output a csv that is easier
    to read and do charting on

    :param file_name: The NEM file to process
    :param output_dir: Specify different output location
    :returns: The file that was created
    """

    output_dir = Path(output_dir)
    output_paths = []
    os.makedirs(output_dir, exist_ok=True)
    m = read_nem_file(file_name)
    nmis = m.readings.keys()
    for nmi in nmis:
        headings, rows = flatten_rows(m.transactions[nmi], m.readings[nmi])
        last_date = rows[-1][1]
        output_file = "{}_{}_transposed.csv".format(nmi, last_date.strftime("%Y%m%d"))
        output_path = output_dir / output_file
        with open(output_path, "w", newline="") as csvfile:
            cwriter = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            cwriter.writerow(headings)
            for row in rows:
                cwriter.writerow(row)

        log.debug("Created %s", output_path)
        output_paths.append(output_path)
    return output_paths
