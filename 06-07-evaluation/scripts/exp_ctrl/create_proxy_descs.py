#! /usr/bin/env python3

# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=duplicate-code

import argparse
import logging
import math
import os

import numpy
import yaml


from create_load_descs import LinkLayer

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

NAME = "doc-eval-proxy"
PREFIX = {
    LinkLayer.IEEE802154: "2001:660:5307:3100::/57",
    LinkLayer.BLE: "2001:660:3207:04c0::/58",
}
SITE = {
    LinkLayer.IEEE802154: "grenoble",
    LinkLayer.BLE: "saclay",
}
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
    64,
]
PROXIED = [
    False,
    True,
]
RECORD_TYPES = [
    "AAAA",
    "A",
]
RESPONSE_DELAYS = [
    {"time": None, "queries": None},
]
DNS_COUNT = 50
AVG_QUERIES_PER_SECS = numpy.arange(5, 5.5, 0.5)
BOARD = {
    LinkLayer.IEEE802154: "iotlab-m3",
    LinkLayer.BLE: "nrf52840dk",
}
NODES = {
    LinkLayer.IEEE802154: {
        "network": {
            "site": SITE[LinkLayer.IEEE802154],
            "sink": "m3-209",
            "proxies": [
                {
                    "name": "m3-205",
                },
            ],
            "edgelist": [
                ["m3-209", "m3-205"],
                ["m3-205", "m3-202"],
                ["m3-205", "m3-290"],
            ],
        },
        "l2addrs": {
            "m3-202": "be:b2:ab:af:cd:8a:fb:ce",
            "m3-205": "66:4e:6f:87:a1:fa:2f:3e",
            "m3-209": "5e:8f:89:df:81:3d:33:b3",
            "m3-290": "be:93:f6:36:ea:07:d4:0b",
        },
    },
}
PROXY_FIRMWARE = {
    "path": "../../apps/proxy",
}
REQUESTER_FIRMWARE = {
    "path": "../../apps/requester",
    "env": {
        "PROXIED": 1,
    },
}
MAX_AGE_MODES = [None]
CLIENT_COAP_CACHE = [False]
DNS_CACHE = [False]

GLOBALS = {
    "results_dir": "../../results",
    "env": {
        "DEFAULT_CHANNEL": 16,
        "QUERY_COUNT": DNS_COUNT,
    },
    "name": f"{NAME}",
    "profiles": ["sniffer16"],
    "sink_firmware": {
        "path": "../../RIOT/examples/gnrc_border_router",
        "env": {
            "CFLAGS": "-DLOG_LEVEL=LOG_WARNING",
            "USEMODULE": " ".join(
                [
                    "gnrc_pktbuf_cmd",
                    "gnrc_rpl",
                    "gnrc_sixlowpan_frag_stats",
                    "netstats_l2",
                    "od",
                ]
            ),
            "RIOT_CONFIG_KCONFIG_USEMODULE_GNRC_NETIF": "y",
            "RIOT_CONFIG_GNRC_NETIF_IPV6_BR_AUTO_6CTX": "n",
            "SHOULD_RUN_KCONFIG": "1",
            "ETHOS_BAUDRATE": str(500000),
            "DOCKER_ENV_VARS": " ".join(
                [
                    "CFLAGS",
                    "RIOT_CONFIG_KCONFIG_USEMODULE_GNRC_NETIF",
                    "RIOT_CONFIG_GNRC_NETIF_IPV6_BR_AUTO_6CTX",
                    "SHOULD_RUN_KCONFIG",
                    "ETHOS_BAUDRATE",
                    "DEFAULT_CHANNEL",
                ]
            ),
        },
    },
    "firmwares": [PROXY_FIRMWARE] + (2 * [REQUESTER_FIRMWARE]),
    "run_name": "{exp.name}-{run[link_layer]}-{run.env[DNS_TRANSPORT]}-"
    "proxied{run[args][proxied]:d}-"
    "{run[args][response_delay][time]}-"
    "{run[args][response_delay][queries]}-"
    f"{DNS_COUNT}x"
    "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}",
    "tmux": {
        "target": f"{NAME}:run.0",
    },
}

COAP_TRANSPORTS = {"coap", "coaps", "oscore"}
COAP_RUN_NAME = (
    "{exp.name}-{run[link_layer]}-"
    "{run.env[DNS_TRANSPORT]}-{run[args][method]}-"
    "proxied{run[args][proxied]:d}-"
    "{run[args][response_delay][time]}-"
    "{run[args][response_delay][queries]}-"
    f"{DNS_COUNT}x"
    "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
)
COAP_BLOCKWISE_RUN_NAME = (
    "{exp.name}-{run[link_layer]}-"
    "{run.env[DNS_TRANSPORT]}-{run[args][method]}-"
    "proxied{run[args][proxied]:d}-"
    "b{run.env[COAP_BLOCKSIZE]}-{run[args][response_delay][time]}-"
    "{run[args][response_delay][queries]}-"
    f"{DNS_COUNT}x"
    "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
)
RUN_DURATION_SLACK = 300


def add_run(descs, run, run_wait):
    descs["unscheduled"][0]["runs"].append(run)
    return run_wait + RUN_DURATION_SLACK


def main():  # noqa: C901
    # pylint: disable=missing-function-docstring,too-many-nested-blocks
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
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
    parser.add_argument(
        "-d",
        "--docker",
        action="store_true",
        help="Build firmware in riot/riotbuild:2022.01 docker container",
    )
    args = parser.parse_args()
    args.link_layer = LinkLayer.IEEE802154

    GLOBALS["nodes"] = NODES[args.link_layer]
    GLOBALS["env"]["SITE_PREFIX"] = PREFIX[args.link_layer]
    if args.docker:
        GLOBALS["env"]["BUILD_IN_DOCKER"] = 1
        docker_usemodules = (
            f"-e 'USEMODULE={GLOBALS['sink_firmware']['env']['USEMODULE']}'"
        )
        if "DOCKER_ENVIRONMENT_CMDLINE" in GLOBALS["sink_firmware"]["env"]:
            GLOBALS["sink_firmware"]["env"][
                "DOCKER_ENVIRONMENT_CMDLINE"
            ] += docker_usemodules
        else:
            GLOBALS["sink_firmware"]["env"][
                "DOCKER_ENVIRONMENT_CMDLINE"
            ] = docker_usemodules
    GLOBALS["sink_firmware"]["board"] = BOARD[args.link_layer]
    for firmware in GLOBALS["firmwares"]:
        firmware["board"] = BOARD[args.link_layer]
    descs = {"unscheduled": [{"runs": []}], "globals": GLOBALS}
    duration = 0
    for _ in range(RUNS):
        for transport in DNS_TRANSPORTS:
            # pylint: disable=invalid-name
            for b, coap_blocksize in enumerate(COAP_BLOCKSIZES):
                if transport not in COAP_TRANSPORTS and b > 0:
                    continue
                if transport == "oscore" and b > 0:
                    continue
                if args.docker and transport == "oscore":
                    logging.warning(
                        "Unable to build libOSCORE in docker. Skipping OSCORE runs. "
                        "See https://gitlab.com/oscore/liboscore/-/issues/60"
                    )
                    continue
                for dns_cache in DNS_CACHE:
                    for client_coap_cache in CLIENT_COAP_CACHE:
                        # pylint: disable=invalid-name
                        for m, coap_method in enumerate(COAP_METHODS):
                            if transport not in COAP_TRANSPORTS and m > 0:
                                continue
                            if coap_method == "get" and coap_blocksize is not None:
                                continue
                            if coap_method == "get" and transport == "oscore":
                                continue
                            for avg_queries_per_sec in AVG_QUERIES_PER_SECS:
                                for record_type in RECORD_TYPES:
                                    for proxied in PROXIED:
                                        if transport != "coap" and proxied:
                                            continue
                                        if coap_blocksize is not None and proxied:
                                            continue
                                        if (
                                            record_type == "A"
                                            and coap_blocksize is not None
                                            and coap_blocksize > 58
                                        ):
                                            continue
                                        if record_type != "AAAA" and proxied:
                                            continue
                                        avg_queries_per_sec = round(
                                            float(avg_queries_per_sec), 1
                                        )
                                        run_wait = int(
                                            math.ceil(DNS_COUNT / avg_queries_per_sec)
                                            + 100
                                        )
                                        if coap_blocksize is not None:
                                            if record_type == "AAAA":
                                                run_wait += (70 // coap_blocksize) * 100
                                            else:
                                                run_wait += (58 // coap_blocksize) * 100
                                            run_wait += (42 // coap_blocksize) * 100
                                        for delay in RESPONSE_DELAYS:
                                            for max_age_mode in MAX_AGE_MODES:
                                                if (
                                                    not proxied
                                                    and max_age_mode != MAX_AGE_MODES[0]
                                                ):
                                                    continue
                                                run = {
                                                    "env": {
                                                        "DNS_TRANSPORT": transport,
                                                        "WITH_COAP_CACHE": int(
                                                            client_coap_cache
                                                        ),
                                                        "WITH_DNS_CACHE": int(
                                                            dns_cache
                                                        ),
                                                    },
                                                    "args": {
                                                        "avg_queries_per_sec": (
                                                            avg_queries_per_sec
                                                        ),
                                                        "response_delay": delay,
                                                        "proxied": proxied,
                                                        "record": record_type,
                                                    },
                                                    "link_layer": str(args.link_layer),
                                                    "wait": run_wait,
                                                }
                                                if max_age_mode is not None:
                                                    run["args"][
                                                        "max_age_mode"
                                                    ] = max_age_mode
                                                if transport in COAP_TRANSPORTS:
                                                    run["args"]["method"] = coap_method
                                                    run["name"] = COAP_RUN_NAME
                                                if (
                                                    transport in COAP_TRANSPORTS
                                                    # Blockwise currently does
                                                    # not work with OSCORE
                                                    and transport != "oscore"
                                                    and coap_blocksize is not None
                                                ):
                                                    run["env"]["COAP_BLOCKSIZE"] = str(
                                                        coap_blocksize
                                                    )
                                                    run[
                                                        "name"
                                                    ] = COAP_BLOCKWISE_RUN_NAME
                                                duration += add_run(
                                                    descs, run, run_wait
                                                )
    # add first run env to globals so we only build firmware once on start
    # (rebuild is handled with `--rebuild-first` if desired)
    descs["globals"]["env"].update(descs["unscheduled"][0]["runs"][0]["env"])
    descs["globals"]["duration"] = int((duration / 60) + 20)
    if args.rebuild_first or args.exp_id is not None:
        descs["unscheduled"][0]["runs"][0]["rebuild"] = True
    if args.exp_id is not None:
        descs[args.exp_id] = descs["unscheduled"][0]
        del descs["unscheduled"]
    with open(args.output_desc, "w", encoding="utf-8") as output:
        output.write(yaml.dump(descs))


if __name__ == "__main__":
    main()  # pragma: no cover
