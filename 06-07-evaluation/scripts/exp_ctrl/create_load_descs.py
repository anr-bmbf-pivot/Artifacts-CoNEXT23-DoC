#! /usr/bin/env python3

# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=duplicate-code

import argparse
import enum
import math
import re
import os

import numpy
import yaml

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


class LinkLayer(enum.IntEnum):
    """
    Enum representing one of the IoT-LABs available link layers
    """

    IEEE802154 = 0
    BLE = 1

    @classmethod
    def _missing_(cls, value):
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

NAME = "doc-eval-load"
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
RESPONSE_DELAYS = [
    {"time": None, "queries": None},
    {"time": 1.0, "queries": 25},
]
DNS_COUNT = 60
AVG_QUERIES_PER_SECS = numpy.arange(5, 10.5, 5)
BOARD = {
    LinkLayer.IEEE802154: "iotlab-m3",
    LinkLayer.BLE: "nrf52840dk",
}
NODES = {
    LinkLayer.IEEE802154: {
        "network": {
            "site": SITE[LinkLayer.IEEE802154],
            "sink": "m3-273",
            "edgelist": [
                ["m3-273", "m3-281"],
            ],
        }
    },
    LinkLayer.BLE: {
        "network": {
            "site": SITE[LinkLayer.BLE],
            "sink": "nrf52840dk-1",
            "edgelist": [
                ["nrf52840dk-1", "nrf52840dk-4"],
            ],
        }
    },
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
    },
    "name": f"{NAME}",
    "profiles": ["sniffer16"],
    "sink_firmware": {
        "path": "../../RIOT/examples/gnrc_border_router",
        "env": {
            "CFLAGS": "-DLOG_LEVEL=LOG_NONE",
            "USEMODULE": " ".join(
                [
                    "gnrc_rpl",
                    "netstats_l2",
                    "gnrc_pktbuf_cmd",
                    "od",
                    "gnrc_sixlowpan_frag_stats",
                ]
            ),
            "RIOT_CONFIG_KCONFIG_USEMODULE_GNRC_NETIF": "y",
            "RIOT_CONFIG_GNRC_NETIF_IPV6_DO_NOT_COMP_PREFIX": "y",
            "ETHOS_BAUDRATE": str(500000),
        },
    },
    "firmwares": [
        {
            "path": "../../apps/requester",
        }
    ],
    "run_name": "{exp.name}-{run[link_layer]}-{run.env[DNS_TRANSPORT]}-"
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
    "{run[args][response_delay][time]}-"
    "{run[args][response_delay][queries]}-"
    f"{DNS_COUNT}x"
    "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
)
COAP_BLOCKWISE_RUN_NAME = (
    "{exp.name}-{run[link_layer]}-"
    "{run.env[DNS_TRANSPORT]}-{run[args][method]}-"
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
        GLOBALS.pop("profiles", None)
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
                if args.link_layer == LinkLayer.BLE and b > 0:
                    continue
                # pylint: disable=invalid-name
                for m, coap_method in enumerate(COAP_METHODS):
                    if transport not in COAP_TRANSPORTS and m > 0:
                        continue
                    if (
                        transport == "oscore" or args.link_layer == "ble"
                    ) and coap_method != "fetch":
                        continue
                    if (
                        transport in COAP_TRANSPORTS
                        and coap_method != "get"
                        and coap_blocksize is not None
                    ):
                        continue
                    for avg_queries_per_sec in AVG_QUERIES_PER_SECS:
                        if avg_queries_per_sec > 5 and coap_blocksize == 16:
                            continue
                        for record_type in RECORD_TYPES:
                            if (
                                record_type == "A"
                                and coap_blocksize is not None
                                and coap_blocksize > 58
                            ):
                                continue
                            avg_queries_per_sec = round(float(avg_queries_per_sec), 1)
                            run_wait = int(
                                math.ceil(DNS_COUNT / avg_queries_per_sec) + 100
                            )
                            if coap_blocksize is not None:
                                if record_type == "AAAA":
                                    run_wait += (70 // coap_blocksize) * 100
                                else:
                                    run_wait += (58 // coap_blocksize) * 100
                                run_wait += (42 // coap_blocksize) * 100
                            for delay in RESPONSE_DELAYS:
                                if delay["time"] is not None and (
                                    avg_queries_per_sec == 10
                                    or coap_blocksize is not None
                                ):
                                    continue
                                run = {
                                    "env": {"DNS_TRANSPORT": transport},
                                    "args": {
                                        "avg_queries_per_sec": avg_queries_per_sec,
                                        "response_delay": delay,
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
                                    run["env"]["COAP_BLOCKSIZE"] = str(coap_blocksize)
                                    run["name"] = COAP_BLOCKWISE_RUN_NAME
                                duration += add_run(descs, run, run_wait)
    if not descs["unscheduled"][-1]["runs"]:
        del descs["unscheduled"][-1]
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
