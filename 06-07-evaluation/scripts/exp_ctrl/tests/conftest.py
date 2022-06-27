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

import pytest

from iotlab_controller.experiment.descs.file_handler import NestedDescriptionBase

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


class MockExperiment:
    def __init__(self, exp_id):
        self._exp_id = exp_id

    @property
    def name(self):
        return "mock_experiment"

    @property
    def exp_id(self):
        return self._exp_id


class MockRun:  # pylint: disable=too-few-public-methods
    def __init__(self, args, env, link_layer, *a, **kwargs):
        # pylint: disable=unused-argument
        self._args = args
        self._link_layer = link_layer
        self.env = env

    def __getitem__(self, key):
        if key == "args":
            return self._args
        if key == "link_layer":
            return self._link_layer
        raise KeyError(key)  # pragma: no cover


@pytest.fixture(scope="module")
def mock_experiment_factory():
    yield MockExperiment


@pytest.fixture(scope="module")
def mock_run_factory():
    yield MockRun


TEST_RUN_DESC = NestedDescriptionBase(
    {
        "tmux": {"target": "dns-eval-load:run.0"},
        "env": {"DNS_COUNT": "12", "SITE_PREFIX": "2001:db8::/62"},
    }
)


@pytest.fixture(scope="function")
def network(request, default_network):
    if hasattr(request, "param") and request.param is not None:
        yield request.param
    else:
        yield default_network


@pytest.fixture
def api_and_desc(mocker, test_run_desc, network):
    # pylint: disable=redefined-outer-name
    api = mocker.MagicMock()
    api.get_nodes = mocker.MagicMock(
        return_value={
            "items": [
                {
                    "archi": "m3:at86rf231",
                    "mobile": 0,
                    "mobility_type": " ",
                    "site": "grenoble",
                    "uid": "test",
                    "x": "1",
                    "y": "2",
                    "z": "3",
                    "network_address": "m3-10.grenoble.iot-lab.info",
                },
                {
                    "archi": "m3:at86rf231",
                    "mobile": 0,
                    "mobility_type": " ",
                    "site": "grenoble",
                    "uid": "test",
                    "x": "2",
                    "y": "2",
                    "z": "3",
                    "network_address": "m3-15.grenoble.iot-lab.info",
                },
                {
                    "archi": "m3:at86rf231",
                    "mobile": 0,
                    "mobility_type": " ",
                    "site": "grenoble",
                    "uid": "test",
                    "x": "2",
                    "y": "2",
                    "z": "2",
                    "network_address": "m3-171.grenoble.iot-lab.info",
                },
                {
                    "archi": "m3:at86rf231",
                    "mobile": 0,
                    "mobility_type": " ",
                    "site": "grenoble",
                    "uid": "test",
                    "x": "1",
                    "y": "3",
                    "z": "3",
                    "network_address": "m3-232.grenoble.iot-lab.info",
                },
                {
                    "archi": "nrf52dk:ble",
                    "camera": 0,
                    "mobile": 0,
                    "mobility_type": " ",
                    "network_address": "nrf52dk-9.saclay.iot-lab.info",
                    "power_consumption": 0,
                    "power_control": 1,
                    "radio_sniffing": 0,
                    "site": "saclay",
                    "state": "Alive",
                    "uid": "e37c",
                    "x": "4",
                    "y": "67.3",
                    "z": "6",
                },
                {
                    "archi": "nrf52dk:ble",
                    "camera": 0,
                    "mobile": 0,
                    "mobility_type": " ",
                    "network_address": "nrf52dk-10.saclay.iot-lab.info",
                    "power_consumption": 0,
                    "power_control": 1,
                    "radio_sniffing": 0,
                    "site": "saclay",
                    "state": "Alive",
                    "uid": "e6d3",
                    "x": "5",
                    "y": "67.3",
                    "z": "6",
                },
            ]
        }
    )
    if test_run_desc is TEST_RUN_DESC:
        test_run_desc = copy.deepcopy(test_run_desc)
    test_run_desc["nodes"] = {"network": network}
    yield {
        "api": api,
        "desc": test_run_desc,
    }


@pytest.fixture
def mocked_dispatcher(mocker, dispatcher_class, runner_class, api_and_desc, network):
    # pylint: disable=redefined-outer-name
    nodes = set(node for edge in network["edgelist"] for node in edge)

    dispatcher = dispatcher_class("test.yaml", api=api_and_desc["api"])
    runner = runner_class(dispatcher=dispatcher, **api_and_desc)
    dispatcher.descs["globals"] = {
        "nodes": api_and_desc["desc"]["nodes"],
        "sink_firmware": {
            "path": f"/the/application/{network['sink']}",
        },
        "firmwares": [
            {"path": f"/the/application/{node}"}
            for node in nodes
            if node != network["sink"]
        ],
    }
    dispatcher.firmwares = [
        mocker.MagicMock(application_path=f"/the/application/{node}") for node in nodes
    ]
    runner.experiment.exp_id = 3124258635
    runner.experiment.username = "test_user"
    runner.experiment.tmux_session = mocker.MagicMock()
    # check if network provided to api_and_desc is how we expect it to be
    runner.experiment.firmwares = [
        mocker.MagicMock(application_path=f"/the/application/{node}") for node in nodes
    ]
    yield {
        "dispatcher": dispatcher,
        "runner": runner,
    }
