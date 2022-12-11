#! /usr/bin/env python3

# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import argparse
import os

import matplotlib
import matplotlib.patches
import matplotlib.pyplot
import matplotlib.ticker
import pandas

try:
    from . import parse_max_age_link_util
    from . import plot_common as pc
except ImportError:  # pragma: no cover
    import parse_max_age_link_util
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

METHODS = [
    "fetch",
]
CLIENT_COAP_CACHE = [
    0,
    1,
]
CLIENT_COAP_CACHE_READABLE = {
    0: "w/o CoAP client cache",
    1: "w/ CoAP client cache",
}
DNS_CACHE = [
    0,
    1,
]
DNS_CACHE_READABLE = {
    0: "w/o DNS\nclient cache",
    1: "w/ DNS\nclient cache",
}
MAX_AGE_CONFIG_READABLE = {
    "dohlike": "DoH-\nlike",
    "eolttls": "EOL\nTTLs",
}


def plot_stat(ax, df, stat):
    queries_column = f"queries_{stat}"
    resp_column = f"responses_{stat}"
    x = [0.5, 1.65, 2.35]
    groupby = df.groupby(
        [
            "distance",
            "node",
        ]
    )[[queries_column, resp_column]]
    mean = groupby.aggregate("mean")
    std = groupby.aggregate("std")
    if stat == "bytes":
        mean /= 1000
        std /= 1000
    ax.grid(True, axis="y", which="major")
    ax.grid(True, axis="y", which="minor", linewidth=0.25)
    ax.bar(
        x=x,
        height=mean[resp_column],
        yerr=std[resp_column],
        color="C1",
        width=0.6,
        capsize=2,
    )
    ax.bar(
        x=x,
        height=mean[queries_column],
        yerr=std[queries_column],
        color="C3",
        width=0.6,
        capsize=2,
        bottom=mean[resp_column],
    )
    ax.set_xticks(x)
    ax.tick_params(axis="both", which="major", length=2.0)
    ax.tick_params(axis="both", which="minor", length=1.5)
    ax.xaxis.set_ticklabels([])
    if stat == "bytes":
        y = 1
        ax.set_ylim((0, 100))
    else:
        y = 10
        ax.set_ylim((0, 899))
    ax.annotate(
        "",
        xy=(-0.04, -0.07),
        xycoords="axes fraction",
        xytext=(0.35, -0.07),
        arrowprops=dict(arrowstyle="|-|", mutation_aspect=0.1),
    )
    ax.annotate(
        "",
        xy=(0.39, -0.07),
        xycoords="axes fraction",
        xytext=(1.04, -0.07),
        arrowprops=dict(arrowstyle="|-|", mutation_aspect=0.1),
    )
    ax.text(0.5, -6.3 * y, "1", ha="center", va="top", fontsize="small")
    ax.text(2, -6.3 * y, "2", ha="center", va="top", fontsize="small")
    return mean[resp_column]


def plot_df(  # pylint: disable=too-many-arguments
    ax_bytes, ax_pkts, df, max_age_config, method, proxied, client_coap_cache, dns_cache
):
    df = df[df["max_age_config"] == max_age_config]
    df = df[df["method"] == method]
    df = df[df["proxied"] == proxied]
    df = df[df["client_coap_cache"] == client_coap_cache]
    df = df[df["dns_cache"] == dns_cache]
    plot_stat(ax_bytes, df, "bytes")
    ax_bytes.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(10))
    bottom = plot_stat(ax_pkts, df, "packets")  # noqa: F841 bottom used in GET code
    if (
        not proxied
        and not client_coap_cache
        and not dns_cache
        and max_age_config == "dohlike"
    ):
        ax_bytes.set_facecolor("#c6dbef")
        ax_pkts.set_facecolor("#c6dbef")
    if proxied and client_coap_cache and not dns_cache:
        ax_bytes.set_facecolor("#c6dbef")
        ax_pkts.set_facecolor("#c6dbef")
    # if method == "get":
    #     x = [0.5, 1.65, 2.35]
    #     queries_column = "queries_frags"
    #     resp_column = "responses_frags"
    #     groupby = df.groupby(
    #         [
    #             "distance",
    #             "node",
    #         ]
    #     )[[queries_column, resp_column]]
    #     mean = groupby.aggregate("mean")
    #     ax_pkts.bar(
    #         x=x,
    #         height=mean[resp_column],
    #         facecolor="C1",
    #         hatch="xxxxxxxxxx",
    #         edgecolor="white",
    #         lw=0,
    #         width=0.6,
    #         capsize=2,
    #     )
    #     ax_pkts.bar(
    #         x=x,
    #         height=mean[queries_column],
    #         color="C3",
    #         hatch="xxxxxxxxxx",
    #         edgecolor="white",
    #         lw=0,
    #         width=0.6,
    #         capsize=2,
    #         bottom=bottom,
    #     )
    ax_pkts.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(100))


def annotate_setup(ax, width, height, setup):
    ax.annotate(
        "",
        xy=(-0.15, height),
        xycoords="axes fraction",
        xytext=(width * 1.15, height),
        arrowprops=dict(arrowstyle="|-|", mutation_aspect=0.2),
    )
    ax.annotate(
        setup,
        xy=((width * 1.15 - 0.15) / 2, height - 0.01),
        xycoords="axes fraction",
        xytext=((width * 1.15 - 0.15) / 2, height - 0.01),
        ha="center",
        va="bottom",
        fontsize="small",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    matplotlib.rcParams["figure.subplot.bottom"] = 0.07
    matplotlib.rcParams["figure.subplot.wspace"] = 0.15
    matplotlib.rcParams["legend.fontsize"] = "x-small"
    matplotlib.rcParams["legend.framealpha"] = 0.95
    matplotlib.rcParams["figure.figsize"] = (
        7.00697 / 1.76,
        1.75,
    )
    df = pandas.read_csv(parse_max_age_link_util.CSV_NAME)
    last_max_age_config = None
    last_client_coap_cache = None
    last_dns_cache = None
    for method in METHODS:
        for proxied in pc.PROXIED:
            fig = matplotlib.pyplot.figure(
                figsize=(
                    matplotlib.rcParams["figure.figsize"][0],
                    matplotlib.rcParams["figure.figsize"][1] * 0.71,
                )
            )
            subfigs = fig.subfigures(2, 1)
            axs_pkts = subfigs[0].subplots(
                1,
                len(pc.MAX_AGE_CONFIGS) * len(CLIENT_COAP_CACHE) * len(DNS_CACHE),
                sharey=True,
                sharex=True,
            )
            axs_bytes = subfigs[1].subplots(
                1,
                len(pc.MAX_AGE_CONFIGS) * len(CLIENT_COAP_CACHE) * len(DNS_CACHE),
                sharey=True,
                sharex=True,
            )
            ax_idx = 0
            for client_coap_cache in CLIENT_COAP_CACHE:
                for dns_cache in DNS_CACHE:
                    for max_age_config in pc.MAX_AGE_CONFIGS:
                        if last_client_coap_cache != client_coap_cache:
                            annotate_setup(
                                axs_pkts[ax_idx],
                                4,
                                1.87,
                                CLIENT_COAP_CACHE_READABLE[client_coap_cache],
                            )
                        if last_dns_cache != dns_cache:
                            annotate_setup(
                                axs_pkts[ax_idx], 2, 1.45, DNS_CACHE_READABLE[dns_cache]
                            )
                        if last_max_age_config != max_age_config:  # pragma: no cover
                            annotate_setup(
                                axs_pkts[ax_idx],
                                1,
                                1.03,
                                MAX_AGE_CONFIG_READABLE[max_age_config],
                            )
                        plot_df(
                            axs_bytes[ax_idx],
                            axs_pkts[ax_idx],
                            df,
                            max_age_config,
                            method,
                            proxied,
                            client_coap_cache,
                            dns_cache,
                        )
                        ax_idx += 1
                        last_max_age_config = max_age_config
                        last_client_coap_cache = client_coap_cache
                        last_dns_cache = dns_cache
            fig.text(
                0.5,
                -0.12,
                "Link distance to sink [hops]",
                ha="center",
                fontsize="small",
            )
            if not proxied:
                axs_pkts[0].set_ylabel(r"L2 Frames [\#]")
                axs_bytes[0].set_ylabel("Bytes [kBytes]")
            else:
                axs_pkts[0].yaxis.set_ticklabels([])
                axs_bytes[0].yaxis.set_ticklabels([])
            if proxied:
                axs_pkts[len(axs_pkts) - 1].legend(["Responses", "Queries"])
            for ext in pc.OUTPUT_FORMATS:
                matplotlib.pyplot.savefig(
                    os.path.join(
                        pc.DATA_PATH,
                        f"doc-eval-max_age-{method}-proxied{proxied:d}-"
                        f"link_utilization.{ext}",
                    ),
                    bbox_inches="tight",
                    pad_inches=0.01,
                )


if __name__ == "__main__":
    main()  # pragma: no cover
