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
    exp_type,
    link_layer,
    transport,
    record_type,
    method,
    blocksize,
    proxied,
    avg_queries_per_sec,
    response_delay,
    max_age_config=None,
):
    logpattern_str = pc.FILENAME_PATTERN_FMT.format(
        exp_type=exp_type,
        link_layer=f"(?P<link_layer>{link_layer})",
        transport=transport,
        method=f"(?P<method>{method})",
        blocksize=f"(?P<blocksize>{blocksize})",
        proxied=f"(?P<proxied>{proxied})",
        delay_time=response_delay[0],
        delay_queries=response_delay[1],
        queries=pc.QUERIES_DEFAULT,
        avg_queries_per_sec=avg_queries_per_sec,
        record=f"(?P<record_type>{record_type})",
        max_age_config=max_age_config,
    )
    logpattern = re.compile(logpattern_str)
    res = []
    if (
        exp_type in ["proxy", "max_age"]
        and (proxied or exp_type == "max_age")
        and (transport != "coap" or record_type == "A" or blocksize is not None)
    ):
        return numpy.nan
    if transport == "oscore" and (
        blocksize is not None or method not in ["fetch", "post"]
    ):
        return numpy.nan
    if link_layer == "ble" and blocksize is not None:
        return numpy.nan
    if (
        transport in pc.COAP_TRANSPORTS
        and blocksize is not None
        and (
            response_delay != (None, None)
            or (blocksize < 32 and avg_queries_per_sec > 5)
            or method == "get"
        )
    ):
        return numpy.nan
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
            and blocksize != pc.COAP_BLOCKSIZE_DEFAULT
            and transport in pc.COAP_TRANSPORTS
        ):
            continue
        if match["record_type"] is None and record_type != pc.RECORD_TYPE_DEFAULT:
            continue
        if exp_type == "proxy" and max_age_config is not None:
            continue
        res.append(log)
    return len(res)


def main():  # noqa: C901
    logs = glob.glob(os.path.join(pc.DATA_PATH, "doc-eval-load-*[0-9].log"))
    logs += glob.glob(os.path.join(pc.DATA_PATH, "doc-eval-proxy-*[0-9].log"))
    logs += glob.glob(os.path.join(pc.DATA_PATH, "doc-eval-max_age-*[0-9].log"))
    ylabels = []
    xlabels = []
    lognums = []
    transport_borders = []
    method_borders = []
    blocksize_borders = []
    last_transport = None
    last_method = None
    last_blocksize = 0
    for transport in reversed(pc.TRANSPORTS):
        for m, method in enumerate(pc.COAP_METHODS):
            if transport not in pc.COAP_TRANSPORTS:
                if m > 0:
                    continue
                method = None
            for b, blocksize in enumerate(pc.COAP_BLOCKSIZE):
                if transport not in pc.COAP_TRANSPORTS or transport == "oscore":
                    if b > 0:
                        continue
                    blocksize = None
                for record_type in pc.RECORD_TYPES:
                    if blocksize is not None and blocksize == 64 and record_type == "A":
                        continue
                    lognums_col = []
                    if last_transport is None:
                        last_transport = transport
                    elif transport != last_transport:
                        transport_border = len(lognums) - 0.5
                        while method_borders and method_borders[-1] == transport_border:
                            method_borders.pop()
                        transport_borders.append(transport_border)
                        last_transport = transport
                        last_method = None
                        last_blocksize = 0
                    if last_method is None:
                        last_method = method
                    elif method != last_method:
                        method_border = len(lognums) - 0.5
                        while (
                            blocksize_borders and blocksize_borders[-1] == method_border
                        ):
                            blocksize_borders.pop()
                        if (
                            not transport_borders
                            or transport_borders[-1] != method_border
                        ):
                            method_borders.append(method_border)
                        method_borders.append(method_border)
                        last_method = method
                        last_blocksize = 0
                    if last_blocksize == 0:
                        last_blocksize = blocksize
                    elif blocksize != last_blocksize:
                        blocksize_border = len(lognums) - 0.5
                        if not method_borders or method_borders[-1] != blocksize_border:
                            blocksize_borders.append(blocksize_border)
                        last_blocksize = blocksize
                    for exp_type in pc.EXP_TYPES:
                        for proxied in pc.PROXIED:
                            for link_layer in pc.LINK_LAYERS:
                                avg_queries_per_sec = 5.0
                                delay_time, delay_count = (None, None)
                                for c, max_age_config in enumerate(pc.MAX_AGE_CONFIGS):
                                    if exp_type == "proxy":
                                        if c > 0:
                                            continue
                                        max_age_config = None
                                    if exp_type == "load":
                                        continue
                                    if link_layer == "ble":
                                        continue
                                    if not proxied and max_age_config == "subtract":
                                        continue
                                    if avg_queries_per_sec > 5 or (
                                        (delay_time, delay_count) != (None, None)
                                    ):
                                        continue
                                    if exp_type == "proxy" and proxied:
                                        continue
                                    if exp_type == "load":
                                        if (
                                            exp_type,
                                            link_layer,
                                            avg_queries_per_sec,
                                            delay_time,
                                            delay_count,
                                        ) not in xlabels:
                                            xlabels.append(
                                                (
                                                    exp_type,
                                                    link_layer,
                                                    avg_queries_per_sec,
                                                    delay_time,
                                                    delay_count,
                                                )
                                            )
                                    elif exp_type in ["proxy", "max_age"]:
                                        if (
                                            exp_type,
                                            link_layer,
                                            bool(proxied),
                                            max_age_config,
                                        ) not in xlabels:
                                            xlabels.append(
                                                (
                                                    exp_type,
                                                    link_layer,
                                                    bool(proxied),
                                                    max_age_config,
                                                )
                                            )
                                    lognums_col.append(
                                        count_logs(
                                            logs,
                                            exp_type,
                                            link_layer,
                                            transport,
                                            record_type,
                                            method,
                                            blocksize,
                                            proxied,
                                            avg_queries_per_sec,
                                            (delay_time, delay_count),
                                            max_age_config,
                                        )
                                    )
                    if numpy.isnan(lognums_col).all():
                        continue
                    lognums.append(lognums_col)
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
        last_transport = transport
    lognums = numpy.array(lognums).transpose()
    fig = matplotlib.pyplot.figure(figsize=(12, 5))
    norm = matplotlib.pyplot.Normalize(0, pc.RUNS)
    im = matplotlib.pyplot.imshow(lognums, cmap="RdYlBu", norm=norm)
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
        color="gray",
    )
    ax = matplotlib.pyplot.gca()
    cbar = fig.colorbar(im, ax=ax, location="top", aspect=58)
    cbar.ax.set_xlabel("Missing runs", va="bottom", ha="center")
    cbar.set_ticks(numpy.arange(pc.RUNS + 1))
    cbar.set_ticklabels(list(reversed(numpy.arange(pc.RUNS + 1))))
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
    textcolors = (2 * ["white"]) + (7 * ["black"]) + (2 * ["white"])
    for i in range(lognums.shape[0]):
        for j in range(lognums.shape[1]):
            if numpy.isnan(lognums[i, j]).all():
                kw["color"] = "red"
                im.axes.text(j, i, "X", **kw)
            else:
                text_idx = max(0, min(int(im.norm(lognums[i, j] * 10)), 10))
                kw.update(color=textcolors[text_idx])
                im.axes.text(j, i, f"{pc.RUNS - lognums[i, j]:.0f}", **kw)
    matplotlib.pyplot.tight_layout()
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(pc.DATA_PATH, f"doc-eval-done.{ext}"), bbox_inches="tight"
        )


if __name__ == "__main__":
    main()
