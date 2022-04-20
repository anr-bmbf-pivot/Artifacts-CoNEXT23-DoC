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
import copy
import os

import matplotlib.lines
import matplotlib.pyplot

try:
    from . import plot_common as pc
    from . import plot_load_cdf
except ImportError:
    import plot_common as pc
    import plot_load_cdf

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def derive_axins_style(ax_style):
    axins_style = copy.deepcopy(ax_style)
    if "markevery" in axins_style:
        axins_style["markevery"] = axins_style["markevery"] // 2
    return axins_style


def main():  # noqa: C901
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "link_layer",
        nargs="?",
        default=pc.LINK_LAYER_DEFAULT,
        choices=pc.LINK_LAYERS,
        help=f"Link layer to plot (default={pc.LINK_LAYER_DEFAULT})",
    )
    args = parser.parse_args()
    maxx = 0
    for avg_queries_per_sec in pc.AVG_QUERIES_PER_SEC:
        if avg_queries_per_sec > 5:
            continue
        plots_contained = 0
        blocksize_plotted = set()
        transports_plotted = set()
        fig = matplotlib.pyplot.gcf()
        axs = fig.subplots(1, 2, sharey=True)
        for i, record in enumerate(reversed(pc.RECORD_TYPES)):
            ax = axs[i]
            ax.set_title(f"{record} record")
            axins = None
            for transport in [
                t for t in pc.TRANSPORTS if t in pc.COAP_TRANSPORTS and t != "oscore"
            ]:
                for blocksize in pc.COAP_BLOCKSIZE:
                    if blocksize == 16 and avg_queries_per_sec > 5:
                        continue
                    if blocksize == 64 and record == "A":
                        continue
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
                        continue
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
                    if axins:
                        axins_style = derive_axins_style(style)
                        axins.plot(
                            x,
                            y,
                            label=pc.TRANSPORTS_READABLE[transport],
                            **axins_style,
                        )
                    plots_contained += 1
                    plot_load_cdf.label_plots(
                        ax,
                        axins,
                        args.link_layer,
                        avg_queries_per_sec,
                        record,
                        xlim=83,
                        blockwise=True,
                    )
            if axins:
                ax.indicate_inset_zoom(axins, edgecolor="black")
        if plots_contained:
            if avg_queries_per_sec == 5:
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
                fig.legend(
                    handles=transport_handles,
                    loc="lower right",
                    title="DNS Transports",
                    bbox_to_anchor=(0.95, -0.28),
                )
                if blocksize_plotted != {None}:
                    blocksize_handles = [
                        matplotlib.lines.Line2D(
                            [0],
                            [0],
                            label=pc.BLOCKWISE_READABLE[blocksize],
                            color="gray",
                            **pc.BLOCKWISE_STYLE[blocksize],
                        )
                        for blocksize in pc.COAP_BLOCKSIZE
                    ]
                    fig.legend(
                        handles=blocksize_handles,
                        loc="lower left",
                        title="Block sizes",
                        bbox_to_anchor=(0.05, -0.28),
                        ncol=2,
                    )
            matplotlib.pyplot.tight_layout(w_pad=0.2)
            for ext in pc.OUTPUT_FORMATS:
                matplotlib.pyplot.savefig(
                    os.path.join(
                        pc.DATA_PATH,
                        f"doc-eval-load-{args.link_layer}-fetch-cdf-blockwise-"
                        f"{avg_queries_per_sec}.{ext}",
                    ),
                    bbox_inches="tight",
                    pad_inches=0.01,
                )
        matplotlib.pyplot.close()


if __name__ == "__main__":
    main()
