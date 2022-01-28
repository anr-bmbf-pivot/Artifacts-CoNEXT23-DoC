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
    from . import plot_iot_data_name_lens as name_len
except ImportError:
    import plot_common as pc
    import plot_iot_data_name_lens as name_len

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--ixp", help="Name of the IXP", default=None)
    parser.add_argument("iot_data_csv")
    args = parser.parse_args()
    assert args.ixp is None or args.iot_data_csv.endswith(
        "csv.gz"
    ), "No IXP name provided, but IXP data at hand"
    for filt_name, filt in name_len.FILTERS:
        if "qd_an_only" in filt_name:
            continue
        if filt_name != "all" and args.ixp is not None:
            continue
        df = pandas.read_csv(args.iot_data_csv)
        if "name_len" in df.head():
            assert args.ixp is not None, "No IXP name provided, but IXP data at hand"
        df = name_len.filter_data_frame(df, filt)
        df = df[df["msg_type"] == "response"].groupby(["pcap_name", "frame_no"])
        resp_lens = df["msg_len"].last()
        if resp_lens.size == 0:
            continue
        bins = resp_lens.max() - resp_lens.min()
        assert bins == int(bins)
        bins = int(bins)
        too_long = resp_lens[resp_lens > 550]
        if too_long.size:
            print(
                filt_name,
                "WILL BE NOT PLOTTED!",
                ", ".join(str(i) for i in sorted(too_long.unique())),
            )
        resp_lens.hist(bins=bins, density=True, histtype="step")
        matplotlib.pyplot.xticks(numpy.arange(0, 551, 50))
        matplotlib.pyplot.xlim((0, 550))
        matplotlib.pyplot.xlabel("Response length [bytes]")
        matplotlib.pyplot.ylim((-0.01, 0.3))
        matplotlib.pyplot.ylabel("Density")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH,
                    f"iot-data-resp-lens-{filt_name}%s.{ext}"
                    % (f"@{args.ixp}" if args.ixp else ""),
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":
    main()
