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
    proxied,
    link_layer=pc.LINK_LAYER_DEFAULT,
    queries=pc.QUERIES_DEFAULT,
    record=pc.RECORD_TYPE_DEFAULT,
):
    files = pc.get_files(
        "proxy",
        transport="coap",
        method=method,
        delay_time=None,
        delay_queries=None,
        queries=queries,
        avg_queries_per_sec=5.0,
        record=record,
        link_layer=link_layer,
        proxied=proxied,
    )
    res = []
    for match, filename in files[-pc.RUNS :]:
        if match["link_layer"] is None and link_layer != pc.LINK_LAYER_DEFAULT:
            continue
        if match["record"] is None and record != pc.RECORD_TYPE_DEFAULT:
            continue
        filename = os.path.join(pc.DATA_PATH, filename)
        with open(filename, encoding="utf-8") as timesfile:
            reader = csv.DictReader(timesfile, delimiter=";")
            base_id = None
            base_time = None
            for row in reader:
                base_id, base_time = pc.normalize_times_and_ids(row, base_id, base_time)
                if row.get("response_time"):
                    times = (row["response_time"] - row["query_time"],)
                    res.append(times)
    if res:
        return plot_load_cdf.cdf(numpy.array(res))
    return numpy.array([]), numpy.array([])


def label_plots(axins, link_layer):
    matplotlib.pyplot.xlabel("Resolution time [s]")
    matplotlib.pyplot.xlim((0, 45))
    matplotlib.pyplot.xticks(numpy.arange(0, 46, step=5))
    matplotlib.pyplot.ylabel("CDF")
    matplotlib.pyplot.ylim((0, 1))
    matplotlib.pyplot.grid(True, linestyle=":")
    # if link_layer == "ble" or delay_time == 5:
    #     axins.set_xlim((0, 2))
    #     axins.set_ylim((0.95, 1))
    #     axins.set_xticks(numpy.arange(0, 2.5, step=0.5))
    #     axins.set_yticks(numpy.arange(0.95, 1.0, step=0.01))
    # else:
    #     axins.set_xlim((0, 9.5))
    #     axins.set_ylim((0.83, 1))
    #     axins.set_xticks(numpy.arange(0, 9.5, step=2))
    #     axins.set_yticks(numpy.arange(0.85, 1.04, step=0.05))
    # axins.yaxis.set_label_position("right")
    # axins.yaxis.tick_right()
    # axins.grid(True, linestyle=":")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "link_layer",
        nargs="?",
        default=pc.LINK_LAYER_DEFAULT,
        choices=pc.LINK_LAYERS,
        help=f"Link layer to plot (default={pc.LINK_LAYER_DEFAULT})",
    )
    args = parser.parse_args()
    for record in ["AAAA"]:
        for proxied in pc.PROXIED:
            plots_contained = 0
            matplotlib.pyplot.figure(figsize=(4, 9 / 4))
            axins = None
            methods_plotted = set()
            for m, method in enumerate(pc.COAP_METHODS):
                x, y = process_data(
                    method,
                    proxied,
                    link_layer=args.link_layer,
                    record=record,
                )
                if len(x) == 0 or len(y) == 0:
                    continue
                methods_plotted.add(method)
                matplotlib.pyplot.plot(
                    x,
                    y,
                    label=pc.TRANSPORTS_READABLE["coap"][method],
                    **pc.TRANSPORTS_STYLE["coap"][method],
                )
                plots_contained += 1
                print(x.max())
                label_plots(axins, args.link_layer)
            matplotlib.pyplot.legend(loc="lower right", title="CoAP Method")
            if plots_contained:
                matplotlib.pyplot.tight_layout()
                for ext in ["pgf", "svg"]:
                    matplotlib.pyplot.savefig(
                        os.path.join(
                            pc.DATA_PATH,
                            f"doc-eval-proxy-{args.link_layer}-cdf-proxied{proxied}-"
                            f"None-None-5.0-{record}.{ext}",
                        ),
                        bbox_inches="tight",
                    )
                matplotlib.pyplot.close()


if __name__ == "__main__":
    main()
