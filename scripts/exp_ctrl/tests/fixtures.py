# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-class-docstring,missing-module-docstring
# pylint: disable=missing-function-docstring

from iotlab_controller.experiment.descs.file_handler import NestedDescriptionBase


TEST_RUN_DESC = NestedDescriptionBase(
    {
        "tmux": {"target": "dns-eval-load:run.0"},
        "nodes": {
            "network": {
                "sink": "m3-10",
                "edgelist": [
                    ["m3-10", "m3-232"],
                ],
                "site": "grenoble",
            },
        },
        "env": {"DNS_COUNT": "12", "SITE_PREFIX": "2001:db8::/57"},
    }
)
