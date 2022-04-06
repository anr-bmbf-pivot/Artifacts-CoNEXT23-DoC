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
import csv
import os

import matplotlib.lines
import matplotlib.pyplot
import numpy

try:
    from . import plot_common as pc
    from . import plot_load_cdf
except ImportError:
    import plot_common as pc
    import plot_load_cdf

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def process_data(
    method,
    max_age_config,
    proxied=1,
    link_layer=pc.LINK_LAYER_DEFAULT,
    queries=pc.QUERIES_DEFAULT,
    record=pc.RECORD_TYPE_DEFAULT,
):
    files = pc.get_files(
        "max_age",
        transport="coap",
        method=method,
        delay_time=None,
        delay_queries=None,
        queries=queries,
        avg_queries_per_sec=5.0,
        record=record,
        link_layer=link_layer,
        proxied=proxied,
        max_age_config=max_age_config,
    )
    res = []
    for match, filename in files[-pc.RUNS :]:
        filename = os.path.join(pc.DATA_PATH, filename)
        with open(filename, encoding="utf-8") as timesfile:
            reader = csv.DictReader(timesfile, delimiter=";")
            base_id = None
            base_time = None
            for row in reader:
                base_id, base_time = pc.normalize_times_and_ids(row, base_id, base_time)
                if row.get("response_time"):
                    times = (row["response_time"] - row["query_time"],)
                else:
                    times = (numpy.nan,)
                res.append(times)
    if res:
        return plot_load_cdf.cdf(numpy.array(res))
    return numpy.array([]), numpy.array([])


def label_plots(ax, labelx=True, labely=True):
    ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(2))
    if labelx:
        ax.set_xlabel("Resolution time [s]")
    ax.set_xlim((-0.2, 45))
    ax.set_xticks(numpy.arange(0, 46, step=10))
    ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
    if labely:
        ax.set_ylabel("CDF")
    ax.set_ylim((0, 1.02))
    ax.set_yticks(numpy.arange(0, 1.01, step=0.5))
    ax.grid(True, which="major")
    ax.grid(True, which="minor", linewidth=0.25)


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    matplotlib.rcParams["legend.fontsize"] = "x-small"
    matplotlib.rcParams["legend.handletextpad"] = 0.2
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0] * 1.15,
        matplotlib.rcParams["figure.figsize"][1] * 0.51,
    )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "link_layer",
        nargs="?",
        default=pc.LINK_LAYER_DEFAULT,
        choices=pc.LINK_LAYERS,
        help=f"Link layer to plot (default={pc.LINK_LAYER_DEFAULT})",
    )
    args = parser.parse_args()
    fig = matplotlib.pyplot.figure()
    axs = fig.subplots(
        1,
        3,
        sharex=True,
        sharey=True,
        gridspec_kw={
            "wspace": 0.1,
        },
    )
    for max_age_config in pc.MAX_AGE_CONFIGS:
        for proxied in pc.PROXIED:
            if not proxied and max_age_config not in [None, "min"]:
                continue
            for record in ["AAAA"]:
                plots_contained = 0
                for method in pc.COAP_METHODS:
                    idx = int(proxied) + (pc.MAX_AGE_CONFIGS.index(max_age_config))
                    ax = axs[idx]
                    x, y = process_data(
                        method,
                        max_age_config,
                        proxied=proxied,
                        link_layer=args.link_layer,
                        record=record,
                    )
                    if len(x) == 0 or len(y) == 0:
                        continue
                    ax.plot(
                        x,
                        y,
                        label=pc.METHODS_READABLE[method],
                        **pc.TRANSPORTS_STYLE["coap"][method],
                    )
                    plots_contained += 1
                    label_plots(ax, labelx=idx == len(axs) // 2, labely=not proxied)
                    ax.set_title(
                        "DoH-like\n(w/ Caching)"
                        if proxied and max_age_config == "min"
                        else "EOL TTLs\n(w/ Caching)"
                        if proxied
                        else "Opaque\nforwarder",
                    )
                    if proxied and max_age_config == "subtract":
                        matplotlib.pyplot.legend(loc="lower right")
    if plots_contained:
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH,
                    f"doc-eval-max_age-"
                    f"{args.link_layer}-cdf-None-None-5.0-{record}.{ext}",
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.close()


if __name__ == "__main__":
    main()
