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

import csv
import logging
import os

import matplotlib.pyplot
import numpy

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def array_ordered_by_query_time(times, queries, files=None):
    array = []
    for idx, times_list in enumerate(times):
        if len(times_list) >= queries:
            array.append(sorted((a[0], a[1]) for a in times_list[:queries]))
        else:
            logging.error(
                "%s has too little queries (%d)",
                files[idx][1] if files else f"#{idx}",
                len(times_list),
            )
    return numpy.array(array)


def process_data(
    transport,
    method=pc.COAP_METHOD_DEFAULT,
    delay_time=None,
    delay_queries=None,
    queries=pc.QUERIES_DEFAULT,
    avg_queries_per_sec=pc.AVG_QUERIES_PER_SEC_DEFAULT,
    record=pc.RECORD_TYPE_DEFAULT,
):
    files = pc.get_files(
        "load",
        transport,
        method,
        delay_time,
        delay_queries,
        queries,
        avg_queries_per_sec,
        record,
    )
    res = []
    for match, filename in files[-pc.RUNS :]:
        filename = os.path.join(pc.DATA_PATH, filename)
        with open(filename, encoding="utf-8") as timesfile:
            reader = csv.DictReader(timesfile, delimiter=";")
            base_id = None
            base_time = None
            last_id = None
            times_list = []
            for row in reader:
                base_id, base_time = pc.normalize_times_and_ids(row, base_id, base_time)
                if last_id is not None and last_id < (row["id"] - 1):
                    # A query was skipped
                    times = (numpy.nan, numpy.nan)
                else:
                    if row.get("response_time"):
                        times = (
                            row["query_time"],
                            row["response_time"] - row["query_time"],
                        )
                    else:
                        times = (row["query_time"], numpy.nan)
                times_list.append(times)
            res.append(times_list)
    return array_ordered_by_query_time(res, queries, files=files[-pc.RUNS :])


def label_plot(ax, xmax, ymax, transport, method, time):
    ax.set_xlim((0, xmax))
    ax.set_xticks(numpy.arange(0, xmax + 1, step=4))
    ax.set_ylim((-0.5, ymax))
    ax.set_yticks(numpy.arange(0, ymax + 1, step=1))
    ax.text(
        xmax - 0.5,
        ymax + 0.3,
        pc.TRANSPORTS_READABLE[transport],
        horizontalalignment="right",
        verticalalignment="top",
    )
    # if transport == pc.TRANSPORTS[0]:
    #     ax.text(
    #         xmax + 0.1,
    #         ymax / 2,
    #         "Baseline" if time is None else "Delayed",
    #         clip_on=False,
    #         verticalalignment="center",
    #         rotation=-90,
    #     )
    ax.grid(True)


def _hide_helper_ax(ax):
    ax.spines["top"].set_color("none")
    ax.spines["bottom"].set_color("none")
    ax.spines["left"].set_color("none")
    ax.spines["right"].set_color("none")
    ax._frameon = False  # pylint: disable=protected-access
    ax.tick_params(
        top=False,
        bottom=False,
        left=False,
        right=False,
        labeltop=False,
        labelbottom=False,
        labelleft=False,
        labelright=False,
    )


def main():  # noqa: C901
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    mx = []
    my = []
    for record in pc.RECORD_TYPES:
        for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
            if avg_queries_per_sec > 5:
                continue
            fig = matplotlib.pyplot.figure(figsize=(7.3, 2.5))
            allax = fig.subplots(1, 1)
            rows = fig.subplots(2, 1, sharex=True, sharey=True)
            axs = fig.subplots(2, 5, sharex=True, sharey=True)
            for t, transport in enumerate(reversed(pc.TRANSPORTS)):
                for m, method in enumerate(pc.COAP_METHODS):
                    if transport not in pc.COAP_TRANSPORTS:
                        if m > 0:
                            continue
                        method = None
                    elif method != "fetch":
                        continue
                    for rd, (time, queries) in enumerate(pc.RESPONSE_DELAYS):
                        ax = axs[rd][t]
                        times = process_data(
                            transport,
                            method,
                            time,
                            queries,
                            avg_queries_per_sec=avg_queries_per_sec,
                            record=record,
                        )
                        if len(times) == 0:
                            continue
                        for i in range(times.shape[0]):
                            mx.append(max(times[i, :, 0]))
                            my.append(max(times[i, :, 1]))
                            ax.plot(
                                times[i, :, 0],
                                times[i, :, 1],
                                alpha=(1 / pc.RUNS) * 4,
                                # marker="x",
                                # markersize=3,
                                **pc.TRANSPORTS_STYLE[transport][method],
                            )
                        if times.shape[0] > 0:
                            label_plot(ax, 21, 2.5, transport, method, time)
            _hide_helper_ax(allax)
            allax.set_ylabel("Resolution time [s]", labelpad=16.0)
            allax.set_xlabel("Query sent timestamp [s]", labelpad=16.0)
            for rowax in rows:
                _hide_helper_ax(rowax)
            rows[0].set_title("Baseline (no artificial delay)")
            rows[1].set_title("Delayed (response to every 25th query delayed by 1 s)")
            matplotlib.pyplot.tight_layout()
            for ext in ["pgf", "svg"]:
                matplotlib.pyplot.savefig(
                    os.path.join(
                        pc.DATA_PATH,
                        f"doc-eval-load-{avg_queries_per_sec}-{record}.{ext}",
                    ),
                    bbox_inches="tight",
                )
            matplotlib.pyplot.gcf()
            matplotlib.pyplot.close(fig)
    try:
        print(max(mx))
    except ValueError:
        print(0)
    try:
        print(max(my))
    except ValueError:
        print(0)


if __name__ == "__main__":
    main()
