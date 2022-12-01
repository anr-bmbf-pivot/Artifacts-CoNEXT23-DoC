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
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_iot_data_name_lens as name_len

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def extract_hostname(name):
    """
    >>> extract_hostname("foobar")
    'foobar'
    >>> extract_hostname("example.org")
    ''
    >>> extract_hostname("test.example.org")
    'test'
    """
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


def _len(hostname):
    """
    >>> _len("example.org")
    11
    """
    res = len(hostname)
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    parser.add_argument("iot_data_csvs", nargs="+")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    args.iot_data_csvs = sorted(set(args.iot_data_csvs))
    data_src = []
    for iot_data_csv in args.iot_data_csvs:
        for doi in name_len.DOI_TO_NAME.keys():
            if doi in iot_data_csv.lower():
                data_src.append(name_len.DOI_TO_NAME[doi])
    assert data_src, "Data source can not inferred from CSV name"
    if "ixp" in data_src:
        raise ValueError("Script does not support IXP dataset")
    data_src = "+".join(sorted(data_src))
    for filt_name, filt in name_len.FILTERS:
        if "iotfinder" in data_src and "qrys_only" in filt_name:
            continue
        name_lens = None
        for iot_data_csv in args.iot_data_csvs:
            df = pandas.read_csv(iot_data_csv)
            df = name_len.filter_data_frame(df, filt)
            series = pandas.Series(
                [
                    _len(extract_hostname(name[:-1]))
                    for name in df["name"].str.lower().unique()
                ]
            )
            if name_lens is None:
                name_lens = series
            else:
                name_lens = pandas.concat([name_lens, series], ignore_index=False)
            del df
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
                    f"iot-data-hostname-lens-{filt_name}@{data_src}.{ext}",
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":  # pragma: no cover
    main()
