#! /usr/bin/env python
#
# Copyright (C) 2021-22 Freie Universität Berlin
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

import matplotlib.pyplot
import numpy

try:
    from . import plot_common as pc
    from . import plot_comp_cdf
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_comp_cdf

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

RETRIES = 4
TIMEOUT_MS = 2000
COAP_RANDOM_FACTOR_1000 = 1500


def files_to_tables(files, transport, record, method):
    tables = {}
    for match, filename in files[-pc.RUNS :]:
        filename = os.path.join(pc.DATA_PATH, filename)
        with open(filename, encoding="utf-8") as timesfile:
            reader = csv.DictReader(timesfile, delimiter=";")
            timestamp = int(match["timestamp"])
            if timestamp not in tables:  # pragma: no cover
                tables[timestamp] = {}
            table = tables[timestamp]
            for row in reader:
                qt = float(row["query_time"])
                if qt in table:
                    table[qt].update(  # pragma: no cover
                        {k: v for k, v in row.items() if v}
                    )
                else:
                    table[qt] = row
    for timestamp in tables:
        tables[timestamp] = sorted(
            (v for v in tables[timestamp].values()),
            key=lambda v: float(v["query_time"]),
        )
    return tables


def process_data(
    transport,
    method=pc.COAP_METHOD_DEFAULT,
    delay_time=None,
    delay_queries=None,
    queries=pc.QUERIES_DEFAULT,
    avg_queries_per_sec=pc.AVG_QUERIES_PER_SEC_DEFAULT,
    record=pc.RECORD_TYPE_DEFAULT,
    exp_type="baseline",
    proxied=None,
    max_age_config=None,
    client_coap_cache=None,
    dns_cache=None,
):
    files = pc.get_files(
        exp_type,
        transport,
        method,
        delay_time,
        delay_queries,
        queries,
        avg_queries_per_sec,
        record,
        proxied=proxied,
        max_age_config=max_age_config,
        client_coap_cache=client_coap_cache,
        dns_cache=dns_cache,
    )
    tables = files_to_tables(files, transport, method, record)
    transmissions = []
    cache_hits = []
    for timestamp in tables:
        base_id = None
        base_time = None
        last_id = None
        for row in tables[timestamp]:
            base_id, base_time = pc.normalize_times_and_ids(row, base_id, base_time)
            if (
                max_age_config is None
                and last_id is not None
                and last_id < (row["id"] - 1)
            ):
                # A query was skipped
                transmissions.append((numpy.nan, numpy.nan))  # pragma: no cover
            else:
                if row.get("transmissions"):
                    for transmission in row["transmissions"]:
                        transmissions.append(
                            (
                                row["query_time"],
                                transmission - row["query_time"],
                            )
                        )
                else:
                    transmissions.append(  # pragma: no cover
                        (row["query_time"], numpy.nan)
                    )
            if exp_type not in ["comp", "max_age"]:
                continue
            if row.get("cache_hits"):
                for cache_hit in row["cache_hits"]:
                    cache_hits.append(
                        (row["query_time"], cache_hit - row["query_time"])
                    )
            if row.get("client_cache_hits"):
                for cache_hit in row["client_cache_hits"]:
                    cache_hits.append(
                        (row["query_time"], cache_hit - row["query_time"])
                    )
            cache_hits.sort()
    if exp_type in ["comp", "max_age"]:
        return numpy.array(transmissions), numpy.array(cache_hits)
    else:
        return numpy.array(transmissions)


def mark_exp_retrans(ax):
    prev_start = None
    prev_end = None
    bins = [0, 250]
    for i in range(RETRIES + 1):
        timeout = TIMEOUT_MS << i
        end_offset = ((TIMEOUT_MS * COAP_RANDOM_FACTOR_1000) // 1000) << i
        if prev_start is None and prev_end is None:
            start = timeout
            end = end_offset
        else:
            start = prev_start + timeout
            end = prev_end + end_offset
        mean = (start + end) / 2
        prev_start = start
        prev_end = end
        x = numpy.arange(0, 30)
        y1 = numpy.full_like(x, start / 1000)
        y2 = numpy.full_like(x, end / 1000)
        ax.fill_between(x, y1, y2, color="lightgray", alpha=0.5, linewidth=0)
        ax.axhline(mean / 1000, linewidth=0.5, color="gray", alpha=0.5)
        bins.extend([start, end + 1])
    return numpy.array(bins) / 1000


def label_plot(
    ax,
    xmax,
    ymax,
    transport,
    method,
    time,
    exp_type="baseline",
    proxied=False,
    labelx=True,
    xlabeltext="Query sent timestamp [s]",
    labely=True,
    ylabeltext="Since query sent [s]",
):
    if labelx:
        ax.set_xlabel(xlabeltext)
    ax.set_xlim((0, xmax))
    ax.set_xticks(
        numpy.arange(
            0,
            xmax + 1,
            step=2 if exp_type == "baseline" else 5,
        )
    )
    if (exp_type not in ["comp", "max_age"] or not proxied) and labely:
        ax.set_ylabel(ylabeltext)
    ax.set_ylim((-1, ymax))
    ax.set_yticks(numpy.arange(0, ymax + 1, step=5 if exp_type == "baseline" else 10))
    if exp_type == "baseline":
        ax.text(
            xmax - 0.1,
            ymax - 0.1,
            pc.TRANSPORTS_READABLE[transport][method],
            horizontalalignment="right",
            verticalalignment="top",
        )


def main():  # noqa: C901
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    mx0 = []
    mx1 = []
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
                        fig = matplotlib.pyplot.figure()
                        axs = fig.subplots(
                            1,
                            2,
                            sharey=True,
                            gridspec_kw={"wspace": 0.1, "width_ratios": [4, 1]},
                        )
                        for ax in axs:
                            mark_exp_retrans(ax)
                        transmissions = process_data(
                            transport,
                            method,
                            time,
                            queries,
                            queries=100,  # DNS queries per run
                            avg_queries_per_sec=avg_queries_per_sec,
                            record=record,
                        )
                        if len(transmissions) == 0:
                            matplotlib.pyplot.close(fig)
                            continue
                        mx0.append(transmissions[:, 0].max())
                        my.append(transmissions[:, 1].max())
                        axs[0].scatter(
                            transmissions[:, 0],
                            transmissions[:, 1],
                            s=2,
                            marker="o",
                            label="Transport transmissions",
                            alpha=0.8,
                            **pc.TRANSPORTS_STYLE[transport],
                        )
                        if len(transmissions[:, 1]) == 0:
                            matplotlib.pyplot.close(fig)  # pragma: no cover
                            continue  # pragma: no cover
                        x, y = plot_comp_cdf.cdf(transmissions[:, 1])
                        axs[1].plot(
                            y,
                            x,
                            label="Transport transmissions",
                            **pc.TRANSPORTS_STYLE[transport],
                        )
                        axs[1].set_xlabel("CDF")
                        axs[1].set_xticks(numpy.arange(0, 1.5, step=0.5))
                        mx1.append(axs[1].get_xlim()[1])
                        axs[1].set_xlim((0, 1.05))
                        axs[1].grid(True, axis="x")
                        label_plot(
                            axs[0],
                            11 if avg_queries_per_sec == 10 else 21,
                            10,
                            transport,
                            method,
                            time,
                        )
                        fig.tight_layout()
                        for ext in pc.OUTPUT_FORMATS:
                            fig.savefig(
                                os.path.join(
                                    pc.DATA_PATH,
                                    f"doc-eval-baseline-trans-{transport}%s-{time}-"
                                    f"{queries}-{avg_queries_per_sec}-{record}.{ext}"
                                    % (
                                        f"-{method}"
                                        if transport in pc.COAP_TRANSPORTS
                                        else ""
                                    ),
                                ),
                                bbox_inches="tight",
                            )
                        matplotlib.pyplot.clf()
                        matplotlib.pyplot.close(fig)
    try:
        print(max(mx0))
    except ValueError:  # pragma: no cover
        print(0)
    try:
        print(max(mx1))
    except ValueError:  # pragma: no cover
        print(0)
    try:
        print(max(my))
    except ValueError:  # pragma: no cover
        print(0)


if __name__ == "__main__":
    main()  # pragma: no cover
