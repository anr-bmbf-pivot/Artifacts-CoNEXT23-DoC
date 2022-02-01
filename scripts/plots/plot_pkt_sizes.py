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
    "udp": {
        # doc-eval-load-udp-None-None-100x10.0-A-284619-1636041929.pcap.gz
        "query": {
            "lower": 75 - 28,
            "lower_var": 32,
            "dns": 28,
            "dns_var": 10,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "lower": 91 - 44,
            "lower_var": 32,
            "dns": 44,
            "dns_var": 12,
        },
        # doc-eval-load-udp-None-None-100x10.0-284025-1635455554.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "lower": 103 - 56,
            "lower_var": 32,
            "dns": 56,
            "dns_var": 12,
        },
    },
    "dtls": {
        # doc-eval-load-dtls-None-None-100x10.0-A-284631-1636050098.pcap.gz
        # TODO research variable parts of DTLS
        "dtls_client_hello": {
            "lower": 121 - 73,
            "lower_var": 32,
            "dtls": 73,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_hello_verify_req": {
            "lower": 92 - 44,
            "lower_var": 32,
            "dtls": 44,
        },
        "dtls_client_hello+cookie": {
            "lower": (124 - (120 - 40 - 8)) + (45 - 17),
            "lower_var": 44,
            "lower_frag": (124 - (120 - 40 - 8)),
            "lower_frag_var": 44 - 32,
            "dtls": 89,
            "dtls_frag": (120 - 40 - 8),
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello": {
            "lower": 111 - 63,
            "lower_var": 32,
            "dtls": 63,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello_done": {
            "lower": 73 - 25,
            "lower_var": 32,
            "dtls": 25,
        },
        "dtls_client_key_exc": {
            "lower": 90 - 42,
            "lower_var": 32,
            "dtls": 42,
            # "dtls_var": 15,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_change_cipher_spec": {
            "lower": 62 - 14,
            "lower_var": 32,
            "dtls": 14,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_finish": {
            "lower": 101 - 53,
            "lower_var": 32,
            "dtls": 53,
        },
        "query": {
            "lower": 105 - 57,
            "lower_var": 32,
            "dtls": 57 - 28,
            "dns": 28,
            "dns_var": 10,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "lower": 121 - 73,
            "lower_var": 32,
            "dtls": 73 - 44,
            "dns": 44,
            "dns_var": 12,
        },
        # doc-eval-load-dtls-None-None-100x10.0-284025-1635451309.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "lower": (116 - (112 - 40 - 8)) + (49 - 21),
            "lower_var": 44,
            "lower_frag": (116 - (112 - 40 - 8)),
            "lower_frag_var": 44 - 32,
            "dtls": 85 - 56,
            "dns": 56,
            # + 8 in lower since due to stripping there is more place in the fragment
            "dns_frag": (120 - 40 - 8) - (85 - 56),
            "dns_var": 12,
        },
    },
    "coap": {
        # doc-eval-load-coap-None-None-100x10.0-A-284640-1636101104.pcap.gz
        "query": {
            "lower": 99 - 51,
            "lower_var": 32,
            "coap": 51 - 28,
            "coap_var": 18,
            "dns": 28,
            "dns_var": 10,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "lower": 102 - 54,
            "lower_var": 32,
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
            "lower_var": 32,
            "coap": 66 - 56,
            "coap_var": 5,
            "dns": 56,
            "dns_var": 12,
        },
    },
    "coaps": {
        # doc-eval-load-coaps-None-None-100x10.0-A-284623-1636045983.pcap.gz
        "dtls_client_hello": {
            "lower": 121 - 73,
            "lower_var": 32,
            "dtls": 73,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_hello_verify_req": {
            "lower": 92 - 44,
            "lower_var": 32,
            "dtls": 44,
        },
        "dtls_client_hello+cookie": {
            "lower": (124 - (120 - 40 - 8)) + (45 - 17),
            "lower_var": 44,
            "lower_frag": (124 - (120 - 40 - 8)),
            "lower_frag_var": 44 - 32,
            "dtls": 89,
            "dtls_frag": (120 - 40 - 8),
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello": {
            "lower": 111 - 63,
            "lower_var": 32,
            "dtls": 63,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello_done": {
            "lower": 73 - 25,
            "lower_var": 32,
            "dtls": 25,
        },
        "dtls_client_key_exc": {
            "lower": 90 - 42,
            "lower_var": 32,
            "dtls": 42,
            # "dtls_var": 15,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_change_cipher_spec": {
            "lower": 62 - 14,
            "lower_var": 32,
            "dtls": 14,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_finish": {
            "lower": 101 - 53,
            "lower_var": 32,
            "dtls": 53,
        },
        # Name is only 9 characters long, so add one byte to queries and responses
        "query": {
            "lower": (124 - (120 - 40 - 8)) + (36 - 8),
            "lower_var": 44,
            "lower_frag": (124 - (120 - 40 - 8)),
            "lower_frag_var": 44 - 32,
            "dtls": 80 - 51,
            "coap": 51 - 28,
            "coap_var": 18,
            "dns": 28,
            "dns_frag": (120 - 40 - 8) - (80 - 51) - (51 - 28),
            "dns_var": 10,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "lower": (116 - (112 - 40 - 8)) + (45 - 17),
            "lower_var": 44,
            "lower_frag": (116 - (112 - 40 - 8)),
            "lower_frag_var": 44 - 32,
            "dtls": 83 - 54,
            "coap": 54 - 44,
            "coap_var": 5,
            "dns": 44,
            # + 8 in lower since due to stripping there is more place in the fragment
            "dns_frag": (120 - 40 - 8) - (83 - 54) - (54 - 44),
            "dns_var": 12,
        },
        # doc-eval-load-coaps-None-None-100x10.0-283970-1635353886.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "lower": (116 - (112 - 40 - 8)) + (59 - 31),
            "lower_var": 44,
            "lower_frag": (116 - (112 - 40 - 8)),
            "lower_frag_var": 44 - 32,
            "dtls": 95 - 66,
            "coap": 66 - 56,
            "coap_var": 5,
            "dns": 56,
            # + 8 in lower since due to stripping there is more place in the fragment
            "dns_frag": (120 - 40 - 8) - (95 - 66) - (66 - 56),
            "dns_var": 12,
        },
    },
    "oscore": {
        # doc-eval-load-oscore-None-None-100x10.0-A-284623-1636046886.pcap.gz
        "oscore_query_wo_echo": {
            "lower": 113 - 65,
            "lower_var": 32,
            "coap": 65 - 54,
            "coap_var": 2,
            "oscore": 54 - 46,
            "coap_inner": 46 - 28,
            "coap_inner_var": 16,
            "dns": 28,
            "dns_var": 10,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "oscore_unauth_response": {
            "lower": 77 - 29,
            "lower_var": 32,
            "coap": 29 - 19,
            "coap_var": 2,
            "oscore": 19 - 11,
            "coap_inner": 11,
            "coap_inner_var": 8,
        },
        "query": {  # query with echo option
            "lower": 123 - 75,
            "lower_var": 32,
            "coap": 75 - 64,
            "coap_var": 2,
            "oscore": 64 - 56,
            "coap_inner": 56 - 28,
            "coap_inner_var": 26,
            "dns": 28,
            "dns_var": 10,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "lower": 115 - 67,
            "lower_var": 32,
            "coap": 67 - 57,
            "coap_var": 4,
            "oscore": 57 - 49,
            "coap_inner": 49 - 44,
            "coap_inner_var": 2,
            "dns": 44,
            "dns_var": 12,
        },
        # doc-eval-load-oscore-None-None-100x10.0-284585-1635979703.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "lower": (116 - (112 - 40 - 8)) + (41 - 13),
            "lower_var": 44,
            "lower_frag": (116 - (112 - 40 - 8)),
            "lower_frag_var": 44 - 32,
            "coap": 79 - 69,
            "coap_var": 4,
            "oscore": 69 - 61,
            "coap_inner": 61 - 56,
            "coap_inner_var": 2,
            "dns": 56,
            # + 8 in lower since due to stripping there is more place in the fragment
            "dns_frag": (120 - 40 - 8) - (79 - 69) - (69 - 61) - (61 - 56),
            "dns_var": 12,
        },
    },
}
MESSAGE_TYPES = [
    "dtls_client_hello",
    "dtls_hello_verify_req",
    "dtls_client_hello+cookie",
    "dtls_server_hello",
    "dtls_server_hello_done",
    "dtls_client_key_exc",
    "dtls_change_cipher_spec",
    "dtls_finish",
    "oscore_query_wo_echo",
    "oscore_unauth_response",
    "query",
    "query_fetch",
    "query_get",
    "coap_2.31",
    "response_a",
    "response_aaaa",
]
MESSAGE_TYPES_READABLE = {
    "dtls_client_hello": "Client Hello",
    "dtls_hello_verify_req": "Hello Verify Request",
    "dtls_client_hello+cookie": "Client Hello[Cookie]",
    "dtls_server_hello": "Server Hello",
    "dtls_server_hello_done": "Server Hello Done",
    "dtls_client_key_exc": "Client Key Exchange",
    "dtls_change_cipher_spec": "Change Cipher Spec",
    "dtls_finish": "Finish",
    "oscore_query_wo_echo": "Query (w/o Echo)",
    "oscore_unauth_response": "4.01 Unauthorized",
    "query": "Query",
    "query_fetch": "Query [F/P]",
    "query_get": "Query [G]",
    "response_a": "Response (A)",
    "response_aaaa": "Response (AAAA)",
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
TRANSPORT_CIPHER = {
    "coap": "",
    "coaps": "AES-128-CCM-8",
    # AES128-CCM-8 ~= AES-CCM-16-64-128, but with 12 byte nonce instead of 13
    # see https://datatracker.ietf.org/doc/html/rfc6655#section-3
    # and https://datatracker.ietf.org/doc/html/rfc6655#section-4
    #   + https://datatracker.ietf.org/doc/html/rfc8152#section-10.2
    "oscore": "AES-128-CCM-8",
    "dtls": "AES-128-CCM-8",
    "udp": "",
}
TRANSPORT_FIGURE = {
    "coap": 2,
    "coaps": 3,
    "oscore": 4,
    "dtls": 1,
    "udp": 0,
}
TRANSPORT_HANDSHAKE = {
    "oscore": ("OSCORE\nrepeat\nwindow\ninit.", False),
    "dtls": ("DTLSv1.2 Handshake", True),
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


def plot_pkt_var(
    ax, prev_layer, prev_frag_layer, pkt_sizes, layer, mtypes_of_transport
):
    var = numpy.array(
        [
            pkt_sizes.get(m, {}).get(f"{layer}_var", 0.0)
            - pkt_sizes.get(m, {}).get(f"{layer}_frag_var", 0.0)
            for m in mtypes_of_transport
        ]
    )
    frag_var = numpy.array(
        [
            pkt_sizes.get(m, {}).get(f"{layer}_frag_var", 0.0)
            for m in mtypes_of_transport
        ]
    )
    if not var.any():
        return
    x = numpy.arange(len(mtypes_of_transport))
    ax.bar(x, var, bottom=prev_layer, **VAR_MARKERS_STYLE["var"])
    if frag_var.any():
        ax.bar(
            x,
            [y if y > 0 else numpy.nan for y in frag_var],
            bottom=prev_frag_layer,
            **VAR_MARKERS_STYLE["var"],
        )


def mark_handshake(ax, pkt_sizes, transport_cipher, left, ymax):
    print_cipher = True
    for crypto in ["dtls", "oscore"]:
        if any(mtype.startswith(f"{crypto}_") for mtype in pkt_sizes):
            # needs fixing to actual plot 'i's
            crypto_msg_idx = [
                i
                for i, mtype in enumerate(
                    mtype for mtype in MESSAGE_TYPES if mtype in pkt_sizes
                )
                if mtype.startswith(f"{crypto}_")
            ]
            rect = ax.add_patch(
                matplotlib.patches.Rectangle(
                    (min(crypto_msg_idx) - 1, 0),
                    max(crypto_msg_idx) + 1.5,
                    ymax,
                    zorder=-1,
                    alpha=0.3,
                    **LAYERS_STYLE[crypto],
                ),
            )
            left = rect.get_x() + rect.get_width()
            ax.text(
                min(crypto_msg_idx) - 0.4,
                ymax - 4,
                TRANSPORT_HANDSHAKE[crypto][0],
                horizontalalignment="left",
                verticalalignment="top",
                fontsize="xx-small",
            )
            # if TRANSPORT_HANDSHAKE[crypto][1]:
            #     print_cipher = False
            #     ax.text(
            #         min(crypto_msg_idx) + 0.4,
            #         ymax - 18,
            #         f"({transport_cipher})",
            #         horizontalalignment="left",
            #         verticalalignment="top",
            #         fontsize="xx-small",
            #     )
    return print_cipher, left


def plot_pkt_sizes(
    ax,
    pkt_sizes,
    mtypes_of_transport,
    ymax,
    layers_readable=LAYERS_READABLE,
    label=None,
    transport_cipher=None,
):
    prev_layer = None
    prev_frag_layer = numpy.array([127.0 for _ in mtypes_of_transport])
    for layer in LAYERS:
        y = numpy.array(
            [
                pkt_sizes.get(m, {}).get(
                    f"{layer}_frag", pkt_sizes.get(m, {}).get(layer, 0)
                )
                for m in mtypes_of_transport
            ]
        )
        if not y.any():
            continue
        y_frag = numpy.array(
            [
                (
                    pkt_sizes.get(m, {}).get(layer, 0)
                    - pkt_sizes.get(m, {})[f"{layer}_frag"]
                )
                if f"{layer}_frag" in pkt_sizes.get(m, {})
                else 0.0
                for m in mtypes_of_transport
            ]
        )
        if not y.any():
            continue
        xlabels = [MESSAGE_TYPES_READABLE[m] for m in mtypes_of_transport]
        x = numpy.arange(len(xlabels))
        ax.bar(
            x,
            y,
            bottom=prev_layer if prev_layer is not None else [0 for _ in y],
            label=layers_readable[layer],
            edgecolor="black",
            **LAYERS_STYLE[layer],
        )
        if y_frag.any():
            ax.bar(
                x,
                [y if y > 0 else numpy.nan for y in y_frag],
                bottom=prev_frag_layer,
                label=layers_readable[layer],
                edgecolor="black",
                **LAYERS_STYLE[layer],
            )
        plot_pkt_var(
            ax,
            prev_layer,
            prev_frag_layer,
            pkt_sizes,
            layer,
            mtypes_of_transport,
        )
        if y_frag.any():
            prev_frag_layer += y_frag
        # plot_pkt_frags(ax, res, transport, layer, mtypes_of_transport)
        if prev_layer is None:
            prev_layer = y
        else:
            prev_layer += y
        ax.set_xticks(x)
        ax.set_xticklabels(
            labels=xlabels,
            rotation=45,
            horizontalalignment="right",
            verticalalignment="top",
            # position=(3, 0.01),
        )
    xlim = ax.get_xlim()
    xlim = numpy.floor(xlim[0]) + 0.5, numpy.floor(xlim[1]) + 0.5
    ax.set_xlim(xlim[0], xlim[1])
    left = xlim[0]
    right = xlim[1]
    if transport_cipher:
        print_cipher, left = mark_handshake(ax, pkt_sizes, transport_cipher, left, ymax)
    ax.text(
        right - 0.1,
        ymax - 4,
        label,
        horizontalalignment="right",
        verticalalignment="top",
        fontsize="x-small",
    )
    # if print_cipher and TRANSPORT_CIPHER[transport]:
    #     ax.text(
    #         right - 0.1,
    #         ymax - 18,
    #         f"({TRANSPORT_CIPHER[transport]})",
    #         fontsize="xx-small",
    #         horizontalalignment="right",
    #         verticalalignment="top",
    #     )
    #     pass
    ax.grid(True, axis="y")


def main():  # pylint: disable=too-many-local-variables
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    matplotlib.rcParams["figure.figsize"] = (7.00137, 1.5)
    matplotlib.rcParams["legend.handletextpad"] = 0.2
    matplotlib.rcParams["legend.columnspacing"] = 0.4
    figure, axs = matplotlib.pyplot.subplots(
        1,
        len(pc.TRANSPORTS),
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
                        for transport in pc.TRANSPORTS
                    ]
                )
            ]
        },
    )
    ymax = 200
    fragy = 127
    for transport in pc.TRANSPORTS:
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
        plot_pkt_sizes(
            axs[idx],
            PKT_SIZES[transport],
            mtypes_of_transport,
            ymax,
            transport_cipher=TRANSPORT_CIPHER[transport],
            label=pc.TRANSPORTS_READABLE[transport],
        )
    xlim = axs[1].get_xlim()
    axs[1].text(
        xlim[0] + 3.05,
        fragy + 3,
        "IEEE 802.15.4 PDU\n$\\Rightarrow$ Fragmentation",
        color=FRAG_MARKER_COLOR,
        fontsize="x-small",
    )
    axs[0].set_ylabel("PDU [bytes]")
    matplotlib.pyplot.ylim(0, ymax)
    matplotlib.pyplot.yticks(numpy.arange(0, ymax + 1, 32))
    layer_handles = [
        matplotlib.patches.Patch(**LAYERS_STYLE[layer], label=LAYERS_READABLE[layer])
        for layer in LAYERS
        if not layer.endswith("_inner")
    ]
    layer_legend = figure.legend(
        handles=layer_handles,
        loc="upper left",
        ncol=len(LAYERS),
        bbox_to_anchor=(0.02, 1.02),
    )
    figure.add_artist(layer_legend)
    var_handles = [
        matplotlib.patches.Patch(**VAR_MARKERS_STYLE[m], label=VAR_MARKERS_READABLE[m])
        for m in VAR_MARKERS
    ]
    var_legend = figure.legend(
        handles=var_handles,
        loc="upper right",
        ncol=len(VAR_MARKERS),
        bbox_to_anchor=(0.98, 1.02),
    )
    figure.add_artist(var_legend)
    matplotlib.pyplot.tight_layout(w_pad=-4.8)
    matplotlib.pyplot.subplots_adjust(top=0.85, bottom=0)
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-namelen-10.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


if __name__ == "__main__":
    main()
