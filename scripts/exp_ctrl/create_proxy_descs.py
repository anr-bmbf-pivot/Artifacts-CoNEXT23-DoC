#! /usr/bin/env python3

# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring

import argparse
import enum
import math
import re
import os

import numpy
import yaml


class LinkLayer(enum.IntEnum):
    """
    Enum representing one of the IoT-LABs available link layers
    """

    IEEE802154 = 0
    BLE = 1

    @classmethod
    def _missing_(cls, value):
        try:
            if int(value) == LinkLayer.IEEE802154:
                return cls(LinkLayer.IEEE802154)
            if int(value) == LinkLayer.BLE:
                return cls(LinkLayer.BLE)
        except ValueError:
            if re.search(r"802\.?15\.?4", value.lower()) is not None:
                return cls(LinkLayer.IEEE802154)
            if value.lower() == "ble":
                return cls(LinkLayer.BLE)
        return super()._missing_(value)

    def __str__(self):
        # _name_ is hidden, but it exists
        # pylint: disable=no-member
        return str(self._name_).lower()


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
    "coap",
]
COAP_METHODS = [
    "fetch",
    "get",
    "post",
]
COAP_BLOCKSIZES = [
    None,
]
PROXIED = [
    False,
    True,
]
RESPONSE_DELAYS = [
    {"time": None, "queries": None},
]
DNS_COUNT = 100
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
                    "l2addr": "66:4e:6f:87:a1:fa:2f:3e",
                },
            ],
            "edgelist": [
                ["m3-209", "m3-205"],
                ["m3-205", "m3-202"],
                ["m3-205", "m3-290"],
            ],
        }
    },
}
RECORD_TYPES = [
    "AAAA",
]
REQUESTER_FIRMWARE = {
    "path": "../../apps/requester",
    "env": {
        "PROXIED": 1,
    },
}

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
            "RIOT_CONFIG_GNRC_NETIF_IPV6_DO_NOT_COMP_PREFIX": "y",
            "ETHOS_BAUDRATE": str(500000),
        },
    },
    "firmwares": [
        {
            "path": "../../apps/proxy",
        },
    ]
    + (2 * [REQUESTER_FIRMWARE]),
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


def add_run(descs, run, run_wait):
    if run["link_layer"] == "ble":
        run["rebuild"] = True
        descs["unscheduled"][-1]["duration"] = float(numpy.ceil((run_wait + 470) / 60))
        descs["unscheduled"][-1]["runs"].append(run)
        descs["unscheduled"].append({"runs": []})
        return 0
    descs["unscheduled"][0]["runs"].append(run)
    return run_wait + 300


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
    parser.add_argument(
        "link_layer",
        default=LinkLayer.IEEE802154,
        type=LinkLayer,
        nargs="?",
        help=f"link layer to use (default: {default_output_desc})",
    )
    args = parser.parse_args()

    GLOBALS["nodes"] = NODES[args.link_layer]
    GLOBALS["env"]["SITE_PREFIX"] = PREFIX[args.link_layer]
    GLOBALS["sink_firmware"]["board"] = BOARD[args.link_layer]
    if args.link_layer == LinkLayer.BLE:
        GLOBALS["sink_firmware"]["env"].pop("ETHOS_BAUDRATE", None)
        GLOBALS["sink_firmware"]["env"]["USEMODULE"] = " ".join(
            [
                GLOBALS["sink_firmware"]["env"]["USEMODULE"],
                "nimble_netif",
                "nimble_rpble",
            ]
        )
    for firmware in GLOBALS["firmwares"]:
        firmware["board"] = BOARD[args.link_layer]
        if args.link_layer == LinkLayer.BLE:
            firmware["env"] = {
                "USEMODULE": " ".join(
                    [
                        "nimble_netif",
                        "nimble_rpble",
                    ]
                )
            }
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
                            for proxied in PROXIED:
                                avg_queries_per_sec = round(
                                    float(avg_queries_per_sec), 1
                                )
                                run_wait = int(
                                    math.ceil(DNS_COUNT / avg_queries_per_sec) + 100
                                )
                                for delay in RESPONSE_DELAYS:
                                    run = {
                                        "env": {"DNS_TRANSPORT": transport},
                                        "args": {
                                            "avg_queries_per_sec": avg_queries_per_sec,
                                            "response_delay": delay,
                                            "proxied": proxied,
                                            "record": record_type,
                                        },
                                        "link_layer": str(args.link_layer),
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
                                        run["env"]["COAP_BLOCKSIZE"] = str(
                                            coap_blocksize
                                        )
                                        run["name"] = COAP_BLOCKWISE_RUN_NAME
                                    duration += add_run(descs, run, run_wait)
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
