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
        "nodes": {
            "network": {
                "sink": "m3-10",
                "edgelist": [
                    ["m3-10", "m3-232"],
                ],
                "site": "grenoble",
            },
        },
        "env": {"DNS_COUNT": "12", "SITE_PREFIX": "2001:db8::/62"},
    }
)


@pytest.fixture
def api_and_desc(mocker):
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
                    "x": "1",
                    "y": "3",
                    "z": "3",
                    "network_address": "m3-232.grenoble.iot-lab.info",
                },
            ]
        }
    )
    yield {
        "api": api,
        "desc": TEST_RUN_DESC,
    }
