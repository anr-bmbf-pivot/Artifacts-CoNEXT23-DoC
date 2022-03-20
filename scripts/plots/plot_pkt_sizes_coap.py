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

try:
    from . import plot_common as pc
    from . import plot_pkt_sizes as pkt_sizes
except ImportError:
    import plot_common as pc
    import plot_pkt_sizes as pkt_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


PKT_SIZES = {
    "coap": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-None-None-50x5.0-A-297517-1646021150.pcap.gz
        # frames 771
        "query_fetch": {
            "lower": [122],
            "coap": [59],
            "dns": [42],
        },
        # doc-eval-proxy-ieee802154-coap-get-proxied0-None-None-50x5.0-A-297517-1645923710.pcap.gz
        # frames 785, 786
        "query_get": {
            "lower": [123, 45],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 19],
            # -4 for `dns=`
            "dns": [(60 - 4) - 19, 19],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-None-None-50x5.0-A-297517-1646021150.pcap.gz
        # frames 791, 792
        "response_a": {
            "lower": [123, 38],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 12],
            "dns": [58 - 12, 12],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645878469.pcap.gz
        # frames 831, 832
        "response_aaaa": {
            "lower": [123, 50],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 24],
            "dns": [70 - 24, 24],
        },
    },
    "coap16": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-A-297517-1646047198.pcap.gz
        # frames 931 (Block #0), 948 (Block #1)
        "query_fetch": {
            "lower": [102],
            "coap": [39],
            "dns": [16],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-A-297517-1646047198.pcap.gz
        # frames 951
        "coap_2.31": {
            "lower": [72],
            "coap": [9],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-A-297517-1646047198.pcap.gz
        # frames 987 (Block #2)
        "query_fetch_last": {
            "lower": [97],
            "coap": [34],
            "dns": [10],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-get-proxied0-None-None-50x5.0-A-297517-1645923710.pcap.gz
        # frames 785, 786
        "query_get": {
            "lower": [123, 45],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 19],
            # -4 for `dns=`
            "dns": [(60 - 4) - 19, 19],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-A-297517-1646047198.pcap.gz
        # frames 999 (Block #0), Block #1 and #2 are coap 28, since Block1 option not
        # present
        "response_a": {
            "lower": [93],
            "coap": [30],
            "dns": [16],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-A-297517-1646047198.pcap.gz
        # frames 1289 (Block #3)
        "response_a_last": {
            "lower": [85],
            "coap": [22],
            "dns": [10],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-AAAA-297517-1646046287.pcap.gz
        # frames 983 (Block #0), Block #1, #2, and #3 are coap 28, since Block1 option
        # not present
        "response_aaaa": {
            "lower": [93],
            "coap": [30],
            "dns": [16],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-AAAA-297517-1646046287.pcap.gz
        # frames 1290 (Block #4)
        # not present
        "response_aaaa_last": {
            "lower": [81],
            "coap": [18],
            "dns": [6],
        },
    },
    "coap32": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b32-None-None-50x5.0-A-297517-1645979747.pcap.gz
        # frames 851 (Block #0)
        "query_fetch": {
            "lower": [118],
            "coap": [55],
            "dns": [32],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b16-None-None-50x5.0-A-297517-1646047198.pcap.gz
        # frames 951
        "coap_2.31": {
            "lower": [72],
            "coap": [9],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b32-None-None-50x5.0-A-297517-1645979747.pcap.gz
        # frames 871 (Block #1)
        "query_fetch_last": {
            "lower": [98],
            "coap": [35],
            "dns": [10],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-get-proxied0-None-None-50x5.0-A-297517-1645923710.pcap.gz
        # frames 785, 786
        "query_get": {
            "lower": [123, 45],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 19],
            # -4 for `dns=`
            "dns": [(60 - 4) - 19, 19],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b32-None-None-50x5.0-A-297517-1645979747.pcap.gz
        # frames 925 (Block #0)
        # present
        "response_a": {
            "lower": [109],
            "coap": [46],
            "dns": [32],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b32-None-None-50x5.0-A-297517-1645979747.pcap.gz
        # frames 943 (Block #1)
        "response_a_last": {
            "lower": [101],
            "coap": [38],
            "dns": [26],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b32-None-None-50x5.0-AAAA-297517-1646025747.pcap.gz
        # frames 940 (Block #0), Block #1 is coap 44, since Block1 option not present
        "response_aaaa": {
            "lower": [109],
            "coap": [46],
            "dns": [32],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b32-None-None-50x5.0-AAAA-297517-1646025747.pcap.gz
        # frames 1290 (Block #2)
        # not present
        "response_aaaa_last": {
            "lower": [81],
            "coap": [18],
            "dns": [6],
        },
    },
    "coap64": {
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b64-None-None-50x5.0-AAAA-297517-1645951264.pcap.gz
        # frames 765, 766 (Block #0)
        "query_fetch": {
            "lower": [123, 36],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 10],
            "dns": [42 - 10, 10],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b64-None-None-50x5.0-AAAA-297517-1645951264.pcap.gz
        # frames 951
        "coap_2.31": {
            "lower": [72],
            "coap": [9],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-get-proxied0-None-None-50x5.0-A-297517-1645923710.pcap.gz
        # frames 785, 786
        "query_get": {
            "lower": [123, 45],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 19],
            # -4 for `dns=`
            "dns": [(60 - 4) - 19, 19],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b64-None-None-50x5.0-AAAA-297517-1645951264.pcap.gz
        # frames 1473 (Block #0)
        "response_aaaa": {
            "lower": [123, 46],
            "coap": [104 - pkt_sizes.IPHC_NHC_COMP_HDTSZ, 20],
            "dns": [64 - 20, 20],
        },
        # pylint: disable=line-too-long
        # doc-eval-proxy-ieee802154-coap-fetch-proxied0-b64-None-None-50x5.0-AAAA-297517-1645951264.pcap.gz
        # frames 1290 (Block #1)
        # not present
        "response_aaaa_last": {
            "lower": [81],
            "coap": [18],
            "dns": [6],
        },
    },
}
TRANSPORT_FIGURE = {
    "coap": 0,
    "coap16": 1,
    "coap32": 2,
    "coap64": 3,
}
TRANSPORTS_READABLE = {
    "coap": "CoAP\n(No blockwise)",
    "coap16": "CoAP (Blocksize: 16 bytes)",
    "coap32": "CoAP (Blocksize: 32 bytes)",
    "coap64": "CoAP\n(Blocksize: 64 bytes)",
}


def main():  # pylint: disable=too-many-local-variables
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    matplotlib.rcParams["figure.figsize"] = (7.00137, 1.5)
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
    pkt_sizes.plot_pkt_sizes_for_transports(
        axs,
        transports=[k for _, k in sorted((v, k) for k, v in TRANSPORT_FIGURE.items())],
        transport_figure=TRANSPORT_FIGURE,
        transport_readable=TRANSPORTS_READABLE,
        pkt_sizes=PKT_SIZES,
    )
    pkt_sizes.add_legends(figure, layers=["lower", "coap", "dns"], legend_pad=0)
    matplotlib.pyplot.tight_layout(w_pad=-3.1)
    matplotlib.pyplot.subplots_adjust(top=0.85, bottom=0)
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-namelen-24-coap.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


if __name__ == "__main__":
    main()
