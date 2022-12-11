#! /usr/bin/env python3

# Copyright (C) 2021-22 Freie Universität Berlin
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
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def main(prefix="doc-eval-max_age", tmux_session="doc-eval-max_age"):
    create_comp_descs.NAME = prefix
    create_comp_descs.DNS_TRANSPORTS = ["coap"]
    create_comp_descs.COAP_BLOCKSIZES = [None]
    create_comp_descs.RECORD_TYPES = ["AAAA"]
    proxy_env = {
        "RIOT_CONFIG_KCONFIG_USEMODULE_NANOCOAP_CACHE": "y",
        "RIOT_CONFIG_KCONFIG_USEMODULE_NANOCOAP": "y",
        "RIOT_CONFIG_NANOCOAP_CACHE_RESPONSE_SIZE": 228,
        "RIOT_CONFIG_GCOAP_PDU_BUF_SIZE": 228,
        "DOCKER_ENV_VARS": " ".join(
            [
                "RIOT_CONFIG_KCONFIG_USEMODULE_NANOCOAP_CACHE",
                "RIOT_CONFIG_KCONFIG_USEMODULE_NANOCOAP",
                "RIOT_CONFIG_NANOCOAP_CACHE_RESPONSE_SIZE",
                "RIOT_CONFIG_GCOAP_PDU_BUF_SIZE",
            ]
        ),
    }
    if "env" in create_comp_descs.PROXY_FIRMWARE:
        create_comp_descs.PROXY_FIRMWARE["env"].update(proxy_env)
    else:
        create_comp_descs.PROXY_FIRMWARE["env"] = proxy_env
    create_comp_descs.MAX_AGE_MODES = ["dohlike", "eolttls"]
    create_comp_descs.CLIENT_COAP_CACHE = [False, True]
    create_comp_descs.DNS_CACHE = [False, True]
    create_comp_descs.PROXIED = [False, True]
    create_comp_descs.GLOBALS["run_name"] = (
        "{exp.name}-{run[link_layer]}-{run[args][max_age_mode]}-"
        "{run.env[DNS_TRANSPORT]}-"
        "dc{run.env[WITH_DNS_CACHE]}-ccc{run.env[WITH_COAP_CACHE]}-"
        "proxied{run[args][proxied]:d}-"
        "{run[args][response_delay][time]}-"
        "{run[args][response_delay][queries]}-"
        f"{create_comp_descs.DNS_COUNT}x"
        "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
    )
    create_comp_descs.GLOBALS["name"] = f"{create_comp_descs.NAME}"
    create_comp_descs.GLOBALS["tmux"]["target"] = f"{tmux_session}:run.0"
    create_comp_descs.COAP_RUN_NAME = (
        "{exp.name}-{run[link_layer]}-{run[args][max_age_mode]}-"
        "{run.env[DNS_TRANSPORT]}-{run[args][method]}-"
        "dc{run.env[WITH_DNS_CACHE]}-ccc{run.env[WITH_COAP_CACHE]}-"
        "proxied{run[args][proxied]:d}-"
        "{run[args][response_delay][time]}-"
        "{run[args][response_delay][queries]}-"
        f"{create_comp_descs.DNS_COUNT}x"
        "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
    )
    create_comp_descs.main()


if __name__ == "__main__":
    main()  # pragma: no cover
