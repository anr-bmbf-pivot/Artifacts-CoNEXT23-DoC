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
import os

import matplotlib
import matplotlib.pyplot
import matplotlib.style
import matplotlib.ticker

try:
    from . import plot_common as pc
    from . import plot_pkt_sizes
except ImportError:  # pragma: no cover
    import plot_common as pc
    import plot_pkt_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

IPHC_NHC_COMP_HDTSZ = 40 + 8

PKT_SIZES = {
    "dtls": {
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 1398, 1399
        "query": {
            "lower": [123, 41],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 15],
            "dns": [42 - 15, 15],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-dtls-proxied0-None-None-50x5.0-A-297517-1645847954.pcap.gz
        # frames 1537, 1538
        "response_a": {
            "lower": [123, 57],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 31],
            "dns": [58 - 31, 31],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-dtls-proxied0-None-None-50x5.0-AAAA-297517-1645996717.pcap.gz
        # frames 2842, 2843
        "response_aaaa": {
            "lower": [123, 69],
            "dtls": [104 - IPHC_NHC_COMP_HDTSZ, 43],
            "dns": [70 - 43, 43],
        },
    },
    "oscore": {
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 979, 980
        "query": {
            "lower": [123, 43],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 17],
            "oscore": [62 - 17, 17],
            "coap_inner": [54 - 17, 17],
            "dns": [42 - 17, 17],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-A-297517-1645988817.pcap.gz
        # frames 988, 989
        "response_a": {
            "lower": [123, 49],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 23],
            "oscore": [71 - 23, 23],
            "coap_inner": [63 - 23, 23],
            "dns": [58 - 23, 23],
        },
        # pylint: disable=line-too-long
        # doc-eval-comp-ieee802154-oscore-fetch-proxied0-None-None-50x5.0-AAAA-297517-1645863307.pcap.gz
        # frames 1215, 1217
        "response_aaaa": {
            "lower": [123, 61],
            "coap": [104 - IPHC_NHC_COMP_HDTSZ, 35],
            "oscore": [83 - 35, 35],
            "coap_inner": [75 - 35, 35],
            "dns": [70 - 35, 35],
        },
    },
    # QUIC long header
    #  - Destination connection ID length = 0,
    #  - Source connection ID length = 0,
    #  - Packet Number length = 1
    #  - Stream ID = 1
    "quicl_best": {
        "query": {
            "lower": [123, 43],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 0)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 0)
            # + 1..8 (Length) (assuming 2 for value 64)
            # + 1..4 (Packet Number) (assuming 1 for value 00)
            # STREAM FRAME HEADER (63 bytes)
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 1 for value 00)
            # + 0 (Offset = 0)
            # + 1 (Length) (assuming 1 for value 60)
            # + 44 Stream Data
            # + 16 128-bit authentication tag
            # = _73_
            # => 73 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 73 - (104 - IPHC_NHC_COMP_HDTSZ) = 17
            #    17 + 26 = 43
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 17],
            # DNS query length from other protocols (42) + 2 byte length
            "dns": [42 + 2 - 17, 17],
        },
        "response_a": {
            "lower": [123, 63],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 0)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 0)
            # + 1..8 (Length) (assuming 2 for value 86)
            # + 1..4 (Packet Number) (assuming 1 for value 00)
            # FRAMES (85 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 1 for value 00)
            # + 1..8 (ACK Delay) (assuming 1)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 1 for value 00)
            # + 0 (Offset = 0)
            # + 2 (Length) (assuming 2 for value 76)
            # + 60 Stream Data
            # + 16 128-bit authentication tag
            # = _95_
            # => 95 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 95 - (104 - IPHC_NHC_COMP_HDTSZ) = 37
            #    37 + 26 = 63
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 37],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [58 + 2 - 37, 37],
        },
        "response_aaaa": {
            "lower": [123, 75],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 0)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 0)
            # + 1..8 (Length) (assuming 2 for value 86)
            # + 1..4 (Packet Number) (assuming 1 for value 00)
            # FRAMES (85 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 1 for value 00)
            # + 1..8 (ACK Delay) (assuming 1)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 1 for value 00)
            # + 0 (Offset = 0)
            # + 2 (Length) (assuming 2 for value 76)
            # + 72 Stream Data
            # + 16 128-bit authentication tag
            # = _107_
            # => 107 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 107 - (104 - IPHC_NHC_COMP_HDTSZ) = 49
            #    49 + 26 = 75
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 49],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [70 + 2 - 49, 49],
        },
    },
    # QUIC long header
    #  - Destination connection ID length = 20,
    #  - Source connection ID length = 20,
    #  - Packet Number length = 4
    #  - Stream ID = 8
    "quicl_worst": {
        "query": {
            "lower": [123, 94],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 20)
            # + 1..8 (Length) (assuming 2 for value 75)
            # + 1..4 (Packet Number) (assuming 4)
            # STREAM FRAME HEADER (71 bytes)
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 8)
            # + 1 (Offset, assuming 1 for value 00)
            # + 1 (Length) (assuming 1 for value 60)
            # + 44 Stream Data
            # + 16 128-bit authentication tag
            # = _124_
            # => 124 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 124 - (104 - IPHC_NHC_COMP_HDTSZ) = 68
            #    68 + 26 = 94
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 68],
            # DNS query length from other protocols (42) + 2 byte length
            "dns": [0, 42 + 2],
        },
        "response_a": {
            "lower": [123, 118],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 20)
            # + 1..8 (Length) (assuming 2 for value 101)
            # + 1..4 (Packet Number) (assuming 4)
            # FRAMES (97 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 4)
            # + 1..8 (ACK Delay) (assuming 2)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 8)
            # + 1 (Offset, assuming 1 for value 00)
            # + 2 (Length) (assuming 2 for value 76)
            # + 60 Stream Data
            # + 16 128-bit authentication tag
            # = _150_
            # => 150 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 150 - (104 - IPHC_NHC_COMP_HDTSZ) = 92
            #    92 + 26 = 118
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 92],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [0, 58 + 2],
        },
        "response_aaaa": {
            "lower": [123, 122, 34],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 20)
            # + 1..8 (Length) (assuming 2 for value 113)
            # + 1..4 (Packet Number) (assuming 4)
            # FRAMES (109 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 4)
            # + 1..8 (ACK Delay) (assuming 2)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 8)
            # + 1 (Offset, assuming 1 for value 00)
            # + 2 (Length) (assuming 2 for value 88)
            # + 72 Stream Data
            # + 16 128-bit authentication tag
            # = _162_
            # => 162 bytes + 62 bytes > 2 * 127 bytes => 3 fragments
            # => 2nd fragment size = 162 - (104 - IPHC_NHC_COMP_HDTSZ) = 104
            #    104 + 26 = 130 > 127 => 104 - 8 = 96; 96 + 26 = 122
            #    v-----------------------------'
            #    8 + 26 = 34
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 96, 8],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [0, 70 + 2 - 8, 8],
        },
    },
    # QUIC short header
    #  - Destination connection ID length = 0,
    #  - Packet Number length = 1
    #  - Stream ID = 1
    "quics_best": {
        "query": {
            "lower": [123, 35],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 0)
            # + 1..4 (Packet Number) (assuming 1 for value 00)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 1 for value 00)
            # + 0 (Offset = 0)
            # + 1 (Length) (assuming 1 for value 60)
            # + 44 Stream Data
            # + 16 128-bit authentication tag
            # = _65_
            # => 65 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 65 - (104 - IPHC_NHC_COMP_HDTSZ) = 9
            #    9 + 26 = 35
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 9],
            # DNS query length from other protocols (42) + 2 byte length
            "dns": [42 + 2 - 9, 9],
        },
        "response_a": {
            "lower": [123, 54],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 0)
            # + 1..4 (Packet Number) (assuming 1 for value 00)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 1 for value 00)
            # + 1..8 (ACK Delay) (assuming 1)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 1 for value 00)
            # + 0 (Offset = 0)
            # + 2 (Length) (assuming 2 for value 76)
            # + 60 Stream Data
            # + 16 128-bit authentication tag
            # = _86_
            # => 86 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 86 - (104 - IPHC_NHC_COMP_HDTSZ) = 28
            #    28 + 26 = 54
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 28],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [58 + 2 - 28, 28],
        },
        "response_aaaa": {
            "lower": [123, 66],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 0)
            # + 1..4 (Packet Number) (assuming 1 for value 00)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 1 for value 00)
            # + 1..8 (ACK Delay) (assuming 1)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 1 for value 00)
            # + 0 (Offset = 0)
            # + 2 (Length) (assuming 2 for value 88)
            # + 72 Stream Data
            # + 16 128-bit authentication tag
            # = _98_
            # => 98 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 98 - (104 - IPHC_NHC_COMP_HDTSZ) = 40
            #    40 + 26 = 66
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 40],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [70 + 2 - 40, 40],
        },
    },
    # QUIC short header
    #  - Destination connection ID length = 20,
    #  - Packet Number length = 4
    #  - Stream ID = 8
    "quics_worst": {
        "query": {
            "lower": [123, 66],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1..4 (Packet Number) (assuming 4)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 8)
            # + 1 (Offset, assuming 1 for value 00)
            # + 1 (Length) (assuming 1 for value 60)
            # + 44 Stream Data
            # + 16 128-bit authentication tag
            # = _96_
            # => 96 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 75 - (104 - IPHC_NHC_COMP_HDTSZ) = 40
            #    40 + 26 = 66
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 40],
            # DNS query length from other protocols (42) + 2 byte length
            "dns": [42 + 2 - 40, 40],
        },
        "response_a": {
            "lower": [123, 93],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1..4 (Packet Number) (assuming 4 for value 00)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 4)
            # + 1..8 (ACK Delay) (assuming 2)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # HANDSHAKE DONE FRAME HEADER
            # + 1 (Type)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 8)
            # + 1 (Offset, assuming 1 for value 00)
            # + 2 (Length) (assuming 2 for value 76)
            # + 60 Stream Data
            # + 16 128-bit authentication tag
            # = _123_
            # => 123 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 123 - (104 - IPHC_NHC_COMP_HDTSZ) = 67
            #    67 + 26 = 93
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 67],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [0, 58 + 2],
        },
        "response_aaaa": {
            "lower": [123, 105],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1..4 (Packet Number) (assuming 4 for value 00)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 4)
            # + 1..8 (ACK Delay) (assuming 2)
            # + 1..8 (ACK Range Count) (assuming 1 for value 00)
            # + 1..8 (First ACK Range) (assuming 1 for value 00)
            # HANDSHAKE DONE FRAME HEADER
            # + 1 (Type)
            # STREAM FRAME HEADER
            # + 1 (Type)
            # + 1..8 (Stream ID) (assuming 8)
            # + 1 (Offset, assuming 1 for value 00)
            # + 2 (Length) (assuming 2 for value 88)
            # + 72 Stream Data
            # + 16 128-bit authentication tag
            # = _135_
            # => 135 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 135 - (104 - IPHC_NHC_COMP_HDTSZ) = 79
            #    79 + 26 = 105
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 79],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [0, 70 + 2],
        },
    },
}
TRANSPORT_FIGURE = {
    "dtls": 0,
    "oscore": 1,
    "quicl_best": 2,
    "quicl_worst": 3,
    "quics_best": 4,
    "quics_worst": 5,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    matplotlib.rcParams["axes.labelsize"] = "x-small"
    matplotlib.rcParams["xtick.labelsize"] = "x-small"
    matplotlib.rcParams["ytick.labelsize"] = "x-small"
    matplotlib.rcParams["grid.color"] = "lightgray"
    matplotlib.rcParams["grid.alpha"] = 0.7
    matplotlib.rcParams["legend.handletextpad"] = 0.4
    matplotlib.rcParams["legend.columnspacing"] = 0.8
    matplotlib.rcParams["legend.fontsize"] = "x-small"
    figure, axs = matplotlib.pyplot.subplots(
        1,
        len(PKT_SIZES),
        sharey=True,
    )
    plot_pkt_sizes.LAYERS = [
        "lower",
        "dtls",
        "quic",
        "coap",
        "oscore",
        "coap_inner",
        "dns",
    ]
    plot_pkt_sizes.LAYERS_STYLE = {
        "lower": {"facecolor": "C3"},
        "dtls": {"facecolor": "C1"},
        "coap": {"facecolor": "C4"},
        "oscore": {"facecolor": "C2"},
        "coap_inner": {"facecolor": "C4"},
        "quic": {"facecolor": "C1", "hatch": "/////"},
        "dns": {"facecolor": "C0"},
    }
    plot_pkt_sizes.LAYERS_READABLE = {
        "lower": r"802.15.4 \& 6LoWPAN",
        "dtls": "DTLS",
        "coap": "CoAP",
        "oscore": "OSCORE",
        "coap_inner": "CoAP",
        "quic": "QUIC",
        "dns": "DNS",
    }
    plot_pkt_sizes.plot_pkt_sizes_for_transports(
        axs,
        transports=[
            "dtls",
            "oscore",
            "quicl_best",
            "quicl_worst",
            "quics_best",
            "quics_worst",
        ],
        transport_figure=TRANSPORT_FIGURE,
        transport_readable={
            "dtls": "DTLSv1.2",
            "oscore": "OSCORE",
            "quicl_best": "QUIC 0-RTT\n(best)",
            "quicl_worst": "QUIC 0-RTT\n(worst)",
            "quics_best": "QUIC 1-RTT\n(best)",
            "quics_worst": "QUIC 1-RTT\n(worst)",
        },
        pkt_sizes=PKT_SIZES,
        fragys=[127, 254],
        xrotation=35,
        ymax=324,
        label_size="xx-small",
    )
    plot_pkt_sizes.add_legends(
        figure,
        ncol=4,
        layers=plot_pkt_sizes.LAYERS,
        extra_style={"edgecolor": "black"},
        frag_first=True,
        frag_label="802.15.4 max. frame size",
        legend_offset=0.01,
        legend_pad=0.10,
    )
    matplotlib.pyplot.tight_layout(w_pad=-0.8)
    # matplotlib.pyplot.subplots_adjust(top=0.86, bottom=0)
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-quic-namelen-24.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


if __name__ == "__main__":
    main()  # pragma: no cover
