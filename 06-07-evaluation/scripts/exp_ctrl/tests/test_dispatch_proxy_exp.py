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

import copy
import sys

import pytest

from iotlab_controller.experiment.descs.file_handler import NestedDescriptionBase

import dispatch_proxy_experiments as dispatch

from . import conftest

# Used as module-scoped fixtures in conftest.py pylint: disable=unused-import
from .test_dispatch_load_exp import runner_class  # noqa: F401

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture(scope="module")
def test_run_desc():
    res = copy.deepcopy(conftest.TEST_RUN_DESC)
    res["env"]["PROXIED"] = 1
    yield res


@pytest.fixture(scope="module")
def default_network():
    yield {
        "sink": "m3-10",
        "edgelist": [
            ["m3-10", "m3-232"],
            ["m3-232", "m3-171"],
            ["m3-232", "m3-15"],
        ],
        "proxies": [
            {
                "name": "m3-232",
            }
        ],
        "site": "grenoble",
    }


@pytest.fixture(scope="module")
def dispatcher_class():
    yield dispatch.Dispatcher


def test_dispatch_establish_session(mocker):
    shell = mocker.MagicMock()
    shell.cmd = mocker.MagicMock(return_value="")
    with pytest.raises(dispatch.ExperimentError):
        dispatch.Dispatcher.establish_session(shell)
    shell.cmd = mocker.MagicMock(return_value="1656586202.681869;test;12345\r\n")
    with pytest.raises(dispatch.ExperimentError):
        dispatch.Dispatcher.establish_session(shell)
    shell.cmd = mocker.MagicMock(return_value="1656586202.681869;t;12345\r\n")
    dispatch.Dispatcher.establish_session(shell)


def test_dispatch_pre_run(mocker, mocked_dispatcher):
    super_pre_run = mocker.patch("dispatch_load_experiments.Dispatcher.pre_run")
    shell_returns = [
        """Iface  5  HWaddr: 2E:82  Channel: 26  Page: 0  NID: 0x23  PHY: O-QPSK

          Long HWaddr: 00:04:25:19:18:01:AE:82
           TX-Power: 0dBm  State: IDLE  max. Retrans.: 3  CSMA Retries: 4
          AUTOACK  ACK_REQ  CSMA  L2-PDU:102  MTU:1280  HL:64  RTR
          RTR_ADV  6LO  IPHC
          Source address length: 8
          Link type: wireless
          inet6 addr: fe80::204:2519:1801:ae82  scope: link  VAL
          inet6 addr: 2001:db8::204:2519:1801:ae82  scope: global  VAL
          inet6 group: ff02::2
          inet6 group: ff02::1
          inet6 group: ff02::1:ff01:ae82
          inet6 group: ff02::1a
          """,
        "Configured proxy coap://[2001:db8::204:2519:1801:ae82]/",
        "Configured proxy coap://[2001:db8::204:2519:1801:ae82]/",
    ]
    mocker.patch("riotctrl.shell.ShellInteraction.cmd", side_effect=shell_returns)
    mocker.patch("dispatch_proxy_experiments.Dispatcher.establish_session")
    mocker.patch("riotctrl.ctrl.RIOTCtrl")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    run = NestedDescriptionBase(args={})
    ctx = {}
    dispatcher.pre_run(runner, run, ctx)
    super_pre_run.assert_called_once_with(runner, run, ctx)
    super_pre_run.reset_mock()
    run = NestedDescriptionBase(args={"proxied": True})
    mocker.patch("riotctrl.shell.ShellInteraction.cmd", side_effect=shell_returns)
    dispatcher.pre_run(runner, run, ctx)
    super_pre_run.assert_called_once_with(runner, run, ctx)
    super_pre_run.reset_mock()
    mocker.patch(
        "riotctrl.shell.ShellInteraction.cmd",
        side_effect=shell_returns[:1] + ["Nope", "Nope", "Nope"],
    )
    dispatcher.verbosity = False
    with pytest.raises(dispatch.ExperimentError):
        dispatcher.pre_run(runner, run, ctx)


def test_dispatch_is_proxy(mocked_dispatcher, network):
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    proxies = [p["name"] for p in network["proxies"]]
    for node in runner.nodes:
        if any(node.uri.startswith(p) for p in proxies):
            assert dispatcher.is_proxy(node)
        else:
            assert not dispatcher.is_proxy(node)


def test_dispatch_is_source_node(mocked_dispatcher, network):
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    proxies = [p["name"] for p in network["proxies"]]
    for node in runner.nodes:
        if any(node.uri.startswith(p) for p in proxies) or node.uri.startswith(
            network["sink"]
        ):
            assert not dispatcher.is_source_node(runner, node)
        else:
            assert dispatcher.is_source_node(runner, node)


def test_dispatch_schedule_experiments(mocker, mocked_dispatcher):
    mocker.patch("dispatch_proxy_experiments.open")
    mocker.patch(
        "iotlab_controller.experiment.descs.runner.ExperimentRunner.build_firmwares"
    )
    mocker.patch(
        "iotlabcli.experiment.submit_experiment",
        return_value={"id": mocked_dispatcher["runner"].experiment.exp_id},
    )
    dispatcher = mocked_dispatcher["dispatcher"]
    assert not dispatcher.schedule_experiments()


def test_main(monkeypatch, mocker, api_and_desc):
    args = [sys.argv[0], "test.yaml"]
    monkeypatch.setattr(sys, "argv", args)
    mocker.patch(
        "iotlab_controller.common.get_default_api", return_value=api_and_desc["api"]
    )
    load_experiment_descriptions = mocker.patch(
        "dispatch_proxy_experiments.Dispatcher.load_experiment_descriptions"
    )
    dispatch.dle.main(dispatch.Dispatcher)
    load_experiment_descriptions.assert_called_once()
    load_experiment_descriptions.reset_mock()
