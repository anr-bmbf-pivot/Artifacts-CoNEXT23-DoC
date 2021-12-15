#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2021 Freie Universität Berlin
#
# Distributed under terms of the MIT license.

import glob
import os
import re

import matplotlib.pyplot
import numpy

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc


def count_logs(
    logs,
    link_layer,
    transport,
    record_type,
    method,
    blocksize,
    avg_queries_per_sec,
    response_delay,
):
    logpattern = re.compile(
        pc.FILENAME_PATTERN_FMT.format(
            exp_type="load",
            link_layer=f"(?P<link_layer>{link_layer})",
            transport=transport,
            method=f"(?P<method>{method})",
            blocksize=f"(?P<blocksize>{blocksize})",
            delay_time=response_delay[0],
            delay_queries=response_delay[1],
            queries=pc.QUERIES_DEFAULT,
            avg_queries_per_sec=avg_queries_per_sec,
            record=f"(?P<record_type>{record_type})",
        )
    )
    res = []
    for log in logs:
        match = logpattern.search(log)
        if match is None:
            continue
        if match["link_layer"] is None and link_layer != pc.LINK_LAYER_DEFAULT:
            continue
        if (
            match["method"] is None
            and method != pc.COAP_METHOD_DEFAULT
            and transport in pc.COAP_TRANSPORTS
        ):
            continue
        if (
            match["blocksize"] is None
            and blocksize != pc.COAP_BLOCKTYPE_DEFAULT
            and transport in pc.COAP_TRANSPORTS
        ):
            continue
        if match["record_type"] is None and record_type != pc.RECORD_TYPE_DEFAULT:
            continue
        res.append(log)
    return min(len(res), pc.RUNS)


def main():  # noqa: C901
    logs = glob.glob(os.path.join(pc.DATA_PATH, "doc-eval-load-*[0-9].log"))
    ylabels = []
    xlabels = []
    lognums = []
    transport_borders = []
    method_borders = []
    blocksize_borders = []
    last_transport = None
    last_method = None
    last_blocksize = 0
    for transport in pc.TRANSPORTS:
        for m, method in enumerate(pc.COAP_METHODS):
            if transport not in pc.COAP_TRANSPORTS:
                if m > 0:
                    continue
                method = None
            for b, blocksize in enumerate(pc.COAP_BLOCKSIZE):
                if transport not in pc.COAP_TRANSPORTS:
                    if b > 0:
                        continue
                    blocksize = None
                for record_type in pc.RECORD_TYPES:
                    if transport not in pc.COAP_TRANSPORTS:
                        ylabel = f"{pc.TRANSPORTS_READABLE[transport]} [{record_type}]"
                    else:
                        if blocksize is None:
                            ylabel = (
                                f"{pc.TRANSPORTS_READABLE[transport][method]} "
                                f"[{record_type}]"
                            )
                        else:
                            ylabel = (
                                f"{pc.TRANSPORTS_READABLE[transport][method]} "
                                f"[B: {blocksize}] [{record_type}]"
                            )
                    ylabels.append(ylabel)
                    lognums_col = []
                    if last_transport is None:
                        last_transport = transport
                    elif transport != last_transport:
                        transport_borders.append(len(lognums) - 0.5)
                        last_transport = transport
                        last_method = None
                        last_blocksize = 0
                    if last_method is None:
                        last_method = method
                    elif method != last_method:
                        method_borders.append(len(lognums) - 0.5)
                        last_method = method
                        last_blocksize = 0
                    if last_blocksize == 0:
                        last_blocksize = blocksize
                    elif blocksize != last_blocksize:
                        blocksize_borders.append(len(lognums) - 0.5)
                        last_blocksize = blocksize
                    lognums.append(lognums_col)
                    for link_layer in pc.LINK_LAYERS:
                        for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
                            for delay_time, delay_count in pc.RESPONSE_DELAYS:
                                if link_layer == "ble" and avg_queries_per_sec < 10:
                                    continue
                                if (
                                    avg_queries_per_sec > 5
                                    and (
                                        delay_time,
                                        delay_count,
                                    )
                                    != (None, None)
                                ):
                                    continue
                                if avg_queries_per_sec > 5 and avg_queries_per_sec < 10:
                                    continue
                                if (
                                    link_layer,
                                    avg_queries_per_sec,
                                    delay_time,
                                    delay_count,
                                ) not in xlabels:
                                    xlabels.append(
                                        (
                                            link_layer,
                                            avg_queries_per_sec,
                                            delay_time,
                                            delay_count,
                                        )
                                    )
                                lognums_col.append(
                                    count_logs(
                                        logs,
                                        link_layer,
                                        transport,
                                        record_type,
                                        method,
                                        blocksize,
                                        avg_queries_per_sec,
                                        (delay_time, delay_count),
                                    )
                                )
        last_transport = transport
    lognums = numpy.array(lognums).transpose()
    fig = matplotlib.pyplot.figure(figsize=(12, 3))
    im = matplotlib.pyplot.imshow(lognums)
    matplotlib.pyplot.vlines(
        numpy.array(transport_borders),
        im.get_extent()[2],
        im.get_extent()[3],
        linewidth=3,
        color="red",
    )
    matplotlib.pyplot.vlines(
        numpy.array(method_borders),
        im.get_extent()[2],
        im.get_extent()[3],
        linewidth=2,
        color="orange",
    )
    matplotlib.pyplot.vlines(
        numpy.array(blocksize_borders),
        im.get_extent()[2],
        im.get_extent()[3],
        linewidth=1,
        color="white",
    )
    ax = matplotlib.pyplot.gca()
    cbar = fig.colorbar(im, ax=ax, location="top", aspect=58)
    cbar.ax.set_xlabel("Missing runs", va="bottom", ha="center")
    cbar.ax.set_xticks(numpy.arange(pc.RUNS + 1), reversed(numpy.arange(pc.RUNS + 1)))
    # cbar.ax.set_xticks(cbar.ax.get_xticks(), reversed(cbar.ax.get_xticks()))
    matplotlib.pyplot.yticks(numpy.arange(len(xlabels)), labels=xlabels)
    matplotlib.pyplot.xticks(numpy.arange(len(ylabels)), labels=ylabels)
    ax.set_xticks(numpy.arange(lognums.shape[1] + 1) - 0.5, minor=True)
    ax.set_yticks(numpy.arange(lognums.shape[0] + 1) - 0.5, minor=True)
    matplotlib.pyplot.setp(
        ax.get_xticklabels(),
        rotation=90,
        ha="right",
        va="center",
        rotation_mode="anchor",
    )
    kw = dict(
        horizontalalignment="center",
        verticalalignment="center",
        fontsize=6,
    )
    textcolors = ("white", "black")
    threshold = im.norm(lognums.max()) / 2.0
    for i in range(lognums.shape[0]):
        for j in range(lognums.shape[1]):
            kw.update(color=textcolors[int(im.norm(lognums[i, j]) > threshold)])
            im.axes.text(j, i, f"{pc.RUNS - lognums[i, j]:d}", **kw)
    matplotlib.pyplot.tight_layout()
    for ext in ["pgf", "svg"]:
        matplotlib.pyplot.savefig(
            os.path.join(pc.DATA_PATH, f"doc-eval-load-done.{ext}"), bbox_inches="tight"
        )
    matplotlib.pyplot.show()


if __name__ == "__main__":
    main()
