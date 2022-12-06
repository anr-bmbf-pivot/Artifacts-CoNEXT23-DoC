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

# import copy
import os

import matplotlib.lines
import matplotlib.pyplot

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


# def derive_axins_style(ax_style):
#     axins_style = copy.deepcopy(ax_style)
#     if "markevery" in axins_style:
#         axins_style["markevery"] = axins_style["markevery"] // 2
#     return axins_style


def main():  # noqa: C901
    parser = argparse.ArgumentParser()
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
    matplotlib.rcParams["legend.fontsize"] = "x-small"
    matplotlib.rcParams["legend.title_fontsize"] = "x-small"
    matplotlib.rcParams["legend.labelspacing"] = 0.2
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0] * 0.56,
        matplotlib.rcParams["figure.figsize"][1] * 0.9,
    )
    maxx = 0
    for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
        if avg_queries_per_sec > 5:
            continue
        plots_contained = 0
        blocksize_plotted = set()
        transports_plotted = set()
        for i, record in enumerate(reversed(pc.RECORD_TYPES)):
            ax = matplotlib.pyplot.gca()
            axins = None
            for transport in [
                t for t in pc.TRANSPORTS if t in pc.COAP_TRANSPORTS and t != "oscore"
            ]:
                for blocksize in pc.COAP_BLOCKSIZE:
                    if blocksize == 16 and avg_queries_per_sec > 5:
                        continue  # pragma: no cover
                    if blocksize == 64 and record == "A":
                        continue  # pragma: no cover
                    x, y = plot_load_cdf.process_data(
                        transport,
                        "fetch",
                        None,
                        None,
                        avg_queries_per_sec=avg_queries_per_sec,
                        record=record,
                        link_layer=args.link_layer,
                        blocksize=blocksize,
                    )
                    if len(x) == 0 or len(y) == 0:
                        continue  # pragma: no cover
                    transports_plotted.add(transport)
                    blocksize_plotted.add(blocksize)
                    style = pc.TRANSPORTS_STYLE[transport]
                    style.update(pc.BLOCKWISE_STYLE[blocksize])
                    if x.max() > maxx:
                        maxx = x.max()
                    ax.plot(
                        x,
                        y,
                        label=pc.TRANSPORTS_READABLE[transport],
                        **style,
                    )
                    # if axins:
                    #     axins_style = derive_axins_style(style)
                    #     axins.plot(
                    #         x,
                    #         y,
                    #         label=pc.TRANSPORTS_READABLE[transport],
                    #         **axins_style,
                    #     )
                    plots_contained += 1
                    plot_load_cdf.label_plots(
                        ax,
                        axins,
                        args.link_layer,
                        avg_queries_per_sec,
                        record,
                        xlim=87,
                        blockwise=True,
                    )
            # if axins:
            #     ax.indicate_inset_zoom(axins, edgecolor="black")
            if plots_contained:  # pragma: no cover
                if avg_queries_per_sec == 5:  # pragma: no cover
                    transport_readable = pc.TransportsReadable.TransportReadable
                    transport_handles = [
                        matplotlib.lines.Line2D(
                            [0],
                            [0],
                            label=transport_readable.TRANSPORTS_READABLE[transport],
                            **pc.TRANSPORTS_STYLE[transport],
                        )
                        for transport in reversed(pc.TRANSPORTS)
                        if transport in transports_plotted
                    ]
                    if record == "A":
                        ax.legend(
                            handles=transport_handles,
                            loc="lower right",
                            title="DNS Transports",
                        )
                    if blocksize_plotted != {None} and record == "AAAA":
                        blocksize_handles = [
                            matplotlib.lines.Line2D(
                                [0],
                                [0],
                                label=pc.BLOCKWISE_READABLE[blocksize],
                                color="gray",
                                linewidth=0 if blocksize is not None else None,
                                **pc.BLOCKWISE_STYLE[blocksize],
                            )
                            for blocksize in pc.COAP_BLOCKSIZE
                        ]
                        ax.legend(
                            handles=blocksize_handles,
                            handlelength=0.5,
                            loc="lower right",
                            title="Block sizes",
                        )
                for ext in pc.OUTPUT_FORMATS:
                    matplotlib.pyplot.savefig(
                        os.path.join(
                            pc.DATA_PATH,
                            f"doc-eval-load-{args.link_layer}-{record}-fetch-cdf-"
                            f"blockwise-{avg_queries_per_sec}.{ext}",
                        ),
                        bbox_inches="tight",
                        pad_inches=0.01,
                    )
            matplotlib.pyplot.close()


if __name__ == "__main__":
    main()  # pragma: no cover
