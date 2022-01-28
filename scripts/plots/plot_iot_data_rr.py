#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import argparse
import os

import matplotlib.pyplot
import pandas

try:
    from . import plot_common as pc
    from . import plot_iot_data_name_lens as name_len
except ImportError:
    import plot_common as pc
    import plot_iot_data_name_lens as name_len

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

COLORS = {
    "A": "#e31a1c",
    "AAAA": "#fb9a99",
    "NS": "#b2df8a",
    "PTR": "#fdbf6f",
    "NSEC": "#33a02c",
    "SRV": "#a6cee3",
    "TXT": "#1f78b4",
    "CNAME": "#ff7f00",
    "OPT": "#cab2d6",
    "SOA": "#6a3d9a",
    "ANY": "#ffff99",
    "HTTPS": "#b15928",
    "Others": "#cccccc",
}


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0],
        matplotlib.rcParams["figure.figsize"][0],
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--ixp", help="Name of the IXP", default=None)
    parser.add_argument("iot_data_csv")
    args = parser.parse_args()
    assert args.ixp is None or args.iot_data_csv.endswith(
        "csv.gz"
    ), "No IXP name provided, but IXP data at hand"
    for filt_name, filt in name_len.FILTERS:
        if filt_name not in ["all", "qrys_only", "qd_an_only"] and args.ixp is not None:
            continue
        df = pandas.read_csv(args.iot_data_csv)
        if "name_len" in df.head():
            assert args.ixp is not None, "No IXP name provided, but IXP data at hand"
        df = name_len.filter_data_frame(df, filt)
        if args.ixp:
            df = df[
                (df["class"] == "IN") | (df["class"] == 0x8001) | (df["class"] == "ANY")
            ]
        record_types = df.groupby("type")["type"].count().sort_values(ascending=False)
        total = record_types.sum()
        record_types.index = [
            idx if idx not in ["ALL", "65"] else "ANY" if idx == "ALL" else "HTTPS"
            for idx in record_types.index
        ]
        # group all under 2% to others
        specific = record_types[(record_types / total) > 0.01].copy()
        if specific.size < (record_types.size - 1):
            others_series = record_types[(record_types / total) < 0.01]
            others = pandas.Series(others_series.sum(), index=["Others"])
            print(filt_name, "Others:", ", ".join(others_series.index))
            record_types = pandas.concat([specific, others])
        colors = [COLORS[i] for i in record_types.index]
        record_types.plot.pie(autopct="%.1f\\%%", colors=colors, pctdistance=0.85)
        matplotlib.pyplot.ylabel("")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH,
                    f"iot-data-rr-{filt_name}%s.{ext}"
                    % (f"@{args.ixp}" if args.ixp else ""),
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":
    main()
