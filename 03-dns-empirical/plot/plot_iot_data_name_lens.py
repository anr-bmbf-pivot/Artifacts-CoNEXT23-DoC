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
import numpy
import pandas

try:
    from . import plot_common as pc
except ImportError:  # pragma: no cover
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

FILTERS = [
    ("all", None),
    (
        "qrys_only",
        lambda df: (df["section"] == "qd") & (df["msg_type"] == "query"),
    ),
    (
        "qd_only",
        lambda df: df["section"] == "qd",
    ),
    (
        "qd_an_only",
        lambda df: (df["section"] == "qd") | (df["section"] == "an"),
    ),
    ("no_mdns", lambda df: df["transport"] != "MDNS"),
    (
        "no_mdns_qrys_only",
        lambda df: (df["transport"] != "MDNS")
        & (df["section"] == "qd")
        & (df["msg_type"] == "query"),
    ),
    (
        "no_mdns_qd_only",
        lambda df: (df["transport"] != "MDNS") & (df["section"] == "qd"),
    ),
    (
        "no_mdns_qd_an_only",
        lambda df: (df["transport"] != "MDNS")
        & ((df["section"] == "qd") | (df["section"] == "an")),
    ),
]
DOI_TO_NAME = {
    "10.1109-eurosp48549.2020.00037": "iotfinder",
    "10.1109-sp.2019.00013": "yourthings",
    "10.1145-3355369.3355577": "moniotr",
    "dns_packets_ixp_2022_week": "ixp",
    "iotfinder": "iotfinder",
    "moniotr": "moniotr",
    "yourthings": "yourthings",
}


def filter_data_frame(df, filt=None):
    df = df[df["transport"] != "DoTCP"]
    if filt is None:
        return df
    else:
        return df[filt(df)]


def _len(name):
    """
    >>> _len("example.org.")
    11
    """
    name_len = len(name) - 1
    return name_len


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    parser.add_argument("iot_data_csvs", nargs="+")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0] * 1.1,
        matplotlib.rcParams["figure.figsize"][1] * 0.7,
    )
    args.iot_data_csvs = sorted(set(args.iot_data_csvs))
    data_src = []
    for iot_data_csv in args.iot_data_csvs:
        for doi in DOI_TO_NAME.keys():
            if doi in iot_data_csv.lower():
                data_src.append(DOI_TO_NAME[doi])
    assert data_src, "Data source can not inferred from CSV name"
    data_src = "+".join(sorted(data_src))
    statsfile = os.path.join(pc.DATA_PATH, "iot-data-name-lens-stats.csv")
    try:
        stats = pandas.read_csv(statsfile, index_col=["data_src", "filter"])
    except FileNotFoundError:
        stats = None
    for filt_name, filt in FILTERS:
        if "ixp" in data_src and filt_name not in ["qrys_only", "qd_only"]:
            continue
        if "iotfinder" in data_src and "qrys_only" in filt_name:
            continue
        name_lens = None
        for iot_data_csv in args.iot_data_csvs:
            df = pandas.read_csv(iot_data_csv)
            df = filter_data_frame(df, filt)
            if "name_len" in df.head():
                series = pandas.Series(df["name_len"])
            else:
                series = pandas.Series(
                    [_len(name) for name in df["name"].str.lower().unique()]
                )
            if name_lens is None:
                name_lens = series
            else:
                name_lens = pandas.concat([name_lens, series], ignore_index=True)
            del df
        bins = name_lens.max() - name_lens.min()
        assert bins == int(bins)
        bins = int(bins)
        name_lens.hist(
            bins=bins,
            density=True,
            linewidth=0.25,
            edgecolor="black",
            facecolor="#80b1d3",
        )
        matplotlib.pyplot.gca().set_axisbelow(True)
        matplotlib.pyplot.xticks(numpy.arange(0, 86, 5))
        matplotlib.pyplot.xlim((0, 85))
        matplotlib.pyplot.xlabel("Name length [characters]")
        matplotlib.pyplot.ylim((0, 0.08))
        matplotlib.pyplot.yticks(numpy.arange(0, 0.09, 0.02), numpy.arange(0, 9, 2))
        matplotlib.pyplot.ylabel(r"Density [\%]")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH, f"iot-data-name-lens-{filt_name}@{data_src}.{ext}"
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        stats_list = [
            [
                name_lens.min(),
                name_lens.max(),
                name_lens.mean(),
                name_lens.std(),
                name_lens.mode().max(),
                float(name_lens.quantile([0.25])),
                name_lens.median(),
                float(name_lens.quantile([0.75])),
            ]
        ]
        idx = pandas.MultiIndex.from_arrays(
            [[data_src], [filt_name]], names=["data_src", "filter"]
        )
        if stats is not None and (data_src, filt_name) in list(stats.index.values):
            stats.loc[idx, :] = stats_list[0]
        else:
            filt_stats = pandas.DataFrame(
                stats_list,
                columns=["min", "max", "μ", "σ", "mode", "Q1", "Q2", "Q3"],
                index=idx,
            )
            stats = pandas.concat([stats, filt_stats], join="inner")
        stats.to_csv(statsfile)
        matplotlib.pyplot.clf()
        del name_lens


if __name__ == "__main__":  # pragma: no cover
    main()
