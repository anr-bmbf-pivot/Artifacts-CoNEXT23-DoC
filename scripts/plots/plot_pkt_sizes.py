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


import os

import matplotlib.pyplot
import matplotlib.style
import matplotlib.ticker
import numpy

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


IPHC_NHC_COMP_HDTSZ = 40 + 8

PKT_SIZES = {
    "udp": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-udp-proxied0-None-None-50x5.0-AAAA-297517-1646043265.pcap.gz
        # frames 498
        "query": {
            "lower": [104],
            "dns": [42],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-udp-proxied0-None-None-50x5.0-A-297517-1646020465.pcap.gz
        # frames 622
        "response_a": {
            "lower": [122],
            "dns": [58],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-udp-proxied0-None-None-50x5.0-AAAA-297517-1646043265.pcap.gz
        # frames 506, 507
        "response_aaaa": {
            "lower": [123, 40],
            "dns": [104 - IPHC_NHC_COMP_HDTSZ, 14],
        },
    },
    "dtls": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 215, 217
        "dtls_client_hello": {
            "lower": [123, 43],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 17],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 228
        "dtls_hello_verify_req": {
            "lower": [107],
            "dtls": [44],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 240, 241
        "dtls_client_hello+cookie": {
            "lower": [123, 59],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 33],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 253, 254
        "dtls_server_hello": {
            "lower": [123, 33],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 7],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 268
        "dtls_server_hello_done": {
            "lower": [88],
            "dtls": [25],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 279
        "dtls_client_key_exc": {
            "lower": [105],
            "dtls": [42],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 289
        "dtls_change_cipher_spec": {
            "lower": [77],
            "dtls": [14],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 297
        "dtls_finish": {
            "lower": [116],
            "dtls": [53],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 1398, 1399
        "query": {
            "lower": [123, 41],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 15],
            "dns": [42 - 15, 15],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 1537, 1538
        "response_a": {
            "lower": [123, 57],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 31],
            "dns": [58 - 31, 31],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-dtls-proxied0-None-None-50x5.0-AAAA-297517-1645996717.pcap.gz
        # frames 2842, 2843
        "response_aaaa": {
            "lower": [123, 69],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 43],
            "dns": [70 - 43, 43],
        },
    },
    "coap": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-None-None-50x5.0-A-297517-1646021150.pcap.gz
        # frames 771
        "query": {
            "lower": [122],
            "coap": [59],
            "dns": [42],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-None-None-50x5.0-A-297517-1646021150.pcap.gz
        # frames 791, 792
        "response_a": {
            "lower": [123, 38],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 12],
            "dns": [58 - 12, 12],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645878469.pcap.gz
        # frames 831, 832
        "response_aaaa": {
            "lower": [123, 50],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 24],
            "dns": [70 - 24, 24],
        },
    },
    "coaps": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 537, 538
        "dtls_client_hello": {
            "lower": [123, 43],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 17],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 541
        "dtls_hello_verify_req": {
            "lower": [107],
            "dtls": [44],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 559, 560
        "dtls_client_hello+cookie": {
            "lower": [123, 59],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 33],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 570, 572
        "dtls_server_hello": {
            "lower": [123, 33],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 7],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 608
        "dtls_server_hello_done": {
            "lower": [88],
            "dtls": [25],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 680
        "dtls_client_key_exc": {
            "lower": [105],
            "dtls": [42],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 911
        "dtls_change_cipher_spec": {
            "lower": [77],
            "dtls": [14],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 933
        "dtls_finish": {
            "lower": [116],
            "dtls": [53],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 1148, 1149
        "query": {
            "lower": [123, 58],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 32],
            "coap": [59 - 32, 32],
            "dns": [42 - 32, 32],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 1177, 1179
        "response_a": {
            "lower": [123, 67],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 41],
            "coap": [68 - 41, 41],
            "dns": [58 - 41, 41],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645908349.pcap.gz
        # frames 3127, 3128
        "response_aaaa": {
            "lower": [123, 79],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 53],
            "coap": [80 - 53, 53],
            "dns": [70 - 53, 53],
        },
    },
    "oscore": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 582, querying example.org, taking 748, 749 as template for
        # XXXXX.id.exp.example.org
        "oscore_query_w_echo": {
            "lower": [123, 53],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 27],
            "oscore": [72 - 27, 27],
            "coap_inner": [64 - 27, 27],
            "dns": [42 - 27, 27],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 588
        "oscore_unauth_response": {
            "lower": [93],
            "coap": [30],
            "oscore": [19],
            "coap_inner": [11],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 979, 980
        "query": {
            "lower": [123, 43],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 17],
            "oscore": [62 - 17, 17],
            "coap_inner": [54 - 17, 17],
            "dns": [42 - 17, 17],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 988, 989
        "response_a": {
            "lower": [123, 49],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 23],
            "oscore": [71 - 23, 23],
            "coap_inner": [63 - 23, 23],
            "dns": [58 - 23, 23],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645863307.pcap.gz
        # frames 1215, 1217
        "response_aaaa": {
            "lower": [123, 61],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 35],
            "oscore": [91 - 35, 35],
            "coap_inner": [83 - 35, 35],
            "dns": [75 - 35, 35],
        },
    },
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
    "lower": r"802.15.4 \& 6LoWPAN",
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
MSG_TYPES = [
    "dtls_client_hello",
    "dtls_hello_verify_req",
    "dtls_client_hello+cookie",
    "dtls_server_hello",
    "dtls_server_hello_done",
    "dtls_client_key_exc",
    "dtls_change_cipher_spec",
    "dtls_finish",
    "oscore_unauth_response",
    "oscore_query_w_echo",
    "query",
    "query_fetch",
    "query_fetch_last",
    "query_get",
    "coap_2.31",
    "response_a",
    "response_a_last",
    "response_aaaa",
    "response_aaaa_last",
]
MSG_TYPES_READABLE = {
    "dtls_client_hello": "Client Hello",
    "dtls_hello_verify_req": "Hello Verify Request",
    "dtls_client_hello+cookie": "Client Hello[Cookie]",
    "dtls_server_hello": "Server Hello",
    "dtls_server_hello_done": "Server Hello Done",
    "dtls_client_key_exc": "Client Key Exchange",
    "dtls_change_cipher_spec": "Change Cipher Spec",
    "dtls_finish": "Finish",
    "oscore_query_w_echo": "Query (w/ Echo)",
    "oscore_unauth_response": "4.01 Unauthorized",
    "query": "Query",
    "query_fetch": "Query [F/P]",
    "query_fetch_last": "Query [F/P] (Last)",
    "query_get": "Query [G]",
    "response_a": "Response (A)",
    "response_a_last": "Response (A, Last)",
    "response_aaaa": "Response (AAAA)",
    "response_aaaa_last": "Response (AAAA, Last)",
    "coap_2.31": "2.31 Continue",
}
TRANSPORT_CIPHER = {
    "coaps": "AES-128-CCM-8",
    # AES128-CCM-8 ~= AES-CCM-16-64-128, but with 12 byte nonce instead of 13
    # see https://datatracker.ietf.org/doc/html/rfc6655#section-3
    # and https://datatracker.ietf.org/doc/html/rfc6655#section-4
    #   + https://datatracker.ietf.org/doc/html/rfc8152#section-10.2
    "oscore": "AES-128-CCM-8",
    "dtls": "AES-128-CCM-8",
}
TRANSPORT_CRYPTO_OFFSET = {
    "dtls": 0,
    "oscore": 48,
}
TRANSPORT_FIGURE = {
    "udp": 0,
    "dtls": 1,
    "coap": 2,
    "coaps": 3,
    "oscore": 4,
}
TRANSPORT_HANDSHAKE = {
    "dtls": "DTLSv1.2 Handshake",
    "oscore": "OSCORE\nrepeat\nwindow\ninit.",
}
FRAG_MARKER_COLOR = "#f33"


def add_legends(
    figure,
    legend_pad=0.09,
    layers=LAYERS,
    frag_label="802.15.4 max. frame size (Fragmentation)",
):
    layer_handles = [
        matplotlib.patches.Patch(**LAYERS_STYLE[layer], label=LAYERS_READABLE[layer])
        for layer in layers
        if not layer.endswith("_inner")
    ]
    layer_handles.append(
        matplotlib.lines.Line2D(
            [0], [0], color=FRAG_MARKER_COLOR, linestyle="--", label=frag_label
        )
    )
    layer_legend = figure.legend(
        handles=layer_handles,
        loc="upper center",
        ncol=len(layers) + 1,
        bbox_to_anchor=(0.5, 1.02 + legend_pad),
    )
    figure.add_artist(layer_legend)


def mark_handshake(ax, pkt_sizes, transport_cipher, left, ymax):
    for crypto in ["dtls", "oscore"]:
        if any(mtype.startswith(f"{crypto}_") for mtype in pkt_sizes):
            # needs fixing to actual plot 'i's
            crypto_msg_idx = [
                i
                for i, mtype in enumerate(
                    mtype for mtype in MSG_TYPES if mtype in pkt_sizes
                )
                if mtype.startswith(f"{crypto}_")
            ]
            ax.add_patch(
                matplotlib.patches.Rectangle(
                    (min(crypto_msg_idx) - 1, 0),
                    max(crypto_msg_idx) + 1.5,
                    ymax,
                    zorder=-1,
                    alpha=0.9,
                    color="#d9d9d9",
                ),
            )
            ax.add_line(
                matplotlib.lines.Line2D(
                    [
                        min(crypto_msg_idx) - 0.5,
                        min(crypto_msg_idx) - 0.5,
                        max(crypto_msg_idx) + 0.5,
                        max(crypto_msg_idx) + 0.5,
                    ],
                    [ymax, ymax + 8, ymax + 8, ymax],
                    color="black",
                    clip_on=False,
                ),
            )
            ax.text(
                (min(crypto_msg_idx) + max(crypto_msg_idx)) / 2,
                ymax + 10,
                "Session setup",
                horizontalalignment="center",
                verticalalignment="bottom",
                clip_on=False,
                fontsize="x-small",
            )
    return left


def plot_pkt_sizes(
    ax,
    pkt_sizes,
    msg_types_of_transport,
    fragys=None,
    layers_readable=None,
    label=None,
    transport_cipher=None,
    set_xlabels=True,
    xhorizontalalignment="right",
    xrotation=45,
    ymax=210,
):
    if layers_readable is None:
        layers_readable = LAYERS_READABLE
    for frag_idx, offset in enumerate([0] + fragys):
        bottom = numpy.array([offset for _ in msg_types_of_transport]).astype("float")
        for layer_idx, layer in enumerate(LAYERS):
            layer_pkt_sizes = []
            for msg_type in msg_types_of_transport:
                if msg_type not in pkt_sizes:
                    continue
                msg_type_sizes = pkt_sizes[msg_type]
                if layer not in msg_type_sizes:
                    layer_pkt_sizes.append(numpy.nan)
                    continue
                msg_type_layers = msg_type_sizes.keys()
                next_layers = sorted(
                    (LAYERS.index(nl), nl)
                    for nl in msg_type_layers
                    if LAYERS.index(nl) > layer_idx
                )
                if next_layers:
                    next_layer_size = msg_type_sizes[next_layers[0][1]]
                    if frag_idx < len(next_layer_size):
                        next_layer_size = next_layer_size[frag_idx]
                    else:
                        next_layer_size = 0
                else:
                    next_layer_size = 0
                frags = msg_type_sizes[layer]
                if frag_idx < len(frags):
                    layer_pkt_sizes.append(frags[frag_idx] - next_layer_size)
                else:
                    layer_pkt_sizes.append(numpy.nan)
            if not layer_pkt_sizes or numpy.isnan(layer_pkt_sizes).all():
                continue
            y = numpy.array(layer_pkt_sizes).astype("float")
            xlabels = [MSG_TYPES_READABLE[m] for m in msg_types_of_transport]
            x = numpy.arange(len(xlabels))
            ax.bar(
                x,
                y,
                bottom=bottom,
                label=layers_readable[layer],
                edgecolor="black",
                **LAYERS_STYLE[layer],
            )
            bottom += y
            bottom = numpy.nan_to_num(
                bottom, copy=True, nan=0.0, posinf=None, neginf=None
            )
            ax.set_xticks(x)
            if set_xlabels:
                ax.set_xticklabels(
                    labels=xlabels,
                    rotation=xrotation,
                    horizontalalignment=xhorizontalalignment,
                    verticalalignment="top",
                )
            else:
                ax.set_xticklabels([])
    xlim = ax.get_xlim()
    xlim = numpy.floor(xlim[0]) + 0.5, numpy.floor(xlim[1]) + 0.5
    ax.set_xlim(xlim[0], xlim[1])
    left = xlim[0]
    if transport_cipher:
        left = mark_handshake(ax, pkt_sizes, transport_cipher, left, ymax)
    ax.text(
        left + 0.1,
        ymax - 4,
        label,
        horizontalalignment="left",
        verticalalignment="top",
        fontsize="x-small",
    )
    ax.set_ylim(0, ymax)
    ax.set_yticks(numpy.arange(0, ymax + 1, 32))
    ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(8))
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", which="major")
    ax.grid(True, axis="y", which="minor", linewidth=0.25, linestyle="dashed")


def plot_pkt_sizes_for_transports(  # pylint: disable=dangerous-default-value
    axs,
    transports=pc.TRANSPORTS,
    transport_figure=TRANSPORT_FIGURE,
    transport_readable=pc.TRANSPORTS_READABLE,
    pkt_sizes=PKT_SIZES,
    fragys=None,
):
    if fragys is None:
        fragys = [127]
    for transport in transports:
        if transport not in pkt_sizes:
            continue
        pkt_sizes_of_transport = pkt_sizes[transport]
        ax = axs[transport_figure[transport]]
        msg_types_of_transport = set()
        for m in MSG_TYPES:
            if m in pkt_sizes_of_transport:
                msg_types_of_transport.add(m)
        msg_types_of_transport = sorted(
            msg_types_of_transport, key=lambda m: MSG_TYPES.index(m)
        )
        plot_pkt_sizes(
            ax,
            pkt_sizes_of_transport,
            msg_types_of_transport,
            fragys=fragys,
            transport_cipher=TRANSPORT_CIPHER.get(transport),
            label=transport_readable[transport],
        )
        for fragy in fragys:
            ax.axhline(y=fragy, color=FRAG_MARKER_COLOR, linestyle="--")
    axs[0].set_ylabel("Frame Size [bytes]")


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    matplotlib.rcParams["figure.figsize"] = (7.00137, 1.5)
    matplotlib.rcParams["legend.handletextpad"] = 0.2
    matplotlib.rcParams["legend.columnspacing"] = 0.4
    figure, axs = matplotlib.pyplot.subplots(
        1,
        len(PKT_SIZES),
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
                        for transport in PKT_SIZES
                    ]
                )
            ]
        },
    )
    plot_pkt_sizes_for_transports(axs)
    add_legends(figure)
    matplotlib.pyplot.tight_layout(w_pad=-4.7)
    matplotlib.pyplot.subplots_adjust(top=0.85, bottom=0)
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-namelen-24.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


if __name__ == "__main__":
    main()
