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


def label_plots(ax, axins=None):
    ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(1))
    ax.set_xlabel("Resolution time [s]")
    ax.set_xlim((-0.2, 45))
    ax.set_xticks(numpy.arange(0, 46, step=5))
    ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
    ax.set_ylabel("CDF")
    ax.set_ylim((0, 1.02))
    ax.set_yticks(numpy.arange(0, 1.01, step=0.5))
    ax.grid(True, which="major")
    ax.grid(True, which="minor", linewidth=0.25, linestyle="dashed")
    if axins:
        axins.set_xlim((0, 3.5))
        axins.set_ylim((0.65, 0.95))
        axins.set_xticks(numpy.arange(0, 3.5, step=1))
        axins.set_yticks(numpy.arange(0.70, 0.96, step=0.1))
        axins.tick_params(labelsize="small")
        axins.yaxis.set_label_position("right")
        axins.yaxis.tick_right()
        axins.grid(True)


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
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
            ax = matplotlib.pyplot.gca()
            axins = None  # ax.inset_axes([0.09, 0.17, 0.51, 0.67])
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
                transport_readable = pc.TransportsReadable.TransportReadable
                method_readable = transport_readable.MethodReadable
                ax.plot(
                    x,
                    y,
                    label=method_readable.METHODS_READABLE[method],
                    **pc.TRANSPORTS_STYLE["coap"][method],
                )
                if axins:
                    axins.plot(
                        x,
                        y,
                        label=method_readable.METHODS_READABLE[method],
                        **pc.TRANSPORTS_STYLE["coap"][method],
                    )
                plots_contained += 1
                label_plots(ax, axins)
            if axins:
                ax.indicate_inset_zoom(axins, edgecolor="black")
            if proxied:
                matplotlib.pyplot.legend(loc="lower right")
            if plots_contained:
                matplotlib.pyplot.tight_layout()
                for ext in pc.OUTPUT_FORMATS:
                    matplotlib.pyplot.savefig(
                        os.path.join(
                            pc.DATA_PATH,
                            f"doc-eval-proxy-{args.link_layer}-cdf-proxied{proxied}-"
                            f"None-None-5.0-{record}.{ext}",
                        ),
                        bbox_inches="tight",
                        pad_inches=0.01,
                    )
                matplotlib.pyplot.close()


if __name__ == "__main__":
    main()
