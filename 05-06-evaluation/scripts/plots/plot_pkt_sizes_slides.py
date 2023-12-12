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

import matplotlib.lines
import matplotlib.patches
import matplotlib.pyplot

try:
    from . import plot_common as pc
    from . import plot_pkt_sizes as pkt_sizes
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_pkt_sizes as pkt_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

PKT_SIZES = {
    "udp": {
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-udp-proxied0-None-None-50x5.0-AAAA-297517-1646043265.pcap.gz
        # frames 498
        "query_fetch": {
            "lower": [104],
            "dns": [42],
        },
        "query_get": {},
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-udp-proxied0-None-None-50x5.0-A-297517-1646020465.pcap.gz
        # frames 622
        "response_a": {
            "lower": [122],
            "dns": [58],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-udp-proxied0-None-None-50x5.0-AAAA-297517-1646043265.pcap.gz
        # frames 506, 507
        "response_aaaa": {
            "lower": [123, 40],
            "dns": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 14],
        },
    },
    "dtls": {
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 1398, 1399
        "query_fetch": {
            "lower": [123, 41],
            "dtls": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 15],
            "dns": [42 - 15, 15],
        },
        "query_get": {},
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 1537, 1538
        "response_a": {
            "lower": [123, 57],
            "dtls": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 31],
            "dns": [58 - 31, 31],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-dtls-proxied0-None-None-50x5.0-AAAA-297517-1645996717.pcap.gz
        # frames 2842, 2843
        "response_aaaa": {
            "lower": [123, 69],
            "dtls": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 43],
            "dns": [70 - 43, 43],
        },
    },
    "coap": {
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-coap-fetch-proxied0-None-None-50x5.0-A-297517-1646021150.pcap.gz
        # frames 771
        "query_fetch": {
            "lower": [122],
            "coap": [59],
            "dns": [42],
        },
        # doc-eval-comp-ieee802154-coap-get-proxied0-None-None-50x5.0-A-297517-1645923710.pcap.gz
        # frames 785, 786
        "query_get": {
            "lower": [123, 45],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 19],
            # -4 for `dns=`
            "dns": [(60 - 4) - 19, 19],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-coap-fetch-proxied0-None-None-50x5.0-A-297517-1646021150.pcap.gz
        # frames 791, 792
        "response_a": {
            "lower": [123, 38],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 12],
            "dns": [58 - 12, 12],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-coap-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645878469.pcap.gz
        # frames 831, 832
        "response_aaaa": {
            "lower": [123, 50],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 24],
            "dns": [70 - 24, 24],
        },
    },
    "coaps": {
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 1148, 1149
        "query_fetch": {
            "lower": [123, 58],
            "dtls": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 32],
            "coap": [59 - 32, 32],
            "dns": [42 - 32, 32],
        },
        # doc-eval-comp-ieee802154-coaps-get-proxied0-None-None-50x5.0-A-297517-1645930395.pcap.gz
        # frames 841, 842
        "query_get": {
            "lower": [123, 74],
            "dtls": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 48],
            "coap": [75 - 48, 48],
            # -4 for `dns=`
            "dns": [(60 - 4) - 48, 48],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-A-297517-1645856753.pcap.gz
        # frames 1177, 1179
        "response_a": {
            "lower": [123, 67],
            "dtls": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 41],
            "coap": [68 - 41, 41],
            "dns": [58 - 41, 41],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-coaps-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645908349.pcap.gz
        # frames 3127, 3128
        "response_aaaa": {
            "lower": [123, 79],
            "dtls": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 53],
            "coap": [80 - 53, 53],
            "dns": [70 - 53, 53],
        },
    },
    "oscore": {
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 979, 980
        "query_fetch": {
            "lower": [123, 43],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 17],
            "oscore": [62 - 17, 17],
            "coap_inner": [54 - 17, 17],
            "dns": [42 - 17, 17],
        },
        "query_get": {},
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 988, 989
        "response_a": {
            "lower": [123, 49],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 23],
            "oscore": [71 - 23, 23],
            "coap_inner": [63 - 23, 23],
            "dns": [58 - 23, 23],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645863307.pcap.gz
        # frames 1215, 1217
        "response_aaaa": {
            "lower": [123, 61],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 35],
            "oscore": [83 - 35, 35],
            "coap_inner": [75 - 35, 35],
            "dns": [70 - 35, 35],
        },
    },
}
TRANSPORT_FIGURE = {
    "udp": 0,
    "dtls": 1,
    "coap": 2,
    "coaps": 3,
    "oscore": 4,
}
TRANSPORTS_READABLE = {
    "coap": "CoAP\n(No blockwise)",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    pkt_sizes.FRAG_MARKER_STYLE.update({"linewidth": 1.5})
    pkt_sizes.PLOT_LAYERS = False
    matplotlib.rcParams["figure.figsize"] = (3.3, 5.9)
    figure, axs = matplotlib.pyplot.subplots(
        len(TRANSPORT_FIGURE),
        1,
        sharex=True,
    )
    pkt_sizes.plot_pkt_sizes_for_transports(
        axs,
        transports=pc.TRANSPORTS,
        transport_figure=TRANSPORT_FIGURE,
        pkt_sizes=PKT_SIZES,
        set_xlabels=False,
    )
    xlabels = ["Query [F/P]", "Query [G]", "Resp. (A)", "Resp. (AAAA)"]
    axs[max(TRANSPORT_FIGURE.values())].set_xticks(
        range(len(xlabels)),
        labels=xlabels,
        horizontalalignment="center",
    )
    for i in range(len(pc.TRANSPORTS)):
        axs[i].set_ylabel("Frame Size [bytes]")
    pkt_sizes.add_legends(
        figure,
        ncol=2,
        legend_pad=-0.12,
        frag_label="L2 max. frame size",
    )
    matplotlib.pyplot.tight_layout(h_pad=0.1)
    matplotlib.pyplot.subplots_adjust(top=0.85, bottom=0)
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-namelen-24-slides.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


if __name__ == "__main__":
    main()  # pragma: no cover
