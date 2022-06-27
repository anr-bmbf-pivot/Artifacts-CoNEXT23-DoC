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

import os

import matplotlib.pyplot

try:
    from . import plot_common as pc
    from . import plot_load_cdf
    from . import plot_load_trans
except ImportError:
    import plot_common as pc
    import plot_load_cdf
    import plot_load_trans

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def main():  # noqa: C901
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    # matplotlib.rcParams["axes.labelsize"] = "xx-small"
    matplotlib.rcParams["legend.fontsize"] = "x-small"
    matplotlib.rcParams["legend.handlelength"] = 1
    matplotlib.rcParams["legend.handletextpad"] = 0.2
    matplotlib.rcParams["legend.labelspacing"] = 0.75
    # matplotlib.rcParams["xtick.labelsize"] = "xx-small"
    # matplotlib.rcParams["ytick.labelsize"] = "xx-small"
    # matplotlib.rcParams["ytick.major.size"] = 3
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0] * 1.10,
        matplotlib.rcParams["figure.figsize"][1] * 2.4,
    )
    transport = "coap"
    mx0 = []
    mx1 = []
    my = []
    for record in pc.RECORD_TYPES:
        if record != "AAAA":
            continue
        fig = matplotlib.pyplot.figure()
        axsup = fig.subplots(1, 3, sharey=True, gridspec_kw={"wspace": 0.08})
        subplots = fig.subplots(
            3,
            3,  # 8,
            sharex=True,
            sharey=True,
            gridspec_kw={
                "hspace": 0.11,
                "wspace": 0.08,
                # "width_ratios": [4, 1, 0.01, 4, 1, 0.01, 4, 1],
            },
        )
        for m, method in enumerate(pc.COAP_METHODS):
            axs = subplots[m]
            axs[0].text(
                -4.75,
                45 / 2,
                pc.METHODS_READABLE[method],
                verticalalignment="center",
                rotation=90,
                clip_on=False,
            )
            # axs[2].remove()
            # axs[5].remove()
            time, queries = None, None
            for ax in axs:
                # if ax == axs[2] or ax == axs[5]:
                #     continue
                plot_load_trans.mark_exp_retrans(ax)
            for max_age_config in pc.MAX_AGE_CONFIGS:
                for proxied in pc.PROXIED:
                    if not proxied and max_age_config not in [None, "min"]:
                        continue
                    idx = int(proxied) + (pc.MAX_AGE_CONFIGS.index(max_age_config))
                    ax0 = axs[idx]
                    # ax1 = axs[idx + 1]
                    transmissions, cache_hits = plot_load_trans.process_data(
                        transport,
                        method,
                        time,
                        queries,
                        avg_queries_per_sec=5.0,
                        record=record,
                        exp_type="max_age",
                        proxied=proxied,
                        max_age_config=max_age_config,
                    )
                    if len(transmissions) == 0:
                        continue
                    mx0.append(transmissions[:, 0].max())
                    my.append(transmissions[:, 1].max())
                    if len(cache_hits):
                        ax0.scatter(
                            cache_hits[:, 0],
                            cache_hits[:, 1],
                            s=5,
                            marker="x",
                            color="#31a354",
                            # linewidth=0.4,
                            label="Cache hit",
                            alpha=1,
                        )
                    ax0.scatter(
                        transmissions[:, 0],
                        transmissions[:, 1],
                        s=6,
                        marker=".",
                        linewidth=0,
                        label="CoAP\ntransmission",
                        alpha=0.8,
                        **pc.TRANSPORTS_STYLE[transport],
                    )
                    if len(transmissions[:, 1]) == 0:
                        continue
                    x, y = plot_load_cdf.cdf(transmissions[:, 1])
                    # ax1.plot(
                    #     y,
                    #     x,
                    #     label="Transport transmissions",
                    #     **pc.TRANSPORTS_STYLE[transport][method],
                    # )
                    ax0.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(1))
                    # ax1.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.2))
                    # ax1.set_xlabel("CDF")
                    # ax1.set_xticks(numpy.arange(0, 1.5, step=1))
                    # mx1.append(ax1.get_xlim()[1])
                    # ax1.set_xlim((0, 1.05))
                    # ax1.grid(True, axis="x", which="major")
                    # ax1.grid(True, axis="x", which="minor", linewidth=0.25)
                    plot_load_trans.label_plot(
                        ax0,
                        10.5,
                        45,
                        transport,
                        method,
                        time,
                        exp_type="max_age",
                        proxied=proxied,
                        labelx=proxied and max_age_config == "min" and method == "post",
                        xlabeltext="Timestamp of DNS query [s]",
                        labely=method == "get",
                        ylabeltext="Event time offset to DNS query [s]",
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
                        axsup_idx = int(proxied) + pc.MAX_AGE_CONFIGS.index(
                            max_age_config
                        )
                        axsup[axsup_idx].set_title(
                            "DoH-like\n(w/ caching)"
                            if proxied and max_age_config == "min"
                            else "EOL TTLs\n(w/ caching)"
                            if proxied
                            else "Opaque\nforwarder",
                        )
                        if proxied and max_age_config == "subtract":
                            ax0.legend(loc="upper right")
        for ext in pc.OUTPUT_FORMATS:
            fig.savefig(
                os.path.join(
                    pc.DATA_PATH,
                    f"doc-eval-max_age-ieee802154-trans-"
                    f"{transport}-{time}-{queries}-"
                    f"5.0-{record}.{ext}"
                    # % (f"-{method}" if transport in pc.COAP_TRANSPORTS else ""),
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.close(fig)
    try:
        print(max(mx0))
    except ValueError:
        print(0)
    try:
        print(max(mx1))
    except ValueError:
        print(0)
    try:
        print(max(my))
    except ValueError:
        print(0)


if __name__ == "__main__":
    main()