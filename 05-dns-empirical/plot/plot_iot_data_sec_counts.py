#! /usr/bin/env python
#
# Copyright (C) 2021 Freie Universität Berlin
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
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_iot_data_name_lens as name_len

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


SECTIONS = ["qdcount", "ancount", "nscount", "arcount"]
SECTION_COLORS = {
    "qdcount": "C0",
    "ancount": "C1",
    "nscount": "C2",
    "arcount": "C3",
}
SECTIONS_READABLE = {
    "qdcount": "Questions",
    "ancount": "Answers",
    "nscount": "Authorities",
    "arcount": "Additionals",
}
# SEC_FILTERS = [
#     (
#         "no_mdns_no_xiaomi",
#         lambda df: (df["transport"] != "MDNS")
#         & (df["name"] != "mi.com.")
#         & (df["name"] != "ot.io.mi.com."),
#     )
# ]


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    parser = argparse.ArgumentParser()
    parser.add_argument("iot_data_csvs", nargs="+")
    args = parser.parse_args()
    args.iot_data_csvs = sorted(set(args.iot_data_csvs))
    data_src = []
    for iot_data_csv in args.iot_data_csvs:
        for doi in name_len.DOI_TO_NAME.keys():
            if doi in iot_data_csv.lower():
                data_src.append(name_len.DOI_TO_NAME[doi])
    assert data_src, "Data source can not inferred from CSV name"
    data_src = "+".join(sorted(data_src))
    for filt_name, filt in name_len.FILTERS:
        if (
            "qrys_only" in filt_name
            or "qd_an_only" in filt_name
            or "qd_only" in filt_name
        ):
            continue
        if "ixp" in data_src and "no_mdns" in filt_name:
            continue
        df = None
        for iot_data_csv in args.iot_data_csvs:
            tmp = pandas.read_csv(iot_data_csv)
            tmp = name_len.filter_data_frame(tmp, filt)
            tmp = tmp[tmp["msg_type"] == "response"]
            if df is None:
                df = tmp
            else:
                df = pandas.concat([df, tmp], ignore_index=True)
            del tmp
        for sec in SECTIONS:
            section = (
                df[["pcap_name", "frame_no", sec]]
                .groupby(["pcap_name", "frame_no"])
                .min()
            )
            section = section.reset_index()[sec]
            if section.max() == section.min():
                bins = numpy.arange(section.min(), section.max() + 2)
            else:
                bins = section.max() - section.min()
            if numpy.isnan(bins).any():
                continue
            section.hist(
                bins=bins,
                density=True,
                histtype="step",
                label=SECTIONS_READABLE[sec],
                color=SECTION_COLORS[sec],
                alpha=0.9,
            )
            del section
        del df
        matplotlib.pyplot.legend(loc="upper right", ncol=2)
        matplotlib.pyplot.xticks(numpy.arange(0, 31, 3))
        matplotlib.pyplot.xlim((0, 30))
        matplotlib.pyplot.xlabel(r"Section size [\#entries]")
        matplotlib.pyplot.ylim((-0.01, 1.01))
        matplotlib.pyplot.ylabel("Density")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH, f"iot-data-sec-counts-{filt_name}@{data_src}.{ext}"
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":  # pragma: no cover
    main()
