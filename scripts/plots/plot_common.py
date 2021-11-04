#! /usr/bin/env python3

# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

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
    r"doc-eval-{exp_type}-{transport}-{delay_time}-{delay_queries}-"
    r"{queries}x{avg_queries_per_sec}-(?P<exp_id>\d+)-(?P<timestamp>\d+)"
)
CSV_NAME_PATTERN_FMT = fr"{FILENAME_PATTERN_FMT}\.times\.csv"
QUERIES_DEFAULT = 100
AVG_QUERIES_PER_SEC_DEFAULT = 10
RUNS = 10
TRANSPORTS = [
    "coap",
    "coaps",
    "oscore",
    "dtls",
    "udp",
]
AVG_QUERIES_PER_SEC = numpy.arange(5, 10.5, step=5)
RESPONSE_DELAYS = [
    (None, None),
    (1.0, 25),
]
TRANSPORTS_READABLE = {
    "coap": "CoAP",
    "coaps": "CoAPSv1.2",
    "oscore": "OSCORE",
    "dtls": "DTLSv1.2",
    "udp": "UDP",
}
TRANSPORTS_STYLE = {
    "coap": {"color": "C2"},
    "coaps": {"color": "C3"},
    "oscore": {"color": "C4"},
    "dtls": {"color": "C1"},
    "udp": {"color": "C0"},
}


def get_files(  # pylint: disable=too-many-arguments
    exp_type,
    transport,
    delay_time=None,
    delay_queries=None,
    queries=QUERIES_DEFAULT,
    avg_queries_per_sec=AVG_QUERIES_PER_SEC_DEFAULT,
):
    avg_queries_per_sec = round(float(avg_queries_per_sec), 1)
    exp_dict = {
        "exp_type": exp_type,
        "transport": transport,
        "delay_time": delay_time,
        "delay_queries": delay_queries,
        "queries": queries,
        "avg_queries_per_sec": avg_queries_per_sec,
    }
    pattern = CSV_NAME_PATTERN_FMT.format(**exp_dict)
    pattern_c = re.compile(pattern)
    filenames = filter(
        lambda x: x[0] is not None,
        map(
            lambda f: (pattern_c.match(f), os.path.join(DATA_PATH, f)),
            os.listdir(DATA_PATH),
        ),
    )
    filenames = sorted(filenames, key=lambda x: int(x[0]["timestamp"]))
    res = [f for f in filenames if f[1].endswith("times.csv")]
    if len(res) != RUNS:
        logging.warning(
            "doc-eval-%s-%s-%s-%s-%dx%d %shas %d of %d expected runs",
            exp_dict["exp_type"],
            exp_dict["transport"],
            exp_dict["delay_time"],
            exp_dict["delay_queries"],
            exp_dict["queries"],
            exp_dict["avg_queries_per_sec"],
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
    return base_id, base_time
