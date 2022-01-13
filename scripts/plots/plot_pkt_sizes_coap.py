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

import os

import matplotlib.lines
import matplotlib.patches
import matplotlib.pyplot
import numpy

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


DTLS_MSGS = {}
PKT_SIZES = {
    "coap": {
        # doc-eval-load-ieee802154-coap-fetch-None-None-100x5.0-A-289166-1639486177.pcap.gz
        "query_fetch": {
            "lower": 99 - 51,
            "coap": 51 - 28,
            "coap_var": 18,
            "dns": 28,
            "dns_var": 10,
        },
        # doc-eval-load-ieee802154-coap-get-None-None-100x10.0-A-291129-1641555577.pcap.gz
        "query_get": {
            "lower": 99 - 51,
            "coap": 63 - 38,
            "coap_var": 17,
            "dns": 38,
            "dns_var": 14,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "lower": 102 - 54,
            "coap": 54 - 44,
            "coap_var": 5,
            "dns": 44,
            "dns_var": 12,
        },
        # doc-eval-load-coap-1.0-25-100x5.0-284361-1635777176.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "lower": 114 - 66,
            "coap": 66 - 56,
            "coap_var": 5,
            "dns": 56,
            "dns_var": 12,
        },
    },
    "coap16": {
        # doc-eval-load-ieee802154-coap-fetch-b16-None-None-100x5.0-A-290957-1641394073.pcap.gz
        "query_fetch": {
            "lower": 99 - 51,
            "coap": 45 - 16,
            "coap_var": 21,
            "dns": 16,
            "dns_var": 16,
        },
        # doc-eval-load-ieee802154-coap-get-None-None-100x10.0-A-291129-1641555577.pcap.gz
        "query_get": {
            "lower": 99 - 51,
            "coap": 63 - 38,
            "coap_var": 17,
            "dns": 38,
            "dns_var": 14,
        },
        # doc-eval-load-ieee802154-coap-fetch-b16-None-None-100x5.0-A-290957-1641394073.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "coap_2.31": {
            "lower": 57 - 9,
            "coap": 9,
            "coap_var": 2,
        },
        # doc-eval-load-ieee802154-coap-fetch-b16-None-None-100x5.0-A-290957-1641394073.pcap.gz
        "response_a": {
            "lower": 102 - 54,
            "coap": 30 - 16,
            "coap_var": 7,
            "dns": 16,
            "dns_var": 8,
        },
        # doc-eval-load-ieee802154-coap-fetch-b16-None-None-100x5.0-A-290957-1641394073.pcap.gz
        "response_aaaa": {
            "lower": 102 - 54,
            "coap": 30 - 16,
            "coap_var": 7,
            "dns": 16,
            "dns_var": 8,
        },
    },
    "coap32": {
        # doc-eval-load-ieee802154-coap-fetch-b32-None-None-100x5.0-A-290911-1641382075.pcap.gz
        "query_fetch": {
            "lower": 99 - 51,
            "coap": 58 - 28,
            "coap_var": 21,
            "dns": 28,
            "dns_var": 28,
        },
        # doc-eval-load-ieee802154-coap-get-None-None-100x10.0-A-291129-1641555577.pcap.gz
        "query_get": {
            "lower": 99 - 51,
            "coap": 63 - 38,
            "coap_var": 17,
            "dns": 38,
            "dns_var": 14,
        },
        # doc-eval-load-ieee802154-coap-fetch-b32-None-None-100x5.0-A-290911-1641382075.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "coap_2.31": {
            "lower": 57 - 9,
            "coap": 9,
            "coap_var": 2,
        },
        # doc-eval-load-ieee802154-coap-fetch-b32-None-None-100x5.0-A-290911-1641382075.pcap.gz
        "response_a": {
            "lower": 102 - 54,
            "coap": 44 - 32,
            "coap_var": 5,
            "dns": 32,
            "dns_var": 24,
        },
        # doc-eval-load-ieee802154-coap-fetch-b32-None-None-100x5.0-A-290911-1641382075.pcap.gz
        "response_aaaa": {
            "lower": 102 - 54,
            "coap": 44 - 32,
            "coap_var": 5,
            "dns": 32,
            "dns_var": 24,
        },
    },
}
MESSAGE_TYPES = [
    "query_fetch",
    "query_get",
    "coap_2.31",
    "response_a",
    "response_aaaa",
]
MESSAGE_TYPES_READABLE = {
    "query_fetch": "Query [F/P]",
    "query_get": "Query [G]",
    "response_a": "Response (A Record)",
    "response_aaaa": "Response (AAAA Record)",
    "coap_2.31": "2.31 Continue",
}
LAYERS = [
    "lower",
    "dtls",
    "coap",
    "oscore",
    "coap_inner",
    "dns",
]
LAYERS_READABLE = {
    "lower": r"IEEE802.15.4\&6LoWPAN+NHC",
    "dtls": "DTLS",
    "coap": "CoAP",
    "oscore": "OSCORE",
    "coap_inner": "CoAP",
    "dns": "DNS",
}
LAYERS_STYLE = {
    "lower": {"color": "#8dd3c7"},
    "dtls": {"color": "#fdb462"},
    "coap": {"color": "#bebada"},
    "oscore": {"color": "#fb8072"},
    "coap_inner": {"color": "#bebada"},
    "dns": {"color": "#80b1d3"},
}
TRANSPORT_FIGURE = {
    "coap": 0,
    "coap16": 1,
    "coap32": 2,
}
TRANSPORTS_READABLE = {
    "coap": "CoAP\n(No blockwise)",
    "coap16": "CoAP\n(BS: 16 bytes)",
    "coap32": "CoAP\n(BS: 32 bytes)",
}
FRAG_MARKER_COLOR = "#f33"
VAR_MARKERS = ["var", "const"]
VAR_MARKERS_STYLE = {
    "var": {
        "linewidth": 0.5,
        "hatch": "////",
        "fill": False,
    },
    "const": {"linewidth": 0.5, "fill": False},
}
VAR_MARKERS_READABLE = {
    "var": "Variable part",
    "const": "Constant part",
}


def plot_pkt_frags(ax, bar_plot, transport, layer, mtypes_of_transport):
    frags = numpy.array(
        [
            PKT_SIZES[transport].get(m, {}).get(f"{layer}_frag", 0)
            if PKT_SIZES[transport].get(m, {}).get(f"{layer}_frag", 0) > 0
            else numpy.nan
            for m in mtypes_of_transport
        ]
    )
    for frag, rect in zip(frags, bar_plot):
        if not numpy.isnan(frag):
            ax.add_line(
                matplotlib.lines.Line2D(
                    [rect.get_x(), rect.get_x() + rect.get_width()],
                    [rect.get_y() + frag, rect.get_y() + frag],
                    color="black",
                    linewidth=1,
                    linestyle=":",
                    solid_capstyle="butt",
                )
            )


def plot_pkt_var(ax, prev_layer, transport, layer, mtypes_of_transport):
    var = numpy.array(
        [
            PKT_SIZES[transport].get(m, {}).get(f"{layer}_var", 0)
            for m in mtypes_of_transport
        ]
    )
    if not var.any():
        return
    x = numpy.arange(len(mtypes_of_transport))
    ax.bar(x, var, bottom=prev_layer, **VAR_MARKERS_STYLE["var"])


def main():  # pylint: disable=too-many-local-variables
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    figure, axs = matplotlib.pyplot.subplots(
        1,
        len(TRANSPORT_FIGURE),
        sharey=True,
        gridspec_kw={
            "width_ratios": [
                b
                for a, b in sorted(
                    [
                        (
                            TRANSPORT_FIGURE[transport],
                            len(PKT_SIZES.get(transport, {})),
                        )
                        for transport in TRANSPORT_FIGURE
                    ]
                )
            ]
        },
    )
    ymax = 200
    fragy = 127
    for _, transport in sorted((v, k) for k, v in TRANSPORT_FIGURE.items()):
        if transport not in PKT_SIZES:
            continue
        idx = TRANSPORT_FIGURE[transport]
        axs[idx].axhline(y=fragy, color=FRAG_MARKER_COLOR, linestyle="--")
        mtypes_of_transport = set()
        for layer in LAYERS:
            for m in MESSAGE_TYPES:
                if m in PKT_SIZES[transport]:
                    mtypes_of_transport.add(m)
        mtypes_of_transport = sorted(
            mtypes_of_transport, key=lambda m: MESSAGE_TYPES.index(m)
        )
        prev_layer = None
        for layer in LAYERS:
            y = numpy.array(
                [
                    PKT_SIZES[transport].get(m, {}).get(layer, 0)
                    for m in mtypes_of_transport
                ]
            )
            if not y.any():
                continue
            xlabels = [MESSAGE_TYPES_READABLE[m] for m in mtypes_of_transport]
            x = numpy.arange(len(xlabels))
            res = axs[idx].bar(
                x,
                y,
                bottom=prev_layer if prev_layer is not None else [0 for _ in y],
                label=LAYERS_READABLE[layer],
                edgecolor="black",
                **LAYERS_STYLE[layer],
            )
            plot_pkt_var(axs[idx], prev_layer, transport, layer, mtypes_of_transport)
            plot_pkt_frags(axs[idx], res, transport, layer, mtypes_of_transport)
            if prev_layer is None:
                prev_layer = y
            else:
                prev_layer += y
            axs[idx].set_xticks(x)
            axs[idx].set_xticklabels(
                labels=xlabels,
                rotation=45,
                horizontalalignment="right",
                verticalalignment="top",
                # position=(3, 0.01),
            )
        xlim = axs[idx].get_xlim()
        xlim = numpy.floor(xlim[0]) + 0.5, numpy.floor(xlim[1]) + 0.5
        axs[idx].set_xlim(xlim[0], xlim[1])
        right = xlim[1]
        axs[idx].text(
            right - 0.1,
            ymax - 4,
            TRANSPORTS_READABLE[transport],
            horizontalalignment="right",
            verticalalignment="top",
            fontsize="x-small",
        )
        axs[idx].grid(True, axis="y")
    xlim = axs[1].get_xlim()
    axs[0].set_ylabel("PDU [bytes]")
    matplotlib.pyplot.ylim(0, ymax)
    matplotlib.pyplot.yticks(numpy.arange(0, ymax + 1, 32))
    matplotlib.pyplot.tight_layout(w_pad=-2.9)
    matplotlib.pyplot.subplots_adjust(top=0.85, bottom=0)
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-namelen-10-coap.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


if __name__ == "__main__":
    main()
