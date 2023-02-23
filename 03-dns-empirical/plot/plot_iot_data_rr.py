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
import yaml

try:
    from . import plot_common as pc
    from . import plot_iot_data_name_lens as name_len
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_iot_data_name_lens as name_len

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

COLORS = {
    "A": "#e31a1c",
    "AAAA": "#fb9a99",
    "DS": "#8dd3c7",
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
    "RRSIG": "#bc80bd",
    "Others": "#cccccc",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    parser.add_argument("iot_data_csvs", nargs="+")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0],
        matplotlib.rcParams["figure.figsize"][0],
    )
    args.iot_data_csvs = sorted(set(args.iot_data_csvs))
    data_src = []
    for iot_data_csv in args.iot_data_csvs:
        for doi in name_len.DOI_TO_NAME.keys():
            if doi in iot_data_csv.lower():
                data_src.append(name_len.DOI_TO_NAME[doi])
    assert data_src, "Data source can not inferred from CSV name"
    data_src = "+".join(sorted(data_src))
    othersfile = os.path.join(pc.DATA_PATH, "iot-data-rr-others.yaml")
    try:
        with open(othersfile) as others:
            others_lists = yaml.load(others, Loader=yaml.Loader)
    except FileNotFoundError:
        others_lists = dict()
    for filt_name, filt in name_len.FILTERS:
        if "ixp" in data_src and filt_name not in [
            "all",
            "qrys_only",
            "qd_only",
            "qd_an_only",
        ]:
            continue
        if "iotfinder" in data_src and "qrys_only" in filt_name:
            continue
        record_types = None
        for iot_data_csv in args.iot_data_csvs:
            df = pandas.read_csv(iot_data_csv)
            df = name_len.filter_data_frame(df, filt)
            if "ixp" in data_src:
                df = df[
                    (df["class"] == "IN")
                    | (df["class"] == 0x8001)
                    | (df["class"] == "ANY")
                ]
            series = df.groupby("type")["type"].count().sort_values(ascending=False)
            if record_types is None:
                record_types = series
            else:
                record_types = pandas.concat([record_types, series], axis=1).sum(axis=1)
            del df
        total = record_types.sum()
        record_types.index = [
            idx if idx not in ["ALL", "65"] else "ANY" if idx == "ALL" else "HTTPS"
            for idx in record_types.index
        ]
        # group all under 1% to others
        specific = record_types[(record_types / total) > 0.01].copy()
        if specific.size < (record_types.size - 1):
            others_series = record_types[(record_types / total) < 0.01]
            others = pandas.Series(others_series.sum(), index=["Others"])
            if data_src not in others_lists:
                others_lists[data_src] = {}
            others_lists[data_src][filt_name] = {
                k: float(others_series[k] / total * 100) for k in others_series.index
            }
            with open(othersfile, "w") as othersf:
                yaml.dump(others_lists, othersf)
            record_types = pandas.concat([specific, others])
        colors = [COLORS[i] for i in record_types.index]
        record_types.plot.pie(autopct="%.1f\\%%", colors=colors, pctdistance=0.85)
        matplotlib.pyplot.ylabel("")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(pc.DATA_PATH, f"iot-data-rr-{filt_name}@{data_src}.{ext}"),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":  # pragma: no cover
    main()
