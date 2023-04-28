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

import matplotlib
import matplotlib.pyplot
import matplotlib.style
import matplotlib.ticker
import numpy
import pandas

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
    # QUIC long header
    #  - Destination connection ID length = 8, (see section 7.2)
    #  - Source connection ID length = 0,
    #  - Packet Number length = 1
    #  - Stream ID = 1
    "quicl_best": {
        "query": {
            "lower": [123, 51],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 8)
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
            # = _81_
            # => 81 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 81 - (104 - IPHC_NHC_COMP_HDTSZ) = 25
            #    25 + 26 = 51
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 25],
            # DNS query length from other protocols (42) + 2 byte length
            "dns": [42 + 2 - 25, 25],
        },
        "response_a": {
            "lower": [123, 71],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 8)
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
            # = _103_
            # => 103 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 103 - (104 - IPHC_NHC_COMP_HDTSZ) = 45
            #    45 + 26 = 71
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 45],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [58 + 2 - 45, 45],
        },
        "response_aaaa": {
            "lower": [123, 83],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 8)
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
            # = _115_
            # => 115 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 115 - (104 - IPHC_NHC_COMP_HDTSZ) = 57
            #    49 + 26 = 83
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 57],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [70 + 2 - 57, 57],
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
            "lower": [123, 122],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 20)
            # + 1..8 (Length) (assuming 2 for value 105)
            # + 1..4 (Packet Number) (assuming 4)
            # FRAMES (101 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 8)
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
            # = _154_
            # => 154 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 154 - (104 - IPHC_NHC_COMP_HDTSZ) = 96
            #    96 + 26 = 122
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 96],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [0, 58 + 2],
        },
        "response_aaaa": {
            "lower": [123, 122, 38],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 20)
            # + 1..8 (Length) (assuming 2 for value 117)
            # + 1..4 (Packet Number) (assuming 4)
            # FRAMES (113 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 8)
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
            # = _166_
            # => 166 bytes + 62 bytes > 2 * 127 bytes => 3 fragments
            # => 2nd fragment size = 166 - (104 - IPHC_NHC_COMP_HDTSZ) = 108
            #    108 + 26 = 134 > 127 => 108 - 12 = 96; 96 + 26 = 122
            #    v-----------------------------'
            #    12 + 26 = 38
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 96, 12],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [0, 70 + 2 - 12, 12],
        },
    },
    # QUIC long header (the point before AAAA response switches from 2 fragments to 3)
    #  - Destination connection ID length = 20,
    #  - Source connection ID length = 13
    #  - Packet Number length = 4
    #  - Stream ID = 8, <= this one steps in powers of two
    "quicl_knick0.1": {
        "response_aaaa": {
            "lower": [123, 127],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 13)
            # + 1..8 (Length) (assuming 2 for value 117)
            # + 1..4 (Packet Number) (assuming 4)
            # FRAMES (113 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 8)
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
            # = _159_
            # => 2nd fragment size = 162 - (104 - IPHC_NHC_COMP_HDTSZ) = 101
            #    101 + 26 = 127
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 101],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [0, 70 + 2],
        },
    },
    # QUIC long header (the point after AAAA response switches from 2 fragments to 3)
    #  - Destination connection ID length = 20,
    #  - Source connection ID length = 14
    #  - Packet Number length = 4
    #  - Stream ID = 8, <= this one steps in powers of two
    "quicl_knick0.2": {
        "response_aaaa": {
            "lower": [123, 122, 32],
            # LONG HEADER
            # 1 (header form, fixed bit, long packet type, reserved bits, packet number
            # length)
            # + 4 (Version)
            # + 1 (Destination connection ID Length)
            # + 0..20 (Destination connection ID) (assuming 14)
            # + 1 (Source connection ID Length)
            # + 0..20 (Source connection ID) (assuming 20)
            # + 1..8 (Length) (assuming 2 for value 117)
            # + 1..4 (Packet Number) (assuming 4)
            # FRAMES (113 bytes)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 8)
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
            # = _160_
            # => 160 bytes + 62 bytes > 2 * 127 bytes => 3 fragments
            # => 2nd fragment size = 160 - (104 - IPHC_NHC_COMP_HDTSZ) = 102
            #    102 + 26 = 128 > 127 => 102 - 6 = 96; 96 + 26 = 122
            #    v-----------------------------'
            #    6 + 26 = 32
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 96, 6],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [0, 70 + 2 - 6, 6],
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
            "lower": [123, 57],
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
            # = _87_
            # => 87 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 87 - (104 - IPHC_NHC_COMP_HDTSZ) = 31
            #    31 + 26 = 57
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 31],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [58 + 2 - 31, 31],
        },
        "response_aaaa": {
            "lower": [123, 69],
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
            # = _99_
            # => 99 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 98 - (104 - IPHC_NHC_COMP_HDTSZ) = 43
            #    43 + 26 = 69
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 43],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [70 + 2 - 43, 43],
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
            "lower": [123, 97],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1..4 (Packet Number) (assuming 4)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 8)
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
            # = _127_
            # => 127 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 127 - (104 - IPHC_NHC_COMP_HDTSZ) = 71
            #    71 + 26 = 97
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 71],
            # DNS A response length from other protocols (58) + 2 byte length
            "dns": [0, 58 + 2],
        },
        "response_aaaa": {
            "lower": [123, 109],
            # SHORT HEADER
            # 1 (header form, fixed bit, spin bit, reserved bits, key phase,
            #    packet number length)
            # + 0..20 (Destination connection ID) (assuming 20)
            # + 1..4 (Packet Number) (assuming 4)
            # ACK FRAME HEADER (assume shortest possible)
            # + 1 (Type)
            # + 1..8 (Largest Acknowledged) (assuming 8)
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
            # = _139_
            # => 139 bytes + 62 bytes > 127 bytes => 2 fragments
            # => 2nd fragment size = 139 - (104 - IPHC_NHC_COMP_HDTSZ) = 83
            #    83 + 26 = 109
            "quic": [104 - IPHC_NHC_COMP_HDTSZ, 83],
            # DNS A response length from other protocols (70) + 2 byte length
            "dns": [0, 70 + 2],
        },
    },
}
STYLES = {
    ("dtls", "query"): {"color": "C1", "marker": "o", "markersize": 2},
    ("dtls", "response_a"): {"color": "C1", "marker": "x", "markersize": 3},
    ("dtls", "response_aaaa"): {"color": "C1", "marker": "+", "markersize": 4},
    ("coaps", "query"): {"color": "C3", "marker": "o", "markersize": 2},
    ("coaps", "response_a"): {"color": "C3", "marker": "x", "markersize": 3},
    ("coaps", "response_aaaa"): {"color": "C3", "marker": "+", "markersize": 4},
    ("oscore", "query"): {"color": "C2", "marker": "o", "markersize": 2},
    ("oscore", "response_a"): {"color": "C2", "marker": "x", "markersize": 3},
    ("oscore", "response_aaaa"): {"color": "C2", "marker": "+", "markersize": 4},
}
LAYER_READABLE = {
    "l2": "link layer",
    "l4": "DNS transport layer",
}


def quicl_size_increment(start, msg):
    increment = start
    yield increment
    # destination connection id
    for _ in range(20 - 8):
        increment += 1
        yield increment
    # source connection id
    for _ in range(20):
        increment += 1
        yield increment
    # packet number
    for _ in range(3):
        increment += 1
        yield increment
    if msg != "query":
        # manipulate ACK frame
        # Largest Acknowledged
        length = 1
        while length < 8:
            increment += length
            yield increment
            length *= 2
        # ACK delay
        increment += 1
        yield increment
    # manipulate STREAM frame
    # Stream ID
    length = 1
    while length < 8:
        increment += length
        yield increment
        length *= 2
    # Offset
    increment += 1
    yield increment


def quics_size_increment(start, msg):
    increment = start
    yield increment
    # destination connection id
    for _ in range(20):
        increment += 1
        yield increment
    # packet number
    for _ in range(3):
        increment += 1
        yield increment
    if msg != "query":
        # manipulate ACK frame
        # Largest Acknowledged
        length = 1
        while length < 8:
            increment += length
            yield increment
            length *= 2
        # ACK delay
        increment += 1
        yield increment
        # manipulate HANDSHAKE DONE FRAME
        increment += 1
        yield increment
    # manipulate STREAM frame
    # Stream ID
    length = 1
    while length < 8:
        increment += length
        yield increment
        length *= 2
    # Offset
    increment += 1
    yield increment


def size_increments(start, end, knicks_start, knicks_end, quic, msg):
    # pylint: disable=too-many-arguments
    assert len(knicks_start) == len(knicks_end)
    if quic == "quicl":
        inc_gen = quicl_size_increment
    elif quic == "quics":
        inc_gen = quics_size_increment
    else:
        raise ValueError(f"Unexpected QUIC header form {quic}")
    knick_offset = 0
    res = 0
    for increment in inc_gen(start, msg):
        if knicks_start and increment > knicks_start[0]:
            knick_offset += knicks_end[0] - knicks_start[0] - 1
            knicks_start.pop()
            knicks_end.pop()
        yield increment, increment + knick_offset
        res = increment + knick_offset
    assert res == end


def get_sizes():
    sums = {
        "l2": {transport: {} for transport in PKT_SIZES},
        "l4": {transport: {} for transport in PKT_SIZES},
    }
    quic_header_size = {transport: {} for transport in PKT_SIZES}
    for transport in PKT_SIZES:  # pylint: disable=consider-using-dict-items
        for msg in PKT_SIZES[transport]:
            if msg not in ["query", "response_a", "response_aaaa"]:
                continue
            sums["l2"][transport][msg] = sum(PKT_SIZES[transport][msg]["lower"])
            for layer in ["dtls", "quic", "coap"]:
                if not sums["l4"][transport].get(msg):
                    # each layer contains the SDU of that layer so do not count double
                    sums["l4"][transport][msg] = sum(
                        PKT_SIZES[transport][msg].get(layer, [])
                    )
            if "quic" in PKT_SIZES[transport][msg]:
                quic_header_size[transport][msg] = sums["l4"][transport][msg] - sum(
                    PKT_SIZES[transport][msg]["dns"]
                )
            else:
                quic_header_size[transport][msg] = 0
    return sums, quic_header_size


def generate_overhead(layer, quic, sums, quic_header_size):
    overhead = {}
    for msg in sums[layer][f"{quic}_best"]:
        start = sums[layer][f"{quic}_best"][msg]
        end = sums[layer][f"{quic}_worst"][msg]
        knick1 = [
            sums[layer].get(f"{quic}_knick{i}.1", {}).get(msg, float("inf"))
            for i in [0]
        ]
        knick2 = [
            sums[layer].get(f"{quic}_knick{i}.2", {}).get(msg, float("-inf"))
            for i in [0]
        ]
        for x, size in size_increments(start, end, knick1, knick2, quic, msg):
            x -= start
            x += quic_header_size[f"{quic}_best"][msg]
            for transport in ["dtls", "coaps", "oscore"]:
                pkt_size = sums[layer][transport][msg]
                if (transport, msg) in overhead:
                    overhead[(transport, msg)][x] = ((pkt_size - size) * 100) / pkt_size
                else:
                    overhead[(transport, msg)] = {x: (pkt_size - size) * 100 / pkt_size}
    return overhead


def add_legend(quic, ax):
    if quic == "quics":
        transport_readable = pc.TransportsReadable.TransportReadable
        transport_handles = [
            matplotlib.lines.Line2D(
                [0],
                [0],
                label=transport_readable.TRANSPORTS_READABLE[transport],
                **pc.TRANSPORTS_STYLE[transport],
            )
            for transport in ["dtls", "coaps", "oscore"]
        ]
        ax.legend(
            handles=transport_handles,
            loc="lower left",
            title="Compared DNS Transports",
            bbox_to_anchor=(-0.065, 1),
            ncol=len(transport_handles),
        )
    else:
        MSG_TYPE_STYLE = {
            m: {k: v for k, v in s.items() if k != "color"}
            for (t, m), s in STYLES.items() if t == "dtls"
        }
        msg_handles = [
            matplotlib.lines.Line2D(
                [0],
                [0],
                label=plot_pkt_sizes.MSG_TYPES_READABLE[msg],
                linewidth=0,
                color="gray",
                **MSG_TYPE_STYLE[msg],
            )
            for msg in ["query", "response_a", "response_aaaa"]
        ]
        ax.legend(
            handles=msg_handles,
            loc="lower right",
            title="DNS message type",
            bbox_to_anchor=(1.035, 1),
            ncol=len(msg_handles),
        )


def get_xlim(quic):
    if quic == "quicl":
        return 37, 92
    return 21, 67


def main():
    # pylint: disable=too-many-locals
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0] * 0.53,
        matplotlib.rcParams["figure.figsize"][1] * 0.7,
    )
    matplotlib.rcParams["legend.fontsize"] = "x-small"
    matplotlib.rcParams["legend.title_fontsize"] = "x-small"
    matplotlib.rcParams["legend.borderpad"] = 0.2
    matplotlib.rcParams["legend.handletextpad"] = 0.1
    matplotlib.rcParams["legend.handlelength"] = 0.5
    matplotlib.rcParams["legend.columnspacing"] = 0.3
    matplotlib.rcParams["legend.labelspacing"] = 0.1
    matplotlib.rcParams["lines.markeredgewidth"] = 0.2
    PKT_SIZES.update(
        {
            k: v
            for k, v in plot_pkt_sizes.PKT_SIZES.items()
            if k in ["dtls", "coaps", "oscore"]
        }
    )
    sums, quic_header_size = get_sizes()
    for layer in sums:
        for quic in ["quics", "quicl"]:
            df = pandas.DataFrame(
                generate_overhead(layer, quic, sums, quic_header_size)
            ).sort_index()
            matplotlib.pyplot.clf()
            _, ax = matplotlib.pyplot.subplots()
            xmin, xmax = get_xlim(quic)
            ymin = -56
            ymax = 16
            matplotlib.pyplot.xlim((xmin - 2, xmax + 2))
            matplotlib.pyplot.ylim((ymin, ymax))
            matplotlib.pyplot.xticks(numpy.arange(xmin + 8 - (xmin % 8), xmax + 1, 8))
            matplotlib.pyplot.yticks(numpy.arange(ymin + (10 - ymin % 10), ymax + 1, 10))
            matplotlib.pyplot.xlabel("QUIC header size [bytes]")
            matplotlib.pyplot.ylabel(
                f"Compared {LAYER_READABLE[layer]}\nsize savings [\%]"
            )
            matplotlib.pyplot.hlines(
                y=0, xmin=xmin - 3, xmax=xmax + 3, color="lightgray"
            )
            for key in STYLES:  # pylint: disable=consider-using-dict-items
                # pylint: disable=unsubscriptable-object
                df[key][~df[key].isna()].plot.line(
                    ax=ax, y=key, **STYLES[key], legend=False
                )
            add_legend(quic, ax)
            for ext in pc.OUTPUT_FORMATS:
                matplotlib.pyplot.savefig(
                    os.path.join(
                        pc.DATA_PATH,
                        f"doc-eval-pkt-size-{quic}-{layer}-namelen-24-overhead.{ext}",
                    ),
                    bbox_inches="tight",
                    pad_inches=0.01,
                )


if __name__ == "__main__":
    main()  # pragma: no cover
