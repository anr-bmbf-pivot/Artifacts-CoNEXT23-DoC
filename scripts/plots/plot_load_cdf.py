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


def cdf(ttcs):
    bins = (
        numpy.arange(
            numpy.floor(ttcs.min() * 100),
            numpy.floor(ttcs.max() * 100),
        )
        / 100
    )
    hist, x = numpy.histogram(ttcs, bins=bins, density=1)
    if len(x) < 2:
        return numpy.array([]), numpy.array([])
    dx = x[1] - x[0]
    return x[1:], numpy.cumsum(hist) * dx


def process_data(
    transport,
    delay_time=None,
    delay_queries=None,
    queries=pc.QUERIES_DEFAULT,
    avg_queries_per_sec=pc.AVG_QUERIES_PER_SEC_DEFAULT,
    record=pc.RECORD_TYPE_DEFAULT,
):
    files = pc.get_files(
        "load",
        transport,
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
        return cdf(numpy.array(res))
    return numpy.array([]), numpy.array([])


def main():
    for record in pc.RECORD_TYPES:
        for time, queries in pc.RESPONSE_DELAYS:
            for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
                plots_contained = 0
                matplotlib.pyplot.figure(figsize=(4, 9 / 4))
                for transport in reversed(pc.TRANSPORTS):
                    x, y = process_data(
                        transport,
                        time,
                        queries,
                        avg_queries_per_sec=avg_queries_per_sec,
                        record=record,
                    )
                    if len(x) == 0 or len(y) == 0:
                        continue
                    matplotlib.pyplot.plot(
                        x,
                        y,
                        label=pc.TRANSPORTS_READABLE[transport],
                        **pc.TRANSPORTS_STYLE[transport],
                    )
                    plots_contained += 1
                    matplotlib.pyplot.xlabel("Resolution time [s]")
                    matplotlib.pyplot.xlim((0, 20))
                    matplotlib.pyplot.xticks(numpy.arange(0, 21, step=2))
                    matplotlib.pyplot.ylabel("CDF")
                    matplotlib.pyplot.ylim((0, 1))
                    matplotlib.pyplot.grid(True, linestyle=":")
                if plots_contained:
                    matplotlib.pyplot.legend(loc="lower right")
                    matplotlib.pyplot.tight_layout()
                    for ext in ["pgf", "svg"]:
                        matplotlib.pyplot.savefig(
                            os.path.join(
                                pc.DATA_PATH,
                                f"doc-eval-load-cdf-{time}-{queries}-"
                                f"{avg_queries_per_sec}-{record}.{ext}",
                            ),
                            bbox_inches="tight",
                        )
                matplotlib.pyplot.close()


if __name__ == "__main__":
    main()
