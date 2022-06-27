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

import re
import sys

import pytest

from iotlab_controller.experiment.descs.file_handler import NestedDescriptionBase

import dispatch_max_age_experiments as dispatch

# Used as module-scoped fixtures in conftest.py pylint: disable=unused-import
from .test_dispatch_proxy_exp import test_run_desc, default_network  # noqa: F401

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture(scope="module")
def dispatcher_class():
    yield dispatch.Dispatcher


@pytest.fixture(scope="module")
def runner_class():
    yield dispatch.Runner


def test_runner_get_tmux_cmds(mocked_dispatcher):
    runner = mocked_dispatcher["runner"]
    run = NestedDescriptionBase()
    cmd_num = 0
    for cmd in runner.get_tmux_cmds(run):
        assert cmd == "ERROR: RESOLVER NOT RUNNING!"
        cmd_num += 1
    assert cmd_num == 1
    runner.resolver_running = True
    cmd_num = 0
    run = NestedDescriptionBase(args={"record": "AAAA", "method": "fetch"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(
            r"query_bulk exec id.exp.example.org inet6( (get|post|fetch))? +"
            f"{dispatch.QUERY_MODULO}",
            cmd,
        )
        cmd_num += 1
    assert cmd_num == 1
    cmd_num = 0
    run = NestedDescriptionBase(args={"record": "A", "method": "fetch"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(
            r"query_bulk exec id.exp.example.org inet\b( (get|post|fetch))? +"
            f"{dispatch.QUERY_MODULO}",
            cmd,
        )
        cmd_num += 1
    assert cmd_num == 1


def test_dispatch_pre_run(mocker, mocked_dispatcher):
    super_pre_run = mocker.patch("dispatch_proxy_experiments.Dispatcher.pre_run")
    mocker.patch(
        "dispatch_load_experiments.Dispatcher.get_resolver_bind_address",
        return_value="2001:db8::dead:c0ff:ee",
    )
    mocker.patch("subprocess.check_output", return_value=b"/tmp/foobar")
    check_call = mocker.patch("subprocess.check_call", return_value="/tmp/foobar")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    run = NestedDescriptionBase(env={"DNS_TRANSPORT": "udp"}, args={})
    ctx = {}
    dispatcher.pre_run(runner, run, ctx)
    super_pre_run.assert_called_once_with(runner, run, ctx)
    dispatcher.resolver_config_file(runner, run)
    called_cmd = "".join(str(b[0][0]) for b in check_call.call_args_list)
    assert "use_etag: true" in called_cmd
    assert "ttl: " in called_cmd
    assert "max_age: " in called_cmd


def test_main(monkeypatch, mocker, api_and_desc):
    args = [sys.argv[0], "test.yaml"]
    monkeypatch.setattr(sys, "argv", args)
    mocker.patch(
        "iotlab_controller.common.get_default_api", return_value=api_and_desc["api"]
    )
    load_experiment_descriptions = mocker.patch(
        "dispatch_max_age_experiments.Dispatcher.load_experiment_descriptions"
    )
    dispatch.dle.main(dispatch.Dispatcher)
    load_experiment_descriptions.assert_called_once()
    load_experiment_descriptions.reset_mock()
