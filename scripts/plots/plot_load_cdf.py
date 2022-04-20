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
import csv
import math
import os

import matplotlib
import matplotlib.lines
import matplotlib.pyplot
import matplotlib.ticker
import numpy

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def cdf(ttcs):
    nans = numpy.isnan(ttcs)
    nan_num = numpy.count_nonzero(nans)
    pdr = 1.0 - (nan_num / ttcs.shape[0])
    bins = (
        numpy.arange(
            numpy.floor(ttcs[~nans].min() * 100),
            numpy.floor(ttcs[~nans].max() * 100),
        )
        / 100
    )
    hist, x = numpy.histogram(ttcs[~nans], bins=bins, density=1)
    if len(x) < 2:
        return numpy.array([]), numpy.array([])
    dx = x[1] - x[0]
    return x[1:], (numpy.cumsum(hist * pdr) * dx)


def process_data(
    transport,
    method=None,
    delay_time=None,
    delay_queries=None,
    queries=pc.QUERIES_DEFAULT,
    avg_queries_per_sec=pc.AVG_QUERIES_PER_SEC_DEFAULT,
    record=pc.RECORD_TYPE_DEFAULT,
    link_layer=pc.LINK_LAYER_DEFAULT,
    blocksize=None,
):
    files = pc.get_files(
        "proxy",
        transport,
        method,
        delay_time,
        delay_queries,
        queries,
        avg_queries_per_sec,
        record,
        link_layer=link_layer,
        blocksize=blocksize,
        proxied=0,
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
        return cdf(numpy.array(res))
    return numpy.array([]), numpy.array([])


def label_plots(
    ax, axins, link_layer, avg_queries_per_sec, record, xlim=45, blockwise=False
):
    ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(1))
    ax.set_xlabel("Resolution time [s]")
    ax.set_xlim((-0.5, xlim))
    ax.set_xticks(
        numpy.arange(0, xlim + 1, step=2 if xlim <= 10 else 5 if xlim <= 25 else 10)
    )
    if record == pc.RECORD_TYPES[-1]:
        ax.set_ylabel("CDF")
    ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
    ax.set_ylim((0, 1.02))
    ax.set_yticks(numpy.arange(0, 1.01, step=0.5))
    ax.grid(True, which="major")
    ax.grid(True, which="minor", linewidth=0.25)
    if axins:
        if blockwise:
            axins.set_xlim((0, 8.1))
            axins.set_ylim((0.989, 1.0001))
            axins.set_xticks(numpy.arange(0, 8.1, step=2))
            axins.set_yticks(numpy.arange(0.99, 1.0, step=0.01))
        else:
            if link_layer == "ble" or avg_queries_per_sec == 5:
                axins.set_xlim((0, 1.25))
                axins.set_ylim((0.98, 1.001))
                axins.set_xticks(numpy.arange(0, 1.3, step=0.5))
                axins.set_yticks(numpy.arange(0.98, 1.0, step=0.01))
            else:
                axins.set_xlim((0, 4))
                axins.set_ylim((0.98, 1.001))
                axins.set_xticks(numpy.arange(0, 4.5, step=1))
                axins.set_yticks(numpy.arange(0.98, 1.001, step=0.01))
        axins.tick_params(labelsize="small")
        axins.yaxis.set_label_position("right")
        axins.yaxis.tick_right()
        y_minor = matplotlib.ticker.LogLocator(
            base=0.001, subs=numpy.arange(0.98, 1.001, 0.001), numticks=20
        )
        axins.yaxis.set_minor_locator(y_minor)
        axins.grid(True, which="minor", axis="y", linewidth=0.4)
        axins.grid(True)


def main():  # noqa: C901
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
    for time, queries in pc.RESPONSE_DELAYS:
        for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
            if avg_queries_per_sec > 5 or time is not None:
                continue
            plots_contained = 0
            methods_plotted = set()
            transports_plotted = set()
            fig = matplotlib.pyplot.gcf()
            axs = fig.subplots(1, 2, sharey=True)
            for i, record in enumerate(reversed(pc.RECORD_TYPES)):
                ax = axs[i]
                ax.set_title(f"{record} record")
                axins = None
                for transport in reversed(pc.TRANSPORTS):
                    for m, method in enumerate(pc.COAP_METHODS):
                        if transport not in pc.COAP_TRANSPORTS:
                            if m > 0:
                                continue
                            method = None
                        if transport == "oscore" and method != "fetch":
                            continue
                        x, y = process_data(
                            transport,
                            method,
                            time,
                            queries,
                            avg_queries_per_sec=avg_queries_per_sec,
                            record=record,
                            link_layer=args.link_layer,
                        )
                        if len(x) == 0 or len(y) == 0:
                            continue
                        transports_plotted.add(transport)
                        methods_plotted.add(method)
                        ax.plot(
                            x,
                            y,
                            label=pc.TRANSPORTS_READABLE[transport][method],
                            **pc.TRANSPORTS_STYLE[transport][method],
                        )
                        if axins:
                            axins.plot(
                                x,
                                y,
                                label=pc.TRANSPORTS_READABLE[transport][method],
                                **pc.TRANSPORTS_STYLE[transport][method],
                            )
                        plots_contained += 1
                        label_plots(
                            ax, axins, args.link_layer, avg_queries_per_sec, record
                        )
                if axins:
                    ax.indicate_inset_zoom(axins, edgecolor="black")
            if plots_contained:
                transport_readable = pc.TransportsReadable.TransportReadable
                transport_handles = [
                    matplotlib.lines.Line2D(
                        [0],
                        [0],
                        label=transport_readable.TRANSPORTS_READABLE[transport],
                        **pc.TRANSPORTS_STYLE[transport],
                    )
                    for transport in reversed(pc.TRANSPORTS)
                    if transport in transports_plotted
                ]
                if avg_queries_per_sec == 5:
                    transport_legend = fig.legend(
                        handles=transport_handles,
                        loc="lower left",
                        title="DNS Transports",
                        ncol=math.ceil(len(pc.TRANSPORTS) / 3),
                        bbox_to_anchor=(0.05, -0.38),
                    )
                    fig.add_artist(transport_legend)
                    if methods_plotted != {"fetch"}:
                        method_readable = transport_readable.MethodReadable
                        method_handles = [
                            matplotlib.lines.Line2D(
                                [0],
                                [0],
                                label=method_readable.METHODS_READABLE[method],
                                color="gray",
                                **pc.TransportsStyle.TransportStyle.METHODS_STYLE[
                                    method
                                ],
                            )
                            for method in pc.COAP_METHODS
                            if method in methods_plotted
                        ]
                        method_legend = fig.legend(
                            handles=method_handles,
                            loc="lower right",
                            title="CoAP Methods",
                            bbox_to_anchor=(0.95, -0.38),
                        )
                        fig.add_artist(method_legend)
                matplotlib.pyplot.tight_layout(w_pad=0.2)
                for ext in pc.OUTPUT_FORMATS:
                    matplotlib.pyplot.savefig(
                        os.path.join(
                            pc.DATA_PATH,
                            f"doc-eval-load-{args.link_layer}-cdf-{time}-{queries}-"
                            f"{avg_queries_per_sec}.{ext}",
                        ),
                        bbox_inches="tight",
                        pad_inches=0.01,
                    )
            matplotlib.pyplot.close()


if __name__ == "__main__":
    main()
