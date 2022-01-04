#! /usr/bin/env python3

# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import ast
import logging
import re
import os

import numpy


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.environ.get(
    "DATA_PATH", os.path.join(SCRIPT_PATH, "..", "..", "results")
)
FILENAME_PATTERN_FMT = (
    r"doc-eval-{exp_type}(-{link_layer})?-{transport}(-{method})?(-b{blocksize})?-"
    r"{delay_time}-{delay_queries}-{queries}x{avg_queries_per_sec}(-{record})?-"
    r"(?P<exp_id>\d+)-(?P<timestamp>\d+)(?P<border_router>\.border-router|\.resolver)?"
)
CSV_NAME_PATTERN_FMT = fr"{FILENAME_PATTERN_FMT}\.{{csv_type}}\.csv"
LINK_LAYER_DEFAULT = "ieee802154"
COAP_METHOD_DEFAULT = "fetch"
COAP_BLOCKTYPE_DEFAULT = None
QUERIES_DEFAULT = 100
AVG_QUERIES_PER_SEC_DEFAULT = 10
RECORD_TYPE_DEFAULT = "AAAA"
RUNS = 10
LINK_LAYERS = [
    "ieee802154",
    "ble",
]
TRANSPORTS = [
    "oscore",
    "coaps",
    "coap",
    "dtls",
    "udp",
]
AVG_QUERIES_PER_SEC = numpy.arange(5, 10.5, step=5)
COAP_TRANSPORTS = {
    "coap",
    "coaps",
    "oscore",
}
COAP_METHODS = [
    "fetch",
    "get",
    "post",
]
COAP_BLOCKSIZE = [
    None,
    16,
    32,
]
RECORD_TYPES = [
    "AAAA",
    "A",
]
RESPONSE_DELAYS = [
    (None, None),
    (1.0, 25),
]


class TransportsReadable:  # pylint: disable=too-few-public-methods
    class TransportReadable:  # pylint: disable=too-few-public-methods
        class MethodReadable:  # pylint: disable=too-few-public-methods
            METHODS_READABLE = {
                "fetch": "FETCH",
                "get": "GET",
                "post": "POST",
            }

            def __init__(self, transport, method=None):
                self.transport = transport
                self.method = method

            def __str__(self):
                if self.method is None:
                    return str(self.transport)
                return f"{self.transport} ({self.METHODS_READABLE[self.method]})"

        TRANSPORTS_READABLE = {
            "coap": "CoAP",
            "coaps": "CoAPSv1.2",
            "oscore": "OSCORE",
            "dtls": "DTLSv1.2",
            "udp": "UDP",
        }

        def __init__(self, transport):
            self.transport = transport

        def __getitem__(self, method):
            if self.transport not in COAP_TRANSPORTS:
                return self.MethodReadable(self)
            elif method is None:
                method = "fetch"
            return self.MethodReadable(self, method)

        def __str__(self):
            return self.TRANSPORTS_READABLE[self.transport]

    def __getitem__(self, transport):
        return self.TransportReadable(transport)


class TransportsStyle(dict):
    TRANSPORTS_STYLE = {
        "coap": {"color": "C2"},
        "coaps": {"color": "C3"},
        "oscore": {"color": "C4"},
        "dtls": {"color": "C1"},
        "udp": {"color": "C0"},
    }

    class TransportStyle(dict):
        METHODS_STYLE = {
            "fetch": {"linestyle": "-"},
            "get": {"linestyle": ":"},
            "post": {"linestyle": "--"},
        }

        def __init__(self, transport_style, transport, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.update(transport_style)
            self.transport = transport

        def __getitem__(self, method):
            if method is None:
                return self
            if (
                self.transport not in COAP_TRANSPORTS
                or method not in self.METHODS_STYLE
            ):
                return super().__getitem__(method)
            if method is None:
                method = "fetch"
            return dict(**self, **self.METHODS_STYLE[method])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for transport, style in self.TRANSPORTS_STYLE.items():
            self[transport] = style

    def __getitem__(self, transport):
        return self.TransportStyle(super().__getitem__(transport), transport)


TRANSPORTS_READABLE = TransportsReadable()
TRANSPORTS_STYLE = TransportsStyle()


def get_files(  # pylint: disable=too-many-arguments
    exp_type,
    transport,
    method=None,
    delay_time=None,
    delay_queries=None,
    queries=QUERIES_DEFAULT,
    avg_queries_per_sec=AVG_QUERIES_PER_SEC_DEFAULT,
    record="AAAA",
    csv_type="times",
    link_layer=LINK_LAYER_DEFAULT,
):
    avg_queries_per_sec = round(float(avg_queries_per_sec), 1)
    exp_dict = {
        "exp_type": exp_type,
        "link_layer": f"(?P<link_layer>{link_layer})",
        "transport": transport,
        "delay_time": delay_time,
        "delay_queries": delay_queries,
        "method": f"(?P<method>{method})",
        "blocksize": None,
        "queries": queries,
        "avg_queries_per_sec": avg_queries_per_sec,
        "record": f"(?P<record>{record})",
        "csv_type": csv_type,
    }
    pattern = CSV_NAME_PATTERN_FMT.format(**exp_dict)
    pattern_c = re.compile(pattern)
    filenames = filter(
        lambda x: x[0] is not None and (x[0]["record"] is not None or record == "AAAA"),
        map(
            lambda f: (pattern_c.match(f), os.path.join(DATA_PATH, f)),
            os.listdir(DATA_PATH),
        ),
    )
    filenames = sorted(filenames, key=lambda x: int(x[0]["timestamp"]))
    res = [
        f for f in filenames if f[1].endswith("times.csv") or f[1].endswith("stats.csv")
    ]
    if len(res) != RUNS:
        logging.warning(
            "doc-eval-%s-%s-%s%s-%s-%s-%dx%.1f-%s %shas %d of %d expected runs",
            exp_dict["exp_type"],
            exp_dict["link_layer"],
            exp_dict["transport"],
            f"-{method}" if method is not None else "",
            exp_dict["delay_time"],
            exp_dict["delay_queries"],
            exp_dict["queries"],
            exp_dict["avg_queries_per_sec"],
            record,
            "only " if len(res) < RUNS else "",
            len(res),
            RUNS,
        )
    return res


def reject_outliers(data, m=2):  # pylint: disable=invalid-name
    # pylint: disable=invalid-name
    d = numpy.abs(data - numpy.median(data))
    mdev = numpy.median(d)
    s = d / mdev if mdev else 0.0
    data = numpy.array(data)
    return data[s < m]


def normalize_times_and_ids(row, base_id=None, base_time=None):
    if base_id is None:
        base_id = int(row["id"])
    if base_time is None:
        base_time = float(row["query_time"])
    row["id"] = int(row["id"]) - base_id
    row["query_time"] = float(row["query_time"]) - base_time
    if row.get("response_time"):
        row["response_time"] = float(row["response_time"]) - base_time
    try:
        try:
            row["transmissions"] = ast.literal_eval(row.get("transmissions"))
        except SyntaxError:
            logging.error(
                "Unable to parse transmissions in row %s for query at timestamp %f",
                row,
                row["query_time"] + base_time,
            )
            row["transmissions"] = []
        for i, transmission in enumerate(row["transmissions"]):
            try:
                row["transmissions"][i] = float(transmission) - base_time
            except ValueError:
                row["transmissions"][i] = float("nan")
    except ValueError:
        row["transmissions"] = []
    if row.get("unauth_time"):
        row["unauth_time"] = float(row["unauth_time"]) - base_time
    return base_id, base_time
