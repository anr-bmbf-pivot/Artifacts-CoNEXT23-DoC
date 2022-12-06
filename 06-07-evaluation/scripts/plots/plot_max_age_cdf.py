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
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_load_cdf

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def process_data(
    method,
    max_age_config,
    proxied=1,
    link_layer=pc.LINK_LAYER_DEFAULT,
    queries=pc.QUERIES_DEFAULT,
    record=pc.RECORD_TYPE_DEFAULT,
    node_num=None,
    dns_cache=None,
    client_coap_cache=None,
):
    files = pc.get_files(
        "max_age",
        transport="coap",
        method=method,
        delay_time=None,
        delay_queries=None,
        queries=queries,
        avg_queries_per_sec=5.0,
        record=record,
        link_layer=link_layer,
        proxied=proxied,
        max_age_config=max_age_config,
        node_num=node_num,
        dns_cache=dns_cache,
        client_coap_cache=client_coap_cache,
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
    return numpy.array([]), numpy.array([])  # pragma: no cover


def label_plots(ax, xlim=69):
    ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(1))
    ax.set_xlabel("Resolution time [s]")
    ax.set_xlim((-0.5, xlim))
    ax.set_xticks(numpy.arange(0, xlim + 1, step=10))
    ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
    ax.set_ylim((0, 1.02))
    ax.set_yticks(numpy.arange(0, 1.01, step=0.5))
    ax.grid(True, which="major")
    ax.grid(True, which="minor", linewidth=0.25)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--node-num",
        "-n",
        type=int,
        default=None,
        help="Number of nodes used in the experiment (default=None)",
    )
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    parser.add_argument(
        "link_layer",
        nargs="?",
        default=pc.LINK_LAYER_DEFAULT,
        choices=pc.LINK_LAYERS,
        help=f"Link layer to plot (default={pc.LINK_LAYER_DEFAULT})",
    )
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0],
        matplotlib.rcParams["figure.figsize"][1] * 0.7,
    )
    for max_age_config in pc.MAX_AGE_CONFIGS:
        for dns_cache in pc.DNS_CACHE:
            if dns_cache:
                continue
            for client_coap_cache in pc.CLIENT_COAP_CACHE:
                for proxied in pc.PROXIED:
                    if not proxied and max_age_config not in [None, "min"]:
                        continue
                    if not proxied and client_coap_cache:
                        continue
                    for record in ["AAAA"]:
                        plots_contained = 0
                        for method in pc.COAP_METHODS:
                            ax = matplotlib.pyplot.gca()
                            x, y = process_data(
                                method,
                                max_age_config,
                                proxied=proxied,
                                link_layer=args.link_layer,
                                record=record,
                                node_num=args.node_num,
                                dns_cache=int(dns_cache),
                                client_coap_cache=int(client_coap_cache),
                            )
                            if len(x) == 0 or len(y) == 0:
                                continue  # pragma: no cover
                            ax.plot(
                                x,
                                y,
                                label=pc.METHODS_READABLE[method],
                                **pc.TRANSPORTS_STYLE["coap"][method],
                            )
                            plots_contained += 1
                            label_plots(ax, xlim=62)
                            # ax.set_title(
                            #     "DoH-like (w/ caching)"
                            #     if proxied and max_age_config == "min"
                            #     else "EOL TTLs (w/ caching)"
                            #     if proxied
                            #     else "Opaque forwarder",
                            # )
                            if (
                                proxied
                                and client_coap_cache
                                and max_age_config == "subtract"
                                and args.node_num is None
                            ):
                                matplotlib.pyplot.legend(loc="lower right", ncol=3)
                        if plots_contained:  # pragma: no cover
                            matplotlib.pyplot.tight_layout()
                            for ext in pc.OUTPUT_FORMATS:
                                if args.node_num is None:
                                    filename = (
                                        f"doc-eval-max_age-"
                                        f"{args.link_layer}-dc{int(dns_cache)}-"
                                        f"ccc{int(client_coap_cache)}-"
                                        f"proxied{int(proxied)}-{max_age_config}-"
                                        f"cdf-None-None-5.0-{record}.{ext}"
                                    )
                                else:  # pragma: no cover
                                    filename = (
                                        f"doc-eval-max_age-{args.node_num}-"
                                        f"{args.link_layer}-dc{int(dns_cache)}-"
                                        f"ccc{int(client_coap_cache)}-"
                                        f"proxied{int(proxied)}-{max_age_config}-"
                                        f"cdf-None-None-5.0-{record}.{ext}"
                                    )
                                matplotlib.pyplot.savefig(
                                    os.path.join(pc.DATA_PATH, filename),
                                    bbox_inches="tight",
                                    pad_inches=0.01,
                                )
                        matplotlib.pyplot.close()


if __name__ == "__main__":
    main()  # pragma: no cover
