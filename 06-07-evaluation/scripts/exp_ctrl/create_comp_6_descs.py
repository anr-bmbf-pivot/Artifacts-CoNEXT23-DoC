#! /usr/bin/env python3

# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring

try:
    from . import create_comp_descs
except ImportError:
    import create_comp_descs

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


NODES_ORDER = [
    "m3-282",
    "m3-288",
    "m3-2",
    "m3-3",
    "m3-4",
    "m3-70",
    "m3-71",
    "m3-72",
]


def set_network():
    site = create_comp_descs.SITE[create_comp_descs.LinkLayer.IEEE802154]
    create_comp_descs.NODES = {
        # source:
        create_comp_descs.LinkLayer.IEEE802154: {
            "network": {
                "site": site,
                "sink": "m3-282",
                "proxies": [{"name": "m3-288"}],
                "edgelist": [
                    ["m3-282", "m3-288"],
                    ["m3-288", "m3-2"],
                    ["m3-288", "m3-3"],
                    ["m3-288", "m3-4"],
                    ["m3-288", "m3-70"],
                    ["m3-288", "m3-71"],
                    ["m3-288", "m3-72"],
                ],
            },
            "l2addrs": {
                "m3-282": "66:ad:e7:66:e7:a2:13:32",
                "m3-288": "fa:50:90:3c:b0:0c:20:e2",
                "m3-2": "ba:0c:f2:d1:aa:47:94:cb",
                "m3-3": "fa:50:fd:78:13:cf:47:6d",
                "m3-4": "66:5d:9b:c4:6b:74:65:38",
                "m3-70": "be:ef:c0:32:24:31:a2:85",
                "m3-71": "be:ef:c0:32:24:31:a2:85",
                "m3-72": "be:ef:c0:32:24:31:a2:85",
            },
        }
    }
    firmwares = []
    nodes = create_comp_descs.NODES[create_comp_descs.LinkLayer.IEEE802154]
    edgelist = nodes["network"]["edgelist"]
    sink = nodes["network"]["sink"]
    gcoap_config = {
        "RIOT_CONFIG_KCONFIG_USEMODULE_GCOAP": "y",
        "RIOT_CONFIG_GCOAP_REQ_WAITING_MAX": 70,
        "RIOT_CONFIG_GCOAP_RESEND_BUFS_MAX": 70,
    }
    nib_config = {
        "RIOT_CONFIG_KCONFIG_USEMODULE_GNRC_IPV6_NIB": "y",
        "RIOT_CONFIG_GNRC_IPV6_NIB_NUMOF": 16,
        "RIOT_CONFIG_GNRC_IPV6_NIB_OFFL_NUMOF": 16,
    }
    if "env" not in create_comp_descs.PROXY_FIRMWARE:
        # pylint: disable=unnecessary-comprehension
        # we want a copy here, so this list comprehension is very much necessary
        create_comp_descs.PROXY_FIRMWARE["env"] = {k: v for k, v in nib_config.items()}
    else:
        create_comp_descs.PROXY_FIRMWARE["env"].update(nib_config)  # pragma: no cover
    create_comp_descs.PROXY_FIRMWARE["env"].update(gcoap_config)
    for node in NODES_ORDER:
        if node == sink:
            continue
        if node not in [e[0] for e in edgelist]:
            # node is leaf
            firmwares.append(create_comp_descs.REQUESTER_FIRMWARE)
        else:
            # node is forwarder
            firmwares.append(create_comp_descs.PROXY_FIRMWARE)
            nodes["network"]["proxies"].append({"name": node})
    create_comp_descs.GLOBALS["firmwares"] = firmwares
    create_comp_descs.GLOBALS["sink_firmware"]["env"].update(nib_config)
    create_comp_descs.RUN_DURATION_SLACK *= 2


def main():
    set_network()
    create_comp_descs.NAME = "doc-eval-comp-24"
    create_comp_descs.GLOBALS["name"] = f"{create_comp_descs.NAME}"
    create_comp_descs.main()


if __name__ == "__main__":
    main()  # pragma: no cover
