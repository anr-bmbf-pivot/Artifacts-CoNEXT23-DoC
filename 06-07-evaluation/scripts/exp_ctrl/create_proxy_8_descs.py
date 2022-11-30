#! /usr/bin/env python3

# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring

try:
    from . import create_proxy_descs
except ImportError:
    import create_proxy_descs

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
    site = create_proxy_descs.SITE[create_proxy_descs.LinkLayer.IEEE802154]
    create_proxy_descs.NODES = {
        # source:
        create_proxy_descs.LinkLayer.IEEE802154: {
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
                "m3-2": "a6:4b:b8:1f:28:20:90:f6",
                "m3-3": "ee:bb:d6:2e:da:17:c4:1b",
                "m3-4": "aa:08:e0:73:a0:df:96:5f",
                "m3-70": "a6:96:d1:50:ff:29:5f:cf",
                "m3-71": "ba:70:ed:a5:93:b8:4d:bc",
                "m3-72": "ae:1d:64:ff:90:fe:8c:3c",
                "m3-282": "aa:2c:b1:82:97:b5:4d:7b",
                "m3-288": "5a:84:04:c6:40:eb:46:23",
            },
        }
    }
    firmwares = []
    nodes = create_proxy_descs.NODES[create_proxy_descs.LinkLayer.IEEE802154]
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
    if "env" not in create_proxy_descs.PROXY_FIRMWARE:
        # pylint: disable=unnecessary-comprehension
        # we want a copy here, so this list comprehension is very much necessary
        create_proxy_descs.PROXY_FIRMWARE["env"] = {k: v for k, v in nib_config.items()}
    else:
        create_proxy_descs.PROXY_FIRMWARE["env"].update(nib_config)  # pragma: no cover
    create_proxy_descs.PROXY_FIRMWARE["env"].update(gcoap_config)
    for node in NODES_ORDER:
        if node == sink:
            continue
        if node not in [e[0] for e in edgelist]:
            # node is leaf
            firmwares.append(create_proxy_descs.REQUESTER_FIRMWARE)
        else:
            # node is forwarder
            firmwares.append(create_proxy_descs.PROXY_FIRMWARE)
            nodes["network"]["proxies"].append({"name": node})
    create_proxy_descs.GLOBALS["firmwares"] = firmwares
    create_proxy_descs.GLOBALS["sink_firmware"]["env"].update(nib_config)
    create_proxy_descs.RUN_DURATION_SLACK *= 2.5


def main():
    set_network()
    create_proxy_descs.NAME = "doc-eval-proxy-24"
    create_proxy_descs.GLOBALS["name"] = f"{create_proxy_descs.NAME}"
    create_proxy_descs.main()


if __name__ == "__main__":
    main()  # pragma: no cover
