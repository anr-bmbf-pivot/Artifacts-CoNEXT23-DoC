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
except ImportError:
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
        "no_mdns_qd_an_only",
        lambda df: (df["transport"] != "MDNS")
        & ((df["section"] == "qd") | (df["section"] == "an")),
    ),
]


def filter_data_frame(df, filt=None):
    if filt is None:
        return df
    else:
        return df[filt(df)]


def _len(name):
    return len(name) - 1


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    parser = argparse.ArgumentParser()
    parser.add_argument("iot_data_csv")
    args = parser.parse_args()
    for filt_name, filt in FILTERS:
        df = pandas.read_csv(args.iot_data_csv)
        df = filter_data_frame(df, filt)
        name_lens = pandas.Series(
            [_len(name) for name in df["name"].str.lower().unique()]
        )
        bins = name_lens.max() - name_lens.min()
        name_lens.hist(bins=bins, density=True, histtype="step")
        matplotlib.pyplot.xticks(numpy.arange(0, 86, 5))
        matplotlib.pyplot.xlim((0, 85))
        matplotlib.pyplot.xlabel("Name length [characters]")
        matplotlib.pyplot.ylim((-0.01, 0.2))
        matplotlib.pyplot.ylabel("Density")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH,
                    f"iot-data-name-lens-{filt_name}.{ext}",
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":
    main()
