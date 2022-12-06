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
import os

import matplotlib.pyplot
import numpy

try:
    from . import plot_common as pc
    from . import plot_load_cdf
    from . import plot_load_trans
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_load_cdf
    import plot_load_trans

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def main():  # noqa: C901
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    matplotlib.rcParams["axes.labelsize"] = "xx-small"
    matplotlib.rcParams["xtick.labelsize"] = "xx-small"
    matplotlib.rcParams["ytick.labelsize"] = "xx-small"
    matplotlib.rcParams["legend.fontsize"] = "xx-small"
    transport = "coap"
    mx0 = []
    mx1 = []
    my = []
    size = matplotlib.pyplot.gcf().get_size_inches()
    size = size[0], size[1] / 1.5
    for m, method in enumerate(pc.COAP_METHODS):
        for record in pc.RECORD_TYPES:
            if record != "AAAA":
                continue
            time, queries = None, None
            for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
                if avg_queries_per_sec > 5:
                    continue
                fig = matplotlib.pyplot.figure(figsize=size)
                axsup = fig.subplots(1, 2, sharey=True, gridspec_kw={"wspace": 0.11})
                axs = fig.subplots(
                    1,
                    5,
                    sharey=True,
                    gridspec_kw={"wspace": 0.15, "width_ratios": [4, 1, 0.01, 4, 1]},
                )
                axs[2].remove()
                for ax in axs:
                    if ax == axs[2]:
                        continue
                    plot_load_trans.mark_exp_retrans(ax)
                for proxied in pc.PROXIED:
                    ax0 = axs[int(proxied) * 3]
                    ax1 = axs[int(proxied) * 3 + 1]
                    transmissions, cache_hits = plot_load_trans.process_data(
                        transport,
                        method,
                        time,
                        queries,
                        avg_queries_per_sec=avg_queries_per_sec,
                        record=record,
                        exp_type="proxy",
                        proxied=proxied,
                    )
                    if len(transmissions) == 0:
                        continue  # pragma: no cover
                    mx0.append(transmissions[:, 0].max())
                    my.append(transmissions[:, 1].max())
                    ax0.scatter(
                        transmissions[:, 0],
                        transmissions[:, 1],
                        s=6,
                        marker=".",
                        linewidth=0,
                        label="Client send",
                        alpha=0.5,
                        **pc.TRANSPORTS_STYLE[transport],
                    )
                    if len(transmissions[:, 1]) == 0:
                        continue  # pragma: no cover
                    if len(cache_hits):
                        ax0.scatter(
                            cache_hits[:, 0],
                            cache_hits[:, 1],
                            s=15,
                            marker="x",
                            color="#74c476",
                            linewidth=0.4,
                            label="Cache hit",
                            alpha=0.8,
                        )
                    x, y = plot_load_cdf.cdf(transmissions[:, 1])
                    ax1.plot(
                        y,
                        x,
                        label="Transport transmissions",
                        **pc.TRANSPORTS_STYLE[transport][method],
                    )
                    ax1.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
                    ax1.set_xlabel("CDF")
                    ax1.set_xticks(numpy.arange(0, 1.5, step=1))
                    mx1.append(ax1.get_xlim()[1])
                    ax1.set_xlim((0, 1.05))
                    ax1.grid(True, axis="x", which="major")
                    ax1.grid(
                        True,
                        axis="x",
                        which="minor",
                        linewidth=0.25,
                    )
                    plot_load_trans.label_plot(
                        ax0,
                        11 if avg_queries_per_sec == 10 else 21,
                        50,
                        transport,
                        method,
                        time,
                        exp_type="proxy",
                        proxied=proxied,
                    )
                    for ax in axsup:
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
                    if method == "fetch":
                        axsup[int(proxied)].set_title(
                            "Forward proxy" if proxied else "Opaque forwarder",
                        )
                        if proxied:
                            ax0.legend(loc="upper right")
                fig.tight_layout(w_pad=-2)
                for ext in pc.OUTPUT_FORMATS:
                    fig.savefig(
                        os.path.join(
                            pc.DATA_PATH,
                            f"doc-eval-proxy-ieee802154-trans-{transport}%s-"
                            f"{time}-{queries}-"
                            f"{avg_queries_per_sec}-{record}.{ext}"
                            % (f"-{method}" if transport in pc.COAP_TRANSPORTS else ""),
                        ),
                        bbox_inches="tight",
                        pad_inches=0.01,
                    )
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
