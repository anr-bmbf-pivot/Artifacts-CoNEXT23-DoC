#! /usr/bin/env python3

# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring

import numpy

try:
    from . import create_comp_descs
except ImportError:
    import create_comp_descs

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


NODES_ORDER = [
    "m3-205",
    "m3-203",
    "m3-207",
    "m3-198",
    "m3-208",
    "m3-290",
    "m3-195",
    "m3-193",
    "m3-216",
    "m3-219",
    "m3-293",
    "m3-294",
    "m3-188",
    "m3-189",
    "m3-295",
    "m3-297",
    "m3-299",
    "m3-300",
    "m3-303",
    "m3-304",
    "m3-305",
    "m3-307",
    "m3-312",
    "m3-313",
]


def set_network():
    site = create_comp_descs.SITE[create_comp_descs.LinkLayer.IEEE802154]
    create_comp_descs.NODES = {
        # source:
        # https://github.com/inetrg/ACM-ICN-2020-COAP/blob/master/coap/app/testbed.sh
        create_comp_descs.LinkLayer.IEEE802154: {
            "network": {
                "site": site,
                "sink": "m3-205",
                "proxies": [],
                "edgelist": [
                    ["m3-205", "m3-203"],
                    ["m3-205", "m3-207"],
                    ["m3-203", "m3-198"],
                    ["m3-207", "m3-208"],
                    ["m3-207", "m3-290"],
                    ["m3-198", "m3-195"],
                    ["m3-198", "m3-193"],
                    ["m3-208", "m3-216"],
                    ["m3-208", "m3-219"],
                    ["m3-290", "m3-293"],
                    ["m3-290", "m3-294"],
                    ["m3-193", "m3-188"],
                    ["m3-193", "m3-189"],
                    ["m3-293", "m3-295"],
                    ["m3-293", "m3-297"],
                    ["m3-294", "m3-299"],
                    ["m3-294", "m3-300"],
                    ["m3-299", "m3-303"],
                    ["m3-299", "m3-304"],
                    ["m3-300", "m3-305"],
                    ["m3-300", "m3-307"],
                    ["m3-307", "m3-312"],
                    ["m3-307", "m3-313"],
                ],
            },
            "l2addrs": {
                "m3-188": "a6:1b:f8:12:64:5d:32:91",
                "m3-189": "a6:21:9a:9a:8a:65:fc:2d",
                "m3-193": "ba:fc:f8:a1:20:8d:9e:01",
                "m3-195": "6e:5a:a6:e2:de:36:4a:7c",
                "m3-198": "be:93:ab:0f:9b:47:cf:95",
                "m3-203": "5e:42:66:9b:26:df:70:93",
                "m3-205": "66:4e:6f:87:a1:fa:2d:3e",
                "m3-207": "aa:68:f5:29:93:2c:bd:00",
                "m3-208": "de:06:6c:1c:3c:da:28:58",
                "m3-216": "da:e4:0d:19:8b:80:35:54",
                "m3-219": "de:81:83:00:03:9c:cd:90",
                "m3-290": "be:93:f6:36:ea:07:d4:0b",
                "m3-293": "de:06:93:c4:51:0b:7d:61",
                "m3-294": "66:ad:e7:66:e7:a2:11:32",
                "m3-295": "a6:77:31:58:29:b8:2f:70",
                "m3-297": "a6:9a:5f:20:ed:17:e9:9d",
                "m3-299": "a6:fb:68:d6:d0:56:4c:14",
                "m3-300": "fa:50:90:3c:b0:0c:20:e2",
                "m3-303": "ba:0c:f2:d1:aa:47:94:cb",
                "m3-304": "fa:50:fd:78:13:cf:47:6d",
                "m3-305": "66:5d:9b:c4:6b:74:65:38",
                "m3-307": "be:ef:c0:32:24:31:a2:85",
                "m3-312": "ae:57:b0:e9:a4:52:a0:a0",
                "m3-313": "de:3e:20:44:60:ae:dc:6c",
            },
        }
    }
    firmwares = []
    nodes = create_comp_descs.NODES[create_comp_descs.LinkLayer.IEEE802154]
    edgelist = nodes["network"]["edgelist"]
    sink = nodes["network"]["sink"]
    gcoap_config = {
        "RIOT_CONFIG_KCONFIG_USEMODULE_GCOAP": "y",
        "RIOT_CONFIG_GCOAP_REQ_WAITING_MAX": 80,
        "RIOT_CONFIG_GCOAP_RESEND_BUFS_MAX": 80,
    }
    nib_config = {
        "RIOT_CONFIG_KCONFIG_USEMODULE_GNRC_IPV6_NIB": "y",
        "RIOT_CONFIG_GNRC_IPV6_NIB_NUMOF": 45,
        "RIOT_CONFIG_GNRC_IPV6_NIB_OFFL_NUMOF": 45,
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
    create_comp_descs.AVG_QUERIES_PER_SECS = numpy.array([0.8])
    create_comp_descs.RUN_DURATION_SLACK *= 3


def main():
    set_network()
    create_comp_descs.NAME = "doc-eval-comp-24"
    create_comp_descs.GLOBALS["name"] = f"{create_comp_descs.NAME}"
    create_comp_descs.main()


if __name__ == "__main__":
    main()  # pragma: no cover
