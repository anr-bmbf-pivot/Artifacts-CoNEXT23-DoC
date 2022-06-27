# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-class-docstring,missing-module-docstring
# pylint: disable=missing-function-docstring

import os
import sys
import yaml

import pytest

import create_load_descs

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "value, exp, exp_str",
    [
        (
            create_load_descs.LinkLayer.IEEE802154,
            create_load_descs.LinkLayer.IEEE802154,
            "ieee802154",
        ),
        ("IEEE 802.15.4", create_load_descs.LinkLayer.IEEE802154, "ieee802154"),
        ("ieee802154", create_load_descs.LinkLayer.IEEE802154, "ieee802154"),
        ("802154", create_load_descs.LinkLayer.IEEE802154, "ieee802154"),
        (create_load_descs.LinkLayer.BLE, create_load_descs.LinkLayer.BLE, "ble"),
        ("ble", create_load_descs.LinkLayer.BLE, "ble"),
        ("foobar", ValueError, ""),
    ],
)
def test_link_layer_enum(value, exp, exp_str):
    if isinstance(exp, create_load_descs.LinkLayer):
        res = create_load_descs.LinkLayer(value)
        assert res == exp
        assert str(res) == exp_str
    else:
        with pytest.raises(exp):
            create_load_descs.LinkLayer(value)


@pytest.mark.parametrize(
    "args",
    [
        [sys.argv[0]],
        [sys.argv[0], "ble"],
        [sys.argv[0], "--docker"],
        [sys.argv[0], "--docker", "ble"],
        [sys.argv[0], "--rebuild-first"],
        [sys.argv[0], "--exp-id", "68486999"],
        [sys.argv[0], "--rebuild-first", "--exp-id", "68486999"],
    ],
)
def test_create_load_descs(mocker, args, mock_experiment_factory, mock_run_factory):
    open_mock = mocker.mock_open()
    mocker.patch("create_load_descs.open", open_mock)
    mocker.patch("sys.argv", args)

    create_load_descs.main()

    open_mock.assert_called_with(
        os.path.join(create_load_descs.SCRIPT_PATH, "descs.yaml"), "w", encoding="utf-8"
    )
    open_mock.return_value.write.assert_called()
    write_args, _ = open_mock.return_value.write.call_args
    yaml_dict = yaml.load(write_args[0], Loader=yaml.FullLoader)
    assert yaml_dict["globals"] == create_load_descs.GLOBALS
    if "--exp-id" in args:
        exp_id = int(args[args.index("--exp-id") + 1])
        assert exp_id in yaml_dict
        runs = yaml_dict[exp_id]["runs"]
    elif "ble" in args:
        exp_id = 16845407703279583489
        assert len(yaml_dict["unscheduled"]) > 1
        runs = []
        for exp in yaml_dict["unscheduled"]:
            runs += exp["runs"]
        assert len(runs) > 1
    else:
        exp_id = 16845407703279583489
        assert len(yaml_dict["unscheduled"]) == 1
        runs = yaml_dict["unscheduled"][0]["runs"]
    if len(runs) and "--rebuild-first" in args:
        assert runs[0]["rebuild"]
    for run in runs:
        assert "args" in run
        assert "env" in run
        assert "response_delay" in run["args"]
        assert "DNS_TRANSPORT" in run["env"]
        exp = mock_experiment_factory(exp_id=exp_id)
        run_name = yaml_dict["globals"]["run_name"].format(
            run=mock_run_factory(**run), exp=exp, time=596608887
        )
        assert str(exp_id) in run_name
        assert exp.name in run_name
        assert "596608887" in run_name
