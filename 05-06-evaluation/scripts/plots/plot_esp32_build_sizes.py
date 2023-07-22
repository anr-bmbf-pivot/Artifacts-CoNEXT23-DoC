#! /usr/bin/env python
#
# Copyright (C) 2023 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import argparse
import logging
import pathlib

import matplotlib.pyplot
import numpy
import pandas

try:
    from . import plot_common as pc
    from . import collect_esp32_build_sizes
except ImportError:  # pragma: no cover
    import plot_common as pc
    import collect_esp32_build_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2023 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

MODULES = [
    "dns_transport",
    "crypto",
    "app",
]
MODULE_MAPPING = {
    "crypto": [
        "/hacl/",
        "/libcose/",
        "^liboscore/",
        "^quant/lib/deps/picotls/",
        "/build/pkg/tinycrypt/",
        "/build/pkg/tinydtls/",
    ],
    "dns_transport": [
        "/dsm/",
        "/gcoap/gcoap.c",
        "/nanocoap/",
        "^quant/lib/src/",
        "/uri_parser/",
    ],
    "app": [
        "^quant/test/",
        "^quant/riot/",
        "^apps/requester/",
    ],
}
MODULE_READABLE = {
    "app": "Application",
    "dns_transport": r"DNS Transport (w/o UDP \& Crypto)",
    "crypto": "Crypto (DTLS / TLS / OSCORE)",
}
MODULE_STYLE = {
    "app": {"color": "C4"},
    "dns_transport": {"color": "C3"},
    "crypto": {"color": "C2"},
}
MEMS = ["ROM", "RAM"]
APPS = [
    collect_esp32_build_sizes.REQUESTER_PATH,
    collect_esp32_build_sizes.QUANT_APP_PATH,
]


def plot(sums):
    transports = numpy.array(
        [str(pc.TRANSPORTS_READABLE[t]) for t in reversed(pc.TRANSPORTS)] + ["QUIC"]
    )
    for i, mem in enumerate(MEMS):
        ax = matplotlib.pyplot.gca()
        bottom = None
        for mod in MODULES:
            sizes = (
                numpy.array([sums[i][mem][mod] for i, _ in enumerate(transports)])
                / 1024
            )
            ax.bar(
                numpy.arange(len(transports)),
                sizes,
                bottom=0 if bottom is None else bottom,
                label=MODULE_READABLE[mod],
                **MODULE_STYLE[mod],
            )
            if bottom is None:
                bottom = sizes
            else:
                bottom += sizes
        ax.set_xticks(numpy.arange(len(transports)))
        ax.set_xticklabels(
            labels=transports,
            horizontalalignment="right",
            fontsize="x-small",
            rotation=20,
        )
        ax.set_ylim((0, 80))
        ax.set_yticks(numpy.arange(0, 81, step=20))
        ax.grid(True, axis="y")
        if mem == "ROM":
            ax.legend(loc="upper left")
        ax.set_ylabel("Build size [kBytes]")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                pathlib.Path(pc.DATA_PATH)
                / f"doc-eval-esp32-build_sizes-{mem.lower()}.{ext}",
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.close()


def sum_objs(df, transport):
    if transport is None:
        transport = "quic"
    res = {mem: {mod: 0 for mod in MODULES} for mem in MEMS}
    for module in MODULES:
        pat = "|".join(MODULE_MAPPING[module])
        s = df["filename"].str.extract(f"({pat})", expand=False)
        res["ROM"][module] += df.groupby(s)["text"].sum().sum()
        res["ROM"][module] += df.groupby(s)["data"].sum().sum()
        res["RAM"][module] += df.groupby(s)["bss"].sum().sum()
        res["RAM"][module] += df.groupby(s)["data"].sum().sum()
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    args = parser.parse_args()
    matplotlib.style.use(pathlib.Path(pc.SCRIPT_PATH) / args.style_file)
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0] / 1.2,
        matplotlib.rcParams["figure.figsize"][1] * 0.97,
    )
    matplotlib.rcParams["hatch.color"] = "white"
    matplotlib.rcParams["hatch.linewidth"] = 2
    matplotlib.rcParams["legend.handletextpad"] = 0.2
    matplotlib.rcParams["legend.fontsize"] = "xx-small"
    matplotlib.rcParams["patch.linewidth"] = 0.5
    sums = []
    for app in APPS:
        for transport in reversed(pc.TRANSPORTS):
            if app == collect_esp32_build_sizes.QUANT_APP_PATH:
                transport = None
            csv_filename = collect_esp32_build_sizes.filename(app, transport)
            try:
                df = pandas.read_csv(csv_filename)
            except FileNotFoundError:  # pragma: no cover
                logging.exception(
                    "Please call %s first", collect_esp32_build_sizes.__file__
                )
                raise
            sums.append(sum_objs(df, transport))
            if app == collect_esp32_build_sizes.QUANT_APP_PATH:
                break
    plot(sums)


if __name__ == "__main__":
    main()  # pragma: no cover
