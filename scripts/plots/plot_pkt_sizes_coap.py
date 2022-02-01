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
        # doc-eval-load-ieee802154-coap-fetch-None-None-100x5.0-A-289166-1639486177.pcap.gz
        "query_fetch": {
            "lower": 99 - 51,
            "lower_var": 32,
            "coap": 51 - 28,
            "coap_var": 18,
            "dns": 28,
            "dns_var": 10,
        },
        # doc-eval-load-ieee802154-coap-get-None-None-100x10.0-A-291129-1641555577.pcap.gz
        "query_get": {
            "lower": 99 - 51,
            "lower_var": 32,
            "coap": 63 - 38,
            "coap_var": 17,
            "dns": 38,
            "dns_var": 14,
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
    "coap16": {
        # doc-eval-load-ieee802154-coap-fetch-b16-None-None-100x5.0-A-290957-1641394073.pcap.gz
        "query_fetch": {
            "lower": 99 - 51,
            "lower_var": 32,
            "coap": 45 - 16,
            "coap_var": 21,
            "dns": 16,
            "dns_var": 16,
        },
        # doc-eval-load-ieee802154-coap-get-None-None-100x10.0-A-291129-1641555577.pcap.gz
        "query_get": {
            "lower": 99 - 51,
            "lower_var": 32,
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
            "lower_var": 32,
            "coap": 9,
            "coap_var": 2,
        },
        # doc-eval-load-ieee802154-coap-fetch-b16-None-None-100x5.0-A-290957-1641394073.pcap.gz
        "response_a": {
            "lower": 102 - 54,
            "lower_var": 32,
            "coap": 30 - 16,
            "coap_var": 7,
            "dns": 16,
            "dns_var": 8,
        },
        # doc-eval-load-ieee802154-coap-fetch-b16-None-None-100x5.0-A-290957-1641394073.pcap.gz
        "response_aaaa": {
            "lower": 102 - 54,
            "lower_var": 32,
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
            "lower_var": 32,
            "coap": 58 - 28,
            "coap_var": 21,
            "dns": 28,
            "dns_var": 28,
        },
        # doc-eval-load-ieee802154-coap-get-None-None-100x10.0-A-291129-1641555577.pcap.gz
        "query_get": {
            "lower": 99 - 51,
            "lower_var": 32,
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
            "lower_var": 32,
            "coap": 9,
            "coap_var": 2,
        },
        # doc-eval-load-ieee802154-coap-fetch-b32-None-None-100x5.0-A-290911-1641382075.pcap.gz
        "response_a": {
            "lower": 102 - 54,
            "lower_var": 32,
            "coap": 44 - 32,
            "coap_var": 5,
            "dns": 32,
            "dns_var": 24,
        },
        # doc-eval-load-ieee802154-coap-fetch-b32-None-None-100x5.0-A-290911-1641382075.pcap.gz
        "response_aaaa": {
            "lower": 102 - 54,
            "lower_var": 32,
            "coap": 44 - 32,
            "coap_var": 5,
            "dns": 32,
            "dns_var": 24,
        },
    },
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
        axs[idx].axhline(y=fragy, color=pkt_sizes.FRAG_MARKER_COLOR, linestyle="--")
        mtypes_of_transport = set()
        for layer in pkt_sizes.LAYERS:
            for m in pkt_sizes.MESSAGE_TYPES:
                if m in PKT_SIZES[transport]:
                    mtypes_of_transport.add(m)
        mtypes_of_transport = sorted(
            mtypes_of_transport, key=lambda m: pkt_sizes.MESSAGE_TYPES.index(m)
        )
        pkt_sizes.plot_pkt_sizes(
            axs[idx],
            PKT_SIZES[transport],
            mtypes_of_transport,
            ymax,
            label=TRANSPORTS_READABLE[transport],
        )
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
