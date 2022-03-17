#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2022 Freie Universität Berlin
#
# Distributed under terms of the MIT license.

try:
    from . import create_proxy_descs
except ImportError:
    import create_proxy_descs


if __name__ == "__main__":
    create_proxy_descs.NAME = "doc-eval-max_age"
    create_proxy_descs.DNS_TRANSPORTS = ["coap"]
    create_proxy_descs.COAP_BLOCKSIZES = [None]
    create_proxy_descs.RECORD_TYPES = ["AAAA"]
    create_proxy_descs.MAX_AGE_MODES = ["min", "subtract"]
    create_proxy_descs.GLOBALS["run_name"] = (
        "{exp.name}-{run[args][max_age_mode]}-{run[link_layer]}-"
        "{run.env[DNS_TRANSPORT]}-proxied{run[args][proxied]:d}-"
        "{run[args][response_delay][time]}-"
        "{run[args][response_delay][queries]}-"
        f"{create_proxy_descs.DNS_COUNT}x"
        "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}",
    )
    create_proxy_descs.GLOBALS["name"] = f"{create_proxy_descs.NAME}"
    create_proxy_descs.GLOBALS["tmux"]["target"] = f"{create_proxy_descs.NAME}:run.0"
    create_proxy_descs.COAP_RUN_NAME = (
        "{exp.name}-{run[link_layer]}-{run[args][max_age_mode]}-"
        "{run.env[DNS_TRANSPORT]}-{run[args][method]}-"
        "proxied{run[args][proxied]:d}-"
        "{run[args][response_delay][time]}-"
        "{run[args][response_delay][queries]}-"
        f"{create_proxy_descs.DNS_COUNT}x"
        "{run[args][avg_queries_per_sec]}-{run[args][record]}-{exp.exp_id}-{time}"
    )
    create_proxy_descs.main()