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

import re

import dispatch_load_experiments as dispatch

from .fixtures import TEST_RUN_DESC


def test_runner_init(mocker):
    runner = dispatch.Runner(dispatcher=mocker.MagicMock(), desc=TEST_RUN_DESC)
    assert not runner.resolver_running


def test_runner_get_tmux_cmds(mocker):
    runner = dispatch.Runner(dispatcher=mocker.MagicMock(), desc=TEST_RUN_DESC)
    runner.resolver_running = True
    cmd_num = 0
    run = mocker.MagicMock()
    run.get = mocker.MagicMock(return_value={"record": "AAAA"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(r"query_bulk exec h.de inet6", cmd)
        cmd_num += 1
    assert cmd_num == 1
    cmd_num = 0
    run = mocker.MagicMock()
    run.get = mocker.MagicMock(return_value={"record": "A"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(r"query_bulk exec h.de inet$", cmd)
        cmd_num += 1
    assert cmd_num == 1


def test_dispatch_get_resolver_bind_address():
    dispatcher = dispatch.Dispatcher("test.yaml")
    bind_address = dispatcher.get_resolver_bind_address(None)
    if bind_address is not None:  # pragma: no cover
        assert re.match(r"[0-9a-f:]+", bind_address)
        assert not bind_address.startswith("fe80:")


def test_dispatch_get_free_tap():
    dispatcher = dispatch.Dispatcher("test.yaml")
    tap = dispatcher.get_free_tap(None)
    assert re.match(r"tap\d+", tap)
