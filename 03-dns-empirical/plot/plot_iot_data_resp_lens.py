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
import matplotlib.ticker
import numpy
import pandas

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


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    parser = argparse.ArgumentParser()
    parser.add_argument("iot_data_csvs", nargs="+")
    args = parser.parse_args()
    args.iot_data_csvs = sorted(set(args.iot_data_csvs))
    data_src = []
    data_src = []
    for iot_data_csv in args.iot_data_csvs:
        for doi in name_len.DOI_TO_NAME.keys():
            if doi in iot_data_csv.lower():
                data_src.append(name_len.DOI_TO_NAME[doi])
    assert data_src, "Data source can not inferred from CSV name"
    data_src = "+".join(sorted(data_src))
    for filt_name, filt in name_len.FILTERS:
        if "qd_an_only" in filt_name or "qrys_only" in filt_name:
            continue
        if "ixp" in data_src and filt_name != "all":
            continue
        resp_lens = None
        for iot_data_csv in args.iot_data_csvs:
            df = pandas.read_csv(iot_data_csv)
            df = name_len.filter_data_frame(df, filt)
            df = df[df["msg_type"] == "response"].groupby(["pcap_name", "frame_no"])
            series = df["msg_len"].last()
            if resp_lens is None:
                resp_lens = series
            else:
                resp_lens = pandas.concat([resp_lens, series], ignore_index=True)
            del df
        if resp_lens.size == 0:
            continue
        bins = resp_lens.max() - resp_lens.min()
        assert bins == int(bins)
        bins = int(bins)
        too_long = resp_lens[resp_lens > 1500]
        if too_long.size:
            print(
                filt_name,
                "WILL NOT BE PLOTTED!",
                ", ".join(str(i) for i in sorted(too_long.unique())),
            )
        resp_lens.hist(bins=bins, density=True, histtype="step")
        ax = matplotlib.pyplot.gca()
        ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(10))
        ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.01))
        matplotlib.pyplot.xticks(numpy.arange(0, 1501, 100))
        matplotlib.pyplot.yticks(numpy.arange(0, 0.2, 0.1))
        # label only every other major locator
        for i, label in enumerate(ax.xaxis.get_ticklabels()):
            if i % 2:
                label.set_visible(False)
        matplotlib.pyplot.xlim((0, 1500))
        matplotlib.pyplot.xlabel("Response length [bytes]")
        matplotlib.pyplot.ylim((-0.001, 0.11))
        matplotlib.pyplot.ylabel("Density")
        matplotlib.pyplot.tight_layout()
        matplotlib.pyplot.grid(True, which="minor", linewidth=0.25)
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH, f"iot-data-resp-lens-{filt_name}@{data_src}.{ext}"
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()
        del resp_lens


if __name__ == "__main__":  # pragma: no cover
    main()
