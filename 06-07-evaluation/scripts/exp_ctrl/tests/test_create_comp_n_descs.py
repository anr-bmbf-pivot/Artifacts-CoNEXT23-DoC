# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-class-docstring,missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name,unused-argument

import copy
import importlib
import sys

import pytest

import create_comp_descs


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture
def protect_n_globals():
    name = copy.deepcopy(create_comp_descs.NAME)
    nodes = copy.deepcopy(create_comp_descs.NODES)
    proxy_firmware = copy.deepcopy(create_comp_descs.PROXY_FIRMWARE)
    avg_queries_per_secs = copy.deepcopy(create_comp_descs.AVG_QUERIES_PER_SECS)
    run_duration_slack = copy.deepcopy(create_comp_descs.RUN_DURATION_SLACK)
    globs = copy.deepcopy(create_comp_descs.GLOBALS)

    yield

    create_comp_descs.NAME = name
    create_comp_descs.NODES = nodes
    create_comp_descs.PROXY_FIRMWARE = proxy_firmware
    create_comp_descs.AVG_QUERIES_PER_SECS = avg_queries_per_secs
    create_comp_descs.RUN_DURATION_SLACK = run_duration_slack
    create_comp_descs.GLOBALS = globs


@pytest.mark.parametrize(
    "number, args",
    [
        (8, [sys.argv[0]]),
        (8, [sys.argv[0], "--rebuild-first"]),
        (8, [sys.argv[0], "--exp-id", "1842375287"]),
        (8, [sys.argv[0], "--rebuild-first", "--exp-id", "1842375287"]),
        (24, [sys.argv[0]]),
        (24, [sys.argv[0], "--rebuild-first"]),
        (24, [sys.argv[0], "--exp-id", "1842375287"]),
        (24, [sys.argv[0], "--rebuild-first", "--exp-id", "1842375287"]),
    ],
)
def test_create_comp_n_descs(  # pylint: disable=too-many-arguments
    monkeypatch,
    number,
    args,
    protect_n_globals,
    mock_experiment_factory,
    mock_run_factory,
):
    monkeypatch.setattr(sys, "argv", args)
    create_comp_n_descs = importlib.import_module(f"create_comp_{number}_descs")
    create_comp_n_descs.main()
