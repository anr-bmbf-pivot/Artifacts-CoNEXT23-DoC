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
            "ieee802154": 75 - 52,
            "6lowpan": 52 - 28,
            "dns": 28,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "ieee802154": 91 - 68,
            "6lowpan": 68 - 44,
            "dns": 44,
        },
        # doc-eval-load-udp-None-None-100x10.0-284025-1635455554.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "ieee802154": 103 - 80,
            "6lowpan": 80 - 56,
            "dns": 56,
        },
    },
    "dtls": {
        # doc-eval-load-dtls-None-None-100x10.0-A-284631-1636050098.pcap.gz
        "dtls_client_hello": {
            "ieee802154": 121 - 98,
            "6lowpan": 98 - 73,
            "dtls": 73,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_hello_verify_req": {
            "ieee802154": 92 - 69,
            "6lowpan": 69 - 44,
            "dtls": 44,
        },
        "dtls_client_hello+cookie": {
            "ieee802154": (124 - 101) + (45 - 22),
            "ieee802154_frag": (124 - 101),
            "6lowpan": (101 - (120 - 40 - 8)) + (22 - 17),
            "6lowpan_frag": (101 - (120 - 40 - 8)),
            "dtls": 89,
            "dtls_frag": (120 - 40 - 8),
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello": {
            "ieee802154": 111 - 88,
            "6lowpan": 88 - 63,
            "dtls": 63,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello_done": {
            "ieee802154": 73 - 50,
            "6lowpan": 50 - 25,
            "dtls": 25,
        },
        "dtls_client_key_exc": {
            "ieee802154": 90 - 67,
            "6lowpan": 67 - 42,
            "dtls": 42,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_change_cipher_spec": {
            "ieee802154": 62 - 39,
            "6lowpan": 39 - 14,
            "dtls": 14,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_finish": {
            "ieee802154": 101 - 78,
            "6lowpan": 78 - 53,
            "dtls": 53,
        },
        "query": {
            "ieee802154": 105 - 82,
            "6lowpan": 82 - 57,
            "dtls": 57,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "ieee802154": 121 - 98,
            "6lowpan": 98 - 73,
            "dtls": 73,
        },
        # doc-eval-load-dtls-None-None-100x10.0-284025-1635451309.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "ieee802154": (116 - 93) + (49 - 26),
            "ieee802154_frag": (116 - 93),
            "6lowpan": (93 - (112 - 40 - 8)) + (26 - 21),
            "6lowpan_frag": (93 - (112 - 40 - 8)),
            "dtls": 85,
            # + 8 since due to stripping there is more place in the fragment
            "dtls_frag": (120 - 40 - 8),
        },
    },
    "coap": {
        # doc-eval-load-coap-None-None-100x10.0-A-284640-1636101104.pcap.gz
        "query": {
            "ieee802154": 99 - 76,
            "6lowpan": 76 - 51,
            "coap": 51 - 28,
            "dns": 28,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "ieee802154": 102 - 79,
            "6lowpan": 79 - 54,
            "coap": 54 - 44,
            "dns": 44,
        },
        # doc-eval-load-coap-1.0-25-100x5.0-284361-1635777176.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "ieee802154": 114 - 91,
            "6lowpan": 91 - 66,
            "coap": 66 - 56,
            "dns": 56,
        },
    },
    "coaps": {
        # doc-eval-load-coaps-None-None-100x10.0-A-284623-1636045983.pcap.gz
        "dtls_client_hello": {
            "ieee802154": 121 - 98,
            "6lowpan": 98 - 73,
            "dtls": 73,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_hello_verify_req": {
            "ieee802154": 92 - 69,
            "6lowpan": 69 - 44,
            "dtls": 44,
        },
        "dtls_client_hello+cookie": {
            "ieee802154": (124 - 101) + (45 - 22),
            "ieee802154_frag": (124 - 101),
            "6lowpan": (101 - (120 - 40 - 8)) + (22 - 17),
            "6lowpan_frag": (101 - (120 - 40 - 8)),
            "dtls": 89,
            "dtls_frag": (120 - 40 - 8),
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello": {
            "ieee802154": 111 - 88,
            "6lowpan": 88 - 63,
            "dtls": 63,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_server_hello_done": {
            "ieee802154": 73 - 50,
            "6lowpan": 50 - 25,
            "dtls": 25,
        },
        "dtls_client_key_exc": {
            "ieee802154": 90 - 67,
            "6lowpan": 67 - 42,
            "dtls": 42,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_change_cipher_spec": {
            "ieee802154": 62 - 39,
            "6lowpan": 39 - 14,
            "dtls": 14,
        },
        # From server;
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "dtls_finish": {
            "ieee802154": 101 - 78,
            "6lowpan": 78 - 53,
            "dtls": 53,
        },
        "query": {
            "ieee802154": (124 - 101) + (35 - 12),
            "ieee802154_frag": (124 - 101),
            "6lowpan": (101 - (120 - 40 - 8)) + (12 - 7),
            "6lowpan_frag": (101 - (120 - 40 - 8)),
            "dtls": 79,
            "dtls_frag": (120 - 40 - 8),
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "ieee802154": (116 - 93) + (35 - 12),
            "ieee802154_frag": (116 - 93),
            "6lowpan": (93 - (112 - 40 - 8)) + (23 - 18),
            "6lowpan_frag": (93 - (112 - 40 - 8)),
            "dtls": 82,
            # + 8 since due to stripping there is more place in the fragment
            "dtls_frag": (120 - 40 - 8),
        },
        # doc-eval-load-coaps-None-None-100x10.0-283970-1635353886.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "ieee802154": (116 - 93) + (58 - 35),
            "ieee802154_frag": (116 - 93),
            "6lowpan": (93 - (112 - 40 - 8)) + (35 - 30),
            "6lowpan_frag": (93 - (112 - 40 - 8)),
            "dtls": 94,
            # + 8 since due to stripping there is more place in the fragment
            "dtls_frag": (120 - 40 - 8),
        },
    },
    "oscore": {
        # doc-eval-load-oscore-None-None-100x10.0-A-284623-1636046886.pcap.gz
        "oscore_query_wo_echo": {
            "ieee802154": 113 - 90,
            "6lowpan": 90 - 65,
            "coap": 65 - 54,
            "oscore": 54,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "oscore_unauth_response": {
            "ieee802154": 77 - 54,
            "6lowpan": 54 - 29,
            "coap": 29 - 19,
            "oscore": 19,
        },
        "query": {  # query with echo option
            "ieee802154": 123 - 100,
            "6lowpan": 100 - 75,
            "coap": 75 - 64,
            "oscore": 64,
        },
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_a": {
            "ieee802154": 115 - 92,
            "6lowpan": 92 - 67,
            "coap": 67 - 57,
            "oscore": 57,
        },
        # doc-eval-load-coap-1.0-25-100x5.0-284361-1635777176.pcap.gz
        # Stripped inline flow-label and hop limit since not relevant to allow for
        # better comparability
        "response_aaaa": {
            "ieee802154": (116 - 93) + (41 - 15),
            "ieee802154_frag": (116 - 93),
            "6lowpan": (93 - (112 - 40 - 8)) + (15 - 13),
            "6lowpan_frag": (93 - (112 - 40 - 8)),
            "coap": 79 - 69,
            "oscore": 69,
            # + 8 since due to stripping there is more place in the fragment
            "oscore_frag": (120 - 40 - 8) - (79 - 69),
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
    "response_a": "Response (A)",
    "response_aaaa": "Response (AAAA)",
}
LAYERS = [
    "ieee802154",
    "6lowpan",
    "dtls",
    "coap",
    "oscore",
    "dns",
]
LAYERS_READABLE = {
    "ieee802154": "IEEE 802.15.4",
    "6lowpan": "6LoWPAN + NHC",
    "dns": "DNS",
    "dtls": "DTLS",
    "coap": "CoAP",
    "oscore": "OSCORE",
}
LAYERS_STYLE = {
    "ieee802154": {"color": "C0"},
    "6lowpan": {"color": "C1"},
    "dns": {"color": "C2"},
    "dtls": {"color": "C3"},
    "coap": {"color": "C4"},
    "oscore": {"color": "C5"},
}
TRANSPORT_CIPHER = {
    "coap": "",
    "coaps": "AES128-CCM-8",
    # TODO: determine if AES128-CCM-8 == AES-CCM-16-64-128,
    "oscore": "AES-CCM-16-64-128",
    # see https://datatracker.ietf.org/doc/html/rfc8152#section-10.2
    "dtls": "AES128-CCM-8",
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
FRAG_MARKER_COLOR = "C6"


def plot_pkt_frags(ax, bar_plot, transport, layer):
    frags = numpy.array(
        [
            PKT_SIZES[transport].get(m, {}).get(f"{layer}_frag", 0)
            if PKT_SIZES[transport].get(m, {}).get(f"{layer}_frag", 0) > 0
            else numpy.nan
            for m in MESSAGE_TYPES
            if PKT_SIZES[transport].get(m, {}).get(layer, 0) > 0
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


def mark_handshake(ax, transport, left, ymax):
    print_cipher = True
    for crypto in ["dtls", "oscore"]:
        if any(mtype.startswith(f"{crypto}_") for mtype in PKT_SIZES[transport]):
            # needs fixing to actual plot 'i's
            crypto_msg_idx = [
                i
                for i, mtype in enumerate(
                    mtype for mtype in MESSAGE_TYPES if mtype in PKT_SIZES[transport]
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
                max(crypto_msg_idx) + 0.4,
                ymax - 4,
                TRANSPORT_HANDSHAKE[crypto][0],
                horizontalalignment="right",
                verticalalignment="top",
            )
            if TRANSPORT_HANDSHAKE[crypto][1]:
                print_cipher = False
                ax.text(
                    max(crypto_msg_idx) + 0.4,
                    ymax - 18,
                    f"({TRANSPORT_CIPHER[transport]})",
                    fontsize=8,
                    horizontalalignment="right",
                    verticalalignment="top",
                )
    return print_cipher, left


def main():  # pylint: disable=too-many-local-variables
    figure, axs = matplotlib.pyplot.subplots(
        1,
        len(pc.TRANSPORTS),
        figsize=(16, 2.5),
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
    ymax = 192
    fragy = 127
    for transport in pc.TRANSPORTS:
        if transport not in PKT_SIZES:
            continue
        idx = TRANSPORT_FIGURE[transport]
        axs[idx].axhline(y=fragy, color=FRAG_MARKER_COLOR, linestyle="--")
        prev_layer = None
        for layer in LAYERS:
            y = numpy.array(
                [
                    PKT_SIZES[transport].get(m, {}).get(layer, 0)
                    for m in MESSAGE_TYPES
                    if PKT_SIZES[transport].get(m, {}).get(layer, 0) > 0
                ]
            )
            if not y.any():
                continue
            xlabels = [
                MESSAGE_TYPES_READABLE[m]
                for m in MESSAGE_TYPES
                if PKT_SIZES[transport].get(m, {}).get(layer, 0) > 0
            ]
            x = numpy.arange(len(xlabels))
            res = axs[idx].bar(
                x,
                y,
                bottom=prev_layer
                if prev_layer is not None
                else [0 for _ in PKT_SIZES[transport]],
                label=LAYERS_READABLE[layer],
                linewidth=1,
                edgecolor="black",
                **LAYERS_STYLE[layer],
            )
            plot_pkt_frags(axs[idx], res, transport, layer)
            if prev_layer is None:
                prev_layer = y
            else:
                prev_layer += y
            axs[idx].set_xticks(x)
            axs[idx].set_xticklabels(
                labels=xlabels,
                rotation=45,
                horizontalalignment="right",
                position=(0, 0.01),
            )
        xlim = axs[idx].get_xlim()
        left = xlim[0]
        right = xlim[1]
        print_cipher, left = mark_handshake(axs[idx], transport, left, ymax)
        axs[idx].text(
            0.5 * (right - left) + left,
            ymax - 4,
            pc.TRANSPORTS_READABLE[transport],
            horizontalalignment="center",
            verticalalignment="top",
        )
        if print_cipher and TRANSPORT_CIPHER[transport]:
            axs[idx].text(
                0.5 * (right - left) + left,
                ymax - 18,
                f"({TRANSPORT_CIPHER[transport]})",
                fontsize=8,
                horizontalalignment="center",
                verticalalignment="top",
            )
    xlim = axs[0].get_xlim()
    axs[0].text(xlim[0] + 0.02, fragy + 1.2, "Fragmentation", color=FRAG_MARKER_COLOR)
    axs[0].set_ylabel("PDU [bytes]")
    matplotlib.pyplot.ylim(0, ymax)
    matplotlib.pyplot.yticks(numpy.arange(0, ymax + 1, 16))
    handles = [
        matplotlib.patches.Patch(**LAYERS_STYLE[layer], label=LAYERS_READABLE[layer])
        for layer in LAYERS
    ]
    figure.legend(handles=handles, loc="upper center", ncol=len(LAYERS))
    matplotlib.pyplot.tight_layout(w_pad=-4)
    matplotlib.pyplot.subplots_adjust(top=0.85, bottom=0)
    for ext in ["pgf", "svg"]:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-namelen-10.{ext}",
            ),
            bbox_inches="tight",
        )


if __name__ == "__main__":
    main()
