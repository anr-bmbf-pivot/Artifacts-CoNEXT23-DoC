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
import publicsuffix2

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


def extract_hostname(name):
    name = name[:-1]
    tld = publicsuffix2.get_tld(name, strict=True)
    if tld is None:
        hostname = name
    else:
        if tld.endswith("amazonaws.com"):
            tld = "com"
        elif tld == "azurewebsites.net":
            tld = "net"
        elif tld == "cloudapp.net":
            tld = "net"
        elif tld == "cloudfront.net":
            tld = "net"
        elif tld.endswith("dyndns.org"):
            tld = "org"
        elif tld.endswith("elasticbeanstalk.com"):
            tld = "com"
        elif tld == "fastly.net":
            tld = "net"
        elif tld == "googleapis.com":
            tld = "com"
        etld_comps = tld.split(".")
        name_comps = name.split(".")
        hostname = ".".join(name_comps[: -(len(etld_comps) + 1)])
    return hostname


def _len(hostname, name):
    res = len(hostname)
    return res


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    parser = argparse.ArgumentParser()
    parser.add_argument("iot_data_csv")
    args = parser.parse_args()
    for filt_name, filt in name_len.FILTERS:
        df = pandas.read_csv(args.iot_data_csv)
        df = name_len.filter_data_frame(df, filt)
        name_lens = pandas.Series(
            [
                _len(extract_hostname(name), name)
                for name in df["name"].str.lower().unique()
            ]
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
                    f"iot-data-hostname-lens-{filt_name}.{ext}",
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":
    main()
