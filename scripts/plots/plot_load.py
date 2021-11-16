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
        if match["record"] is None and record != pc.RECORD_TYPE_DEFAULT:
            continue
        if (
            transport in pc.COAP_TRANSPORTS
            and match["method"] is None
            and method != pc.COAP_METHOD_DEFAULT
        ):
            continue
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


def label_plot(xmax, ymax, transport, method, time):
    matplotlib.pyplot.xlabel("Experiment duration [s]")
    matplotlib.pyplot.xlim((0, xmax))
    matplotlib.pyplot.xticks(numpy.arange(0, xmax + 1, step=2))
    matplotlib.pyplot.ylabel("Resolution time [s]")
    matplotlib.pyplot.ylim((0, ymax))
    matplotlib.pyplot.yticks(numpy.arange(0, ymax + 1, step=1))
    matplotlib.pyplot.text(
        xmax - 0.1,
        ymax - 0.1,
        pc.TRANSPORTS_READABLE[transport][method],
        horizontalalignment="right",
        verticalalignment="top",
    )
    matplotlib.pyplot.text(
        xmax + 0.1,
        ymax / 2,
        "Baseline" if time is None else "Delayed",
        clip_on=False,
        verticalalignment="center",
        rotation=-90,
    )


def main():  # noqa: C901
    mx = []
    my = []
    for transport in pc.TRANSPORTS:
        for m, method in enumerate(pc.COAP_METHODS):
            if transport not in pc.COAP_TRANSPORTS:
                if m > 0:
                    continue
                method = None
            for record in pc.RECORD_TYPES:
                for time, queries in pc.RESPONSE_DELAYS:
                    for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
                        matplotlib.pyplot.figure(figsize=(4, 9 / 4))
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
                            matplotlib.pyplot.plot(
                                times[i, :, 0],
                                times[i, :, 1],
                                alpha=(1 / pc.RUNS) * 2,
                                **pc.TRANSPORTS_STYLE[transport][method],
                            )
                        if times.shape[0] > 0:
                            label_plot(26, 5, transport, method, time)
                            matplotlib.pyplot.tight_layout()
                            for ext in ["pgf", "svg"]:
                                matplotlib.pyplot.savefig(
                                    os.path.join(
                                        pc.DATA_PATH,
                                        f"doc-eval-load-{transport}%s-{time}-{queries}-"
                                        f"{avg_queries_per_sec}-{record}.{ext}"
                                        % (
                                            f"-{method}"
                                            if transport in pc.COAP_TRANSPORTS
                                            else ""
                                        ),
                                    ),
                                    bbox_inches="tight",
                                )
                        matplotlib.pyplot.clf()
                        matplotlib.pyplot.close()
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
