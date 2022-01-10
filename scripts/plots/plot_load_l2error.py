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

import matplotlib.patches
import matplotlib.pyplot
import matplotlib.text
import numpy

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


WIDTH = 0.9
NODE_GAP = 0.025
L2_COLOR = {
    "l2_success": "C0",
    "l2_multicast": "C4",
    "l2_error": "C3",
    "l2_received": "C1",
}
L2_READABLE = {
    "l2_success": "TX unicast success",
    "l2_multicast": "TX multicast",
    "l2_error": "TX unicast error",
    "l2_received": "RX",
}
NODE_STYLE = {
    "br": {
        "hatch": "//",
    }
}
NODE_READABLE = {"br": "BR"}


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
        csv_type="stats",
    )
    res = {}
    if transport == "dtls":
        return res
    for match, filename in files[-pc.RUNS :]:
        read_csv(filename, res)
    for node in res:
        for key in res[node]:
            array = numpy.array(res[node][key])
            if key == "l2_success":
                array -= numpy.array(res[node]["l2_multicast"])
            res[node][key] = {
                "mean": array.mean(),
                "std": array.std(),
            }
    return res


def read_csv(filename, res):
    with open(filename, encoding="utf-8") as statsfile:
        reader = csv.DictReader(statsfile, delimiter=";")
        for row in reader:
            node = row["node"]
            if node in res:
                for key in row:
                    if key == "node":
                        continue
                    res[node][key].append(int(row[key]))
            else:
                res[node] = {k: [int(v)] for k, v in row.items() if k != "node"}


def aggregate_stats(time, queries, avg_queries_per_sec, record):
    labels = []
    agg_stats = {}
    for transport in pc.TRANSPORTS:
        method = "fetch"
        stats = process_data(
            transport,
            method,
            time,
            queries,
            avg_queries_per_sec=avg_queries_per_sec,
            record=record,
        )
        if not stats or not all(len(stats[n]) > 0 for n in stats):
            continue
        for node in stats:
            if node in agg_stats:
                agg_stats[node]["l2_multicast"].append(stats[node]["l2_multicast"])
                agg_stats[node]["l2_success"].append(stats[node]["l2_success"])
                agg_stats[node]["l2_error"].append(stats[node]["l2_error"])
                agg_stats[node]["l2_received"].append(stats[node]["l2_received"])
            else:
                agg_stats[node] = {
                    "l2_multicast": [stats[node]["l2_multicast"]],
                    "l2_success": [stats[node]["l2_success"]],
                    "l2_error": [stats[node]["l2_error"]],
                    "l2_received": [stats[node]["l2_received"]],
                }
        labels.append(transport)
    return labels, agg_stats


def main():  # noqa: C901
    for record in pc.RECORD_TYPES:
        for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
            for time, queries in pc.RESPONSE_DELAYS:
                fig = matplotlib.pyplot.figure(figsize=(14 / 2, 9 / 4))
                labels, agg_stats = aggregate_stats(
                    time, queries, avg_queries_per_sec, record
                )
                x = numpy.arange(len(labels))
                if not labels:
                    continue
                width = ((WIDTH / len(agg_stats)) - NODE_GAP) / 2
                node_offset = (width / 2) + (NODE_GAP / 2) - (WIDTH / 2)
                for node in sorted(agg_stats):
                    success = numpy.array(
                        [m["mean"] for m in agg_stats[node]["l2_success"]]
                    )
                    y = success
                    matplotlib.pyplot.bar(
                        x + node_offset,
                        y,
                        yerr=numpy.array(
                            [m["std"] for m in agg_stats[node]["l2_success"]]
                        ),
                        label=f"TX uc success ({node})",
                        width=width,
                        color=L2_COLOR["l2_success"],
                        edgecolor="white",
                        **NODE_STYLE.get(node, {}),
                    )
                    bottom = y
                    y = numpy.array(
                        [m["mean"] for m in agg_stats[node]["l2_multicast"]]
                    )
                    matplotlib.pyplot.bar(
                        x + node_offset,
                        y,
                        yerr=numpy.array(
                            [m["std"] for m in agg_stats[node]["l2_multicast"]]
                        ),
                        bottom=bottom,
                        label=f"TX mc ({node})",
                        width=width,
                        color=L2_COLOR["l2_multicast"],
                        edgecolor="white",
                        **NODE_STYLE.get(node, {}),
                    )
                    bottom += y
                    error = numpy.array(
                        [m["mean"] for m in agg_stats[node]["l2_error"]]
                    )
                    y = error
                    matplotlib.pyplot.bar(
                        x + node_offset,
                        y,
                        yerr=numpy.array(
                            [m["std"] for m in agg_stats[node]["l2_error"]]
                        ),
                        bottom=bottom,
                        label=f"TX uc error ({node})",
                        width=width,
                        color=L2_COLOR["l2_error"],
                        edgecolor="white",
                        **NODE_STYLE.get(node, {}),
                    )
                    bottom += y
                    for i in range(len(labels)):
                        matplotlib.pyplot.text(
                            x[i] + node_offset,
                            bottom[i] + 5,
                            f"{error[i] / (error[i] + success[i]) * 100:.1f}%",
                            horizontalalignment="center",
                        )
                    matplotlib.pyplot.bar(
                        x + node_offset + width,
                        numpy.array(
                            [m["mean"] for m in agg_stats[node]["l2_received"]]
                        ),
                        yerr=numpy.array(
                            [m["std"] for m in agg_stats[node]["l2_received"]]
                        ),
                        label=f"TX received ({node})",
                        width=width,
                        color=L2_COLOR["l2_received"],
                        edgecolor="white",
                        **NODE_STYLE.get(node, {}),
                    )
                    node_offset += (2 * width) + NODE_GAP
                matplotlib.pyplot.xticks(
                    x, [pc.TRANSPORTS_READABLE[label] for label in labels]
                )
                matplotlib.pyplot.ylim((0, 380))
                l2_handles = [
                    matplotlib.patches.Patch(color=L2_COLOR[l2], label=L2_READABLE[l2])
                    for l2 in ["l2_success", "l2_multicast", "l2_error", "l2_received"]
                ]
                l2_handles.append(
                    matplotlib.patches.Patch(
                        color="none", label="1.1% = Unicast error rate"
                    )
                )
                l2_legend = matplotlib.pyplot.legend(
                    handles=l2_handles,
                    loc="upper center",
                    ncol=len(l2_handles) + 1,
                    fontsize="small",
                    bbox_to_anchor=(0.5, 1.25),
                )
                fig.add_artist(l2_legend)
                node_handles = [
                    matplotlib.patches.Patch(
                        label=NODE_READABLE.get(node, node),
                        facecolor="gray",
                        linewidth=1,
                        edgecolor="white",
                        linestyle="-",
                        **NODE_STYLE.get(node, {}),
                    )
                    for node in sorted(agg_stats)
                ]
                node_legend = matplotlib.pyplot.legend(
                    handles=node_handles,
                    loc="upper right",
                    fontsize="small",
                )
                fig.add_artist(node_legend)
                matplotlib.pyplot.tight_layout()
                for ext in ["pgf", "svg"]:
                    fig.savefig(
                        os.path.join(
                            pc.DATA_PATH,
                            f"doc-eval-load-l2error-{time}-"
                            f"{queries}-{avg_queries_per_sec}-{record}.{ext}",
                        ),
                        bbox_inches="tight",
                    )
                matplotlib.pyplot.clf()


if __name__ == "__main__":
    main()
