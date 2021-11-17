#! /usr/bin/env python3

# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring

import argparse
import math
import os

import numpy
import yaml


SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

NAME = "doc-eval-load"
PREFIX = "2001:660:5307:3100::/57"
SITE = "grenoble"
RUNS = 10
DNS_TRANSPORTS = [
    "udp",
    "dtls",
    "coap",
    "coaps",
    "oscore",
]
COAP_METHODS = [
    "fetch",
    "get",
    "post",
]
COAP_BLOCKSIZES = [
    None,
    16,
    32,
]
RESPONSE_DELAYS = [
    {"time": None, "queries": None},
    {"time": 1.0, "queries": 25},
]
DNS_COUNT = 100
AVG_QUERIES_PER_SECS = numpy.arange(4, 10.5, 0.5)
NODES = {
    "network": {
        "site": SITE,
        "sink": "m3-273",
        "edgelist": [
            ["m3-273", "m3-281"],
        ],
    }
}
RECORD_TYPES = [
    "A",
    "AAAA",
]

GLOBALS = {
    "results_dir": "../../results",
    "env": {
        "DEFAULT_CHANNEL": 16,
        "QUERY_COUNT": DNS_COUNT,
        "SITE_PREFIX": PREFIX,
    },
    "name": f"{NAME}",
    "profiles": ["sniffer16"],
    "sink_firmware": {
        "path": "../../RIOT/examples/gnrc_border_router",
        "board": "iotlab-m3",
        "env": {
            "CFLAGS": "-DLOG_LEVEL=LOG_NONE",
            "USEMODULE": " ".join(["gnrc_rpl"]),
            "ETHOS_BAUDRATE": str(500000),
        },
    },
    "firmwares": [
        {
            "path": "../../apps/requester",
            "board": "iotlab-m3",
        }
    ],
    "run_name": "{exp.name}-{run.env[DNS_TRANSPORT]}-"
    "{run[args][response_delay][time]}-"
    "{run[args][response_delay][queries]}-"
    f"{DNS_COUNT}x"
    "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}",
    "nodes": NODES,
    "tmux": {
        "target": f"{NAME}:run.0",
    },
}

COAP_TRANSPORTS = {"coap", "coaps", "oscore"}
COAP_RUN_NAME = (
    "{exp.name}-{run.env[DNS_TRANSPORT]}-{run[args][method]}-"
    "{run[args][response_delay][time]}-"
    "{run[args][response_delay][queries]}-"
    f"{DNS_COUNT}x"
    "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
)
COAP_BLOCKWISE_RUN_NAME = (
    "{exp.name}-{run.env[DNS_TRANSPORT]}-{run[args][method]}-"
    "b{run.env[COAP_BLOCKSIZE]}-{run[args][response_delay][time]}-"
    "{run[args][response_delay][queries]}-"
    f"{DNS_COUNT}x"
    "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
)


def main():  # noqa: C901
    # pylint: disable=missing-function-docstring,too-many-nested-blocks
    # pylint: disable=too-many-branches,too-many-locals
    default_output_desc = os.path.join(SCRIPT_PATH, "descs.yaml")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--rebuild-first",
        action="store_true",
        help="Set rebuild=True on first run, regardless of " "firmware or environment",
    )
    parser.add_argument(
        "-i",
        "--exp-id",
        type=int,
        default=None,
        help="Experiment ID of an already running experiment",
    )
    parser.add_argument(
        "-o",
        "--output-desc",
        default=default_output_desc,
        help=f"Output description file (default: {default_output_desc})",
    )
    args = parser.parse_args()

    descs = {"unscheduled": [{"runs": []}], "globals": GLOBALS}
    duration = 0
    for _ in range(RUNS):
        for transport in DNS_TRANSPORTS:
            # pylint: disable=invalid-name
            for b, coap_blocksize in enumerate(COAP_BLOCKSIZES):
                if transport not in COAP_TRANSPORTS and b > 0:
                    continue
                # pylint: disable=invalid-name
                for m, coap_method in enumerate(COAP_METHODS):
                    if transport not in COAP_TRANSPORTS and m > 0:
                        continue
                    for avg_queries_per_sec in AVG_QUERIES_PER_SECS:
                        for record_type in RECORD_TYPES:
                            avg_queries_per_sec = round(float(avg_queries_per_sec), 1)
                            run_wait = int(
                                math.ceil(DNS_COUNT / avg_queries_per_sec) + 100
                            )
                            for delay in RESPONSE_DELAYS:
                                run = {
                                    "env": {"DNS_TRANSPORT": transport},
                                    "args": {
                                        "avg_queries_per_sec": avg_queries_per_sec,
                                        "response_delay": delay,
                                        "record": record_type,
                                    },
                                    "wait": run_wait,
                                }
                                if transport in COAP_TRANSPORTS:
                                    run["args"]["method"] = coap_method
                                    run["name"] = COAP_RUN_NAME
                                if (
                                    transport in COAP_TRANSPORTS
                                    # Blockwise currently does not work with OSCORE
                                    and transport != "oscore"
                                    and coap_blocksize is not None
                                ):
                                    run["env"]["COAP_BLOCKSIZE"] = str(coap_blocksize)
                                    run["name"] = COAP_BLOCKWISE_RUN_NAME
                                descs["unscheduled"][0]["runs"].append(run)
                                duration += run_wait + 170
    # add first run env to globals so we only build firmware once on start
    # (rebuild is handled with `--rebuild-first` if desired)
    descs["globals"]["env"].update(descs["unscheduled"][0]["runs"][0]["env"])
    descs["globals"]["duration"] = int((duration / 60) + 5)
    if args.rebuild_first or args.exp_id is not None:
        descs["unscheduled"][0]["runs"][0]["rebuild"] = True
    if args.exp_id is not None:
        descs[args.exp_id] = descs["unscheduled"][0]
        del descs["unscheduled"]
    with open(args.output_desc, "w", encoding="utf-8") as output:
        output.write(yaml.dump(descs))


if __name__ == "__main__":
    main()  # pragma: no cover
